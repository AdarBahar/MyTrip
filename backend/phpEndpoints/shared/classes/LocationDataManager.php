<?php
/**
 * Location Data Manager
 * 
 * Handles all location data operations with database and file fallback support
 * Provides unified interface for location data storage and retrieval
 * 
 * @version 2.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/../db-config.php';

class LocationDataManager {
    private $pdo;
    private $useDatabaseStorage;
    private $logDir;
    
    public function __construct() {
        $this->useDatabaseStorage = DatabaseConfig::isDatabaseMode();
        $this->logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../../logs'), '/');
        
        if ($this->useDatabaseStorage) {
            try {
                $this->pdo = DatabaseConfig::getInstance()->getConnection();
            } catch (Exception $e) {
                error_log("Database connection failed, falling back to file storage: " . $e->getMessage());
                $this->useDatabaseStorage = false;
            }
        }
    }
    
    /**
     * Insert location record with automatic user/device management
     */
    public function insertLocationRecord($data) {
        if ($this->useDatabaseStorage) {
            return $this->insertLocationToDatabase($data);
        } else {
            return $this->insertLocationToFile($data);
        }
    }
    
    /**
     * Get location records with filtering
     */
    public function getLocationRecords($filters = []) {
        if ($this->useDatabaseStorage) {
            return $this->getLocationsFromDatabase($filters);
        } else {
            return $this->getLocationsFromFiles($filters);
        }
    }
    
    /**
     * Get user locations for map display
     */
    public function getUserLocations($username, $filters = []) {
        if ($this->useDatabaseStorage) {
            return $this->getUserLocationsFromDatabase($username, $filters);
        } else {
            return $this->getUserLocationsFromFiles($username, $filters);
        }
    }
    
    /**
     * Mark location as anomaly
     */
    public function markLocationAnomaly($recordId, $userId, $anomalyType = 'user_marked') {
        if ($this->useDatabaseStorage) {
            return $this->markAnomalyInDatabase('location', $recordId, $userId, $anomalyType);
        } else {
            return $this->markAnomalyInFile($recordId);
        }
    }
    
    /**
     * Get anomaly statistics
     */
    public function getAnomalyStats($userId = null, $dateRange = null) {
        if ($this->useDatabaseStorage) {
            return $this->getAnomalyStatsFromDatabase($userId, $dateRange);
        } else {
            return $this->getAnomalyStatsFromFiles($userId, $dateRange);
        }
    }
    
    // =====================================================
    // DATABASE OPERATIONS
    // =====================================================
    
    private function insertLocationToDatabase($data) {
        try {
            $this->pdo->beginTransaction();

            // Get or create user
            $userId = $this->getOrCreateUser($data['name']);

            // Get or create device
            $deviceId = $this->getOrCreateDevice($data['id'], $userId);

            // Convert client timestamp
            $clientTimeIso = null;
            if (isset($data['client_time']) && is_numeric($data['client_time'])) {
                $clientTimeIso = date('Y-m-d H:i:s', intval($data['client_time'] / 1000));
            }

            // Insert location record
            $stmt = $this->pdo->prepare("
                INSERT INTO location_records (
                    device_id, user_id, server_time, client_time, client_time_iso,
                    latitude, longitude, accuracy, altitude, speed, bearing,
                    battery_level, network_type, provider, ip_address, user_agent,
                    source_type, created_at, updated_at
                ) VALUES (
                    ?, ?, NOW(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'realtime', NOW(), NOW()
                )
            ");

            $result = $stmt->execute([
                $deviceId,  // Fixed: should be deviceId, not data['id']
                $userId,
                $data['client_time'] ?? null,
                $clientTimeIso,
                $data['latitude'],
                $data['longitude'],
                $data['accuracy'] ?? null,
                $data['altitude'] ?? null,
                $data['speed'] ?? null,
                $data['bearing'] ?? null,
                $data['battery_level'] ?? null,
                $data['network_type'] ?? null,
                $data['provider'] ?? null,
                $data['ip'] ?? null,
                $data['user_agent'] ?? null
            ]);

            $recordId = $this->pdo->lastInsertId();

            // Run anomaly detection
            $this->runAnomalyDetection($recordId, $data);

            // Update real-time tracking tables (device_last_position and location_history_cache)
            // Note: Pass the original device_id string, not the database ID
            $this->updateRealtimeTracking($data, $userId, $data['id']);

            $this->pdo->commit();

            return [
                'success' => true,
                'record_id' => $recordId,
                'storage_mode' => 'database'
            ];

        } catch (Exception $e) {
            $this->pdo->rollback();
            error_log("Database insert failed: " . $e->getMessage());

            // Fallback to file storage
            return $this->insertLocationToFile($data);
        }
    }
    
    private function getOrCreateUser($username) {
        $stmt = $this->pdo->prepare("SELECT id FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($user) {
            return $user['id'];
        }
        
        // Create new user
        $stmt = $this->pdo->prepare("
            INSERT INTO users (username, display_name, created_at, updated_at) 
            VALUES (?, ?, NOW(), NOW())
        ");
        $stmt->execute([$username, $username]);
        
        return $this->pdo->lastInsertId();
    }
    
    private function getOrCreateDevice($deviceId, $userId) {
        $stmt = $this->pdo->prepare("SELECT id FROM devices WHERE device_id = ?");
        $stmt->execute([$deviceId]);
        $device = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($device) {
            // Update last seen
            $stmt = $this->pdo->prepare("UPDATE devices SET last_seen = NOW() WHERE device_id = ?");
            $stmt->execute([$deviceId]);
            return $device['id'];
        }
        
        // Create new device
        $stmt = $this->pdo->prepare("
            INSERT INTO devices (device_id, user_id, device_name, first_seen, last_seen) 
            VALUES (?, ?, ?, NOW(), NOW())
        ");
        $stmt->execute([$deviceId, $userId, $deviceId]);
        
        return $this->pdo->lastInsertId();
    }
    
    private function runAnomalyDetection($recordId, $data) {
        // Basic anomaly detection - can be enhanced
        $anomalies = [];
        
        // Poor accuracy detection
        if (isset($data['accuracy']) && $data['accuracy'] > 50) {
            $anomalies[] = [
                'type' => 'poor_accuracy',
                'confidence' => min(100, ($data['accuracy'] - 50) * 2),
                'description' => "GPS accuracy is {$data['accuracy']}m (threshold: 50m)",
                'threshold_value' => 50,
                'actual_value' => $data['accuracy']
            ];
        }
        
        // Excessive speed detection
        if (isset($data['speed']) && $data['speed'] > 55.56) { // 200 km/h in m/s
            $anomalies[] = [
                'type' => 'excessive_speed',
                'confidence' => min(100, ($data['speed'] - 55.56) * 5),
                'description' => "Speed is {$data['speed']} m/s (threshold: 55.56 m/s / 200 km/h)",
                'threshold_value' => 55.56,
                'actual_value' => $data['speed']
            ];
        }
        
        // Insert anomaly detections
        foreach ($anomalies as $anomaly) {
            $stmt = $this->pdo->prepare("
                INSERT INTO anomaly_detections (
                    record_type, record_id, anomaly_type, confidence_score, description,
                    threshold_value, actual_value, detection_algorithm, detected_at
                ) VALUES (
                    'location', ?, ?, ?, ?, ?, ?, 'basic_v1', NOW()
                )
            ");

            $stmt->execute([
                $recordId,
                $anomaly['type'],
                $anomaly['confidence'],
                $anomaly['description'],
                $anomaly['threshold_value'],
                $anomaly['actual_value']
            ]);
        }
    }

    /**
     * Update real-time tracking tables (device_last_position and location_history_cache)
     * This enables live tracking endpoints to work properly
     */
    private function updateRealtimeTracking($data, $userId, $deviceId) {
        try {
            // recorded_at is BIGINT (milliseconds timestamp), not datetime
            $recordedAt = $data['client_time'] ?? (time() * 1000);

            // 1. Update device_last_position (UPSERT)
            // Note: Removed network_type and provider columns for compatibility
            $stmt = $this->pdo->prepare("
                INSERT INTO device_last_position (
                    device_id, user_id, latitude, longitude, accuracy, altitude,
                    speed, bearing, recorded_at, server_time,
                    battery_level
                ) VALUES (
                    :device_id, :user_id, :latitude, :longitude, :accuracy, :altitude,
                    :speed, :bearing, :recorded_at, NOW(),
                    :battery_level
                )
                ON DUPLICATE KEY UPDATE
                    latitude = VALUES(latitude),
                    longitude = VALUES(longitude),
                    accuracy = VALUES(accuracy),
                    altitude = VALUES(altitude),
                    speed = VALUES(speed),
                    bearing = VALUES(bearing),
                    recorded_at = VALUES(recorded_at),
                    server_time = NOW(),
                    battery_level = VALUES(battery_level),
                    updated_at = NOW()
            ");

            $stmt->execute([
                ':device_id' => $deviceId,
                ':user_id' => $userId,
                ':latitude' => $data['latitude'],
                ':longitude' => $data['longitude'],
                ':accuracy' => $data['accuracy'] ?? null,
                ':altitude' => $data['altitude'] ?? null,
                ':speed' => $data['speed'] ?? null,
                ':bearing' => $data['bearing'] ?? null,
                ':recorded_at' => $recordedAt,
                ':battery_level' => $data['battery_level'] ?? null
            ]);

            // 2. Insert into location_history_cache (for recent history)
            // Note: location_history_cache has fewer columns than device_last_position
            $stmt = $this->pdo->prepare("
                INSERT INTO location_history_cache (
                    device_id, user_id, latitude, longitude, accuracy, altitude,
                    speed, bearing, recorded_at, server_time, battery_level
                ) VALUES (
                    :device_id, :user_id, :latitude, :longitude, :accuracy, :altitude,
                    :speed, :bearing, :recorded_at, NOW(), :battery_level
                )
            ");

            $stmt->execute([
                ':device_id' => $deviceId,
                ':user_id' => $userId,
                ':latitude' => $data['latitude'],
                ':longitude' => $data['longitude'],
                ':accuracy' => $data['accuracy'] ?? null,
                ':altitude' => $data['altitude'] ?? null,
                ':speed' => $data['speed'] ?? null,
                ':bearing' => $data['bearing'] ?? null,
                ':recorded_at' => $recordedAt,
                ':battery_level' => $data['battery_level'] ?? null
            ]);

            return true;

        } catch (Exception $e) {
            // Log error but don't fail the main insert
            error_log("Real-time tracking update failed: " . $e->getMessage());
            return false;
        }
    }
    
    // =====================================================
    // FILE OPERATIONS (FALLBACK)
    // =====================================================
    
    private function insertLocationToFile($data) {
        $safeName = preg_replace('/[^a-zA-Z0-9 _.\-]/', '_', trim($data['name']));
        $safeName = preg_replace('/[ _]+/', '_', $safeName);
        $safeName = $safeName !== '' ? $safeName : 'unknown';
        
        $userDir = $this->logDir . '/' . $safeName;
        @mkdir($userDir, 0755, true);
        
        $date = date('Y-m-d');
        $logFile = $userDir . '/location-' . $safeName . '-' . $date . '.log';
        
        $entry = [
            'server_time' => date('c'),
            'id' => $data['id'],
            'name' => $data['name'],
            'client_time' => $data['client_time'] ?? null,
            'latitude' => $data['latitude'],
            'longitude' => $data['longitude'],
            'accuracy' => $data['accuracy'] ?? null,
            'speed' => $data['speed'] ?? null,
            'bearing' => $data['bearing'] ?? null,
            'altitude' => $data['altitude'] ?? null,
            'battery_level' => $data['battery_level'] ?? null,
            'network_type' => $data['network_type'] ?? null,
            'provider' => $data['provider'] ?? null,
            'ip' => $data['ip'] ?? null,
            'ua' => $data['user_agent'] ?? null,
        ];
        
        $success = @file_put_contents(
            $logFile,
            json_encode($entry, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL,
            FILE_APPEND | LOCK_EX
        );
        
        return [
            'success' => $success !== false,
            'storage_mode' => 'file',
            'file_path' => $logFile
        ];
    }
    
    private function getLocationsFromDatabase($filters = []) {
        // Implementation for database queries
        // This will be expanded based on specific filter requirements
        return [];
    }
    
    private function getLocationsFromFiles($filters = []) {
        // Implementation for file-based queries
        // This will be expanded based on specific filter requirements
        return [];
    }
    
    private function getUserLocationsFromDatabase($username, $filters = []) {
        // Implementation for user-specific database queries
        return [];
    }
    
    private function getUserLocationsFromFiles($username, $filters = []) {
        // Implementation for user-specific file queries
        return [];
    }
    
    private function markAnomalyInDatabase($recordType, $recordId, $userId, $anomalyType) {
        // Implementation for database anomaly marking
        return false;
    }
    
    private function markAnomalyInFile($recordId) {
        // Implementation for file-based anomaly marking
        return false;
    }
    
    private function getAnomalyStatsFromDatabase($userId, $dateRange) {
        // Implementation for database anomaly statistics
        return [];
    }
    
    private function getAnomalyStatsFromFiles($userId, $dateRange) {
        // Implementation for file-based anomaly statistics
        return [];
    }
}
?>
