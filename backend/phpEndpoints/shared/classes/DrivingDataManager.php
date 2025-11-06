<?php
/**
 * Driving Data Manager
 * 
 * Handles all driving event data operations with database and file fallback support
 * Manages trip sessions and driving event lifecycle
 * 
 * @version 2.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/../db-config.php';

class DrivingDataManager {
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
     * Insert driving event record
     */
    public function insertDrivingEvent($data) {
        if ($this->useDatabaseStorage) {
            return $this->insertDrivingToDatabase($data);
        } else {
            return $this->insertDrivingToFile($data);
        }
    }
    
    /**
     * Handle driving start event
     */
    public function handleDrivingStart($data) {
        if ($this->useDatabaseStorage) {
            return $this->handleDrivingStartDatabase($data);
        } else {
            return $this->handleDrivingStartFile($data);
        }
    }
    
    /**
     * Handle driving data event
     */
    public function handleDrivingData($data) {
        if ($this->useDatabaseStorage) {
            return $this->handleDrivingDataDatabase($data);
        } else {
            return $this->handleDrivingDataFile($data);
        }
    }
    
    /**
     * Handle driving stop event
     */
    public function handleDrivingStop($data) {
        if ($this->useDatabaseStorage) {
            return $this->handleDrivingStopDatabase($data);
        } else {
            return $this->handleDrivingStopFile($data);
        }
    }
    
    /**
     * Get driving sessions for user
     */
    public function getDrivingSessions($username, $filters = []) {
        if ($this->useDatabaseStorage) {
            return $this->getDrivingSessionsFromDatabase($username, $filters);
        } else {
            return $this->getDrivingSessionsFromFiles($username, $filters);
        }
    }
    
    // =====================================================
    // DATABASE OPERATIONS
    // =====================================================
    
    private function insertDrivingToDatabase($data) {
        try {
            $this->pdo->beginTransaction();
            
            // Get or create user
            $userId = $this->getOrCreateUser($data['name']);
            
            // Convert client timestamp
            $clientTimeIso = null;
            if (isset($data['client_time']) && is_numeric($data['client_time'])) {
                $clientTimeIso = date('Y-m-d H:i:s', intval($data['client_time'] / 1000));
            }
            
            // Extract location data
            $location = $data['location'] ?? [];
            $latitude = $location['latitude'] ?? null;
            $longitude = $location['longitude'] ?? null;
            
            // Insert driving record
            $stmt = $this->pdo->prepare("
                INSERT INTO driving_records (
                    device_id, user_id, server_time, client_time, client_time_iso,
                    event_type, trip_id, latitude, longitude, accuracy, altitude,
                    speed, bearing, trip_summary, ip_address, user_agent,
                    source_type, created_at, updated_at
                ) VALUES (
                    ?, ?, NOW(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'realtime', NOW(), NOW()
                )
            ");
            
            $result = $stmt->execute([
                $data['id'],
                $userId,
                $data['client_time'] ?? null,
                $clientTimeIso,
                $data['event_type'],
                $data['trip_id'] ?? null,
                $latitude,
                $longitude,
                $location['accuracy'] ?? null,
                $location['altitude'] ?? null,
                $data['speed'] ?? null,
                $data['bearing'] ?? null,
                isset($data['trip_summary']) ? json_encode($data['trip_summary']) : null,
                $data['ip'] ?? null,
                $data['user_agent'] ?? null
            ]);
            
            $recordId = $this->pdo->lastInsertId();
            
            $this->pdo->commit();
            
            return [
                'success' => true,
                'record_id' => $recordId,
                'storage_mode' => 'database'
            ];
            
        } catch (Exception $e) {
            $this->pdo->rollback();
            error_log("Database driving insert failed: " . $e->getMessage());
            
            // Fallback to file storage
            return $this->insertDrivingToFile($data);
        }
    }
    
    private function handleDrivingStartDatabase($data) {
        try {
            // Check for existing active trip
            $stmt = $this->pdo->prepare("
                SELECT trip_id FROM driving_records 
                WHERE device_id = ? AND event_type = 'driving_start' 
                AND NOT EXISTS (
                    SELECT 1 FROM driving_records dr2 
                    WHERE dr2.device_id = driving_records.device_id 
                    AND dr2.trip_id = driving_records.trip_id 
                    AND dr2.event_type = 'driving_stop'
                    AND dr2.created_at > driving_records.created_at
                )
                ORDER BY created_at DESC LIMIT 1
            ");
            $stmt->execute([$data['id']]);
            $existingTrip = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($existingTrip) {
                return [
                    'status' => 'warning',
                    'message' => 'Trip already active for this device',
                    'trip_id' => $existingTrip['trip_id']
                ];
            }
            
            // Create new trip
            $tripId = $data['id'] . '_' . time();
            $data['trip_id'] = $tripId;
            $data['event_type'] = 'driving_start';
            
            $result = $this->insertDrivingToDatabase($data);
            
            if ($result['success']) {
                return [
                    'status' => 'success',
                    'message' => 'Driving trip started',
                    'trip_id' => $tripId
                ];
            } else {
                return [
                    'status' => 'error',
                    'message' => 'Failed to start trip'
                ];
            }
            
        } catch (Exception $e) {
            error_log("Database driving start failed: " . $e->getMessage());
            return $this->handleDrivingStartFile($data);
        }
    }
    
    private function handleDrivingDataDatabase($data) {
        try {
            // Find active trip
            $stmt = $this->pdo->prepare("
                SELECT trip_id FROM driving_records 
                WHERE device_id = ? AND event_type = 'driving_start' 
                AND NOT EXISTS (
                    SELECT 1 FROM driving_records dr2 
                    WHERE dr2.device_id = driving_records.device_id 
                    AND dr2.trip_id = driving_records.trip_id 
                    AND dr2.event_type = 'driving_stop'
                    AND dr2.created_at > driving_records.created_at
                )
                ORDER BY created_at DESC LIMIT 1
            ");
            $stmt->execute([$data['id']]);
            $activeTrip = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$activeTrip) {
                return [
                    'status' => 'error',
                    'message' => 'No active trip found for this device'
                ];
            }
            
            $data['trip_id'] = $activeTrip['trip_id'];
            $data['event_type'] = 'driving_data';
            
            $result = $this->insertDrivingToDatabase($data);
            
            if ($result['success']) {
                return [
                    'status' => 'success',
                    'message' => 'Driving data received',
                    'trip_id' => $activeTrip['trip_id']
                ];
            } else {
                return [
                    'status' => 'error',
                    'message' => 'Failed to record driving data'
                ];
            }
            
        } catch (Exception $e) {
            error_log("Database driving data failed: " . $e->getMessage());
            return $this->handleDrivingDataFile($data);
        }
    }
    
    private function handleDrivingStopDatabase($data) {
        try {
            // Find active trip
            $stmt = $this->pdo->prepare("
                SELECT trip_id FROM driving_records 
                WHERE device_id = ? AND event_type = 'driving_start' 
                AND NOT EXISTS (
                    SELECT 1 FROM driving_records dr2 
                    WHERE dr2.device_id = driving_records.device_id 
                    AND dr2.trip_id = driving_records.trip_id 
                    AND dr2.event_type = 'driving_stop'
                    AND dr2.created_at > driving_records.created_at
                )
                ORDER BY created_at DESC LIMIT 1
            ");
            $stmt->execute([$data['id']]);
            $activeTrip = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$activeTrip) {
                return [
                    'status' => 'error',
                    'message' => 'No active trip found for this device'
                ];
            }
            
            $data['trip_id'] = $activeTrip['trip_id'];
            $data['event_type'] = 'driving_stop';
            
            $result = $this->insertDrivingToDatabase($data);
            
            if ($result['success']) {
                return [
                    'status' => 'success',
                    'message' => 'Driving trip stopped',
                    'trip_id' => $activeTrip['trip_id']
                ];
            } else {
                return [
                    'status' => 'error',
                    'message' => 'Failed to stop trip'
                ];
            }
            
        } catch (Exception $e) {
            error_log("Database driving stop failed: " . $e->getMessage());
            return $this->handleDrivingStopFile($data);
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
    
    // =====================================================
    // FILE OPERATIONS (FALLBACK)
    // =====================================================
    
    private function insertDrivingToFile($data) {
        $safeName = preg_replace('/[^a-zA-Z0-9 _.\-]/', '_', trim($data['name']));
        $safeName = preg_replace('/[ _]+/', '_', $safeName);
        $safeName = $safeName !== '' ? $safeName : 'unknown';
        
        $userDir = $this->logDir . '/' . $safeName;
        @mkdir($userDir, 0755, true);
        
        $date = date('Y-m-d');
        $logFile = $userDir . '/driving-' . $safeName . '-' . $date . '.log';
        
        $entry = [
            'server_time' => date('c'),
            'id' => $data['id'],
            'name' => $data['name'],
            'event_type' => $data['event_type'],
            'client_time' => $data['client_time'] ?? null,
            'location' => $data['location'] ?? null,
            'speed' => $data['speed'] ?? null,
            'bearing' => $data['bearing'] ?? null,
            'altitude' => $data['altitude'] ?? null,
            'trip_summary' => $data['trip_summary'] ?? null,
            'trip_id' => $data['trip_id'] ?? null,
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
    
    private function handleDrivingStartFile($data) {
        // Load existing trip sessions
        $sessions = $this->loadTripSessions();
        $this->cleanExpiredSessions($sessions);
        
        $deviceKey = $data['id'];
        $now = time();
        
        // Check if already has active trip
        if (isset($sessions[$deviceKey])) {
            return [
                'status' => 'warning',
                'message' => 'Trip already active for this device',
                'trip_id' => $sessions[$deviceKey]['trip_id']
            ];
        }
        
        // Create new trip session
        $tripId = $deviceKey . '_' . $now;
        $sessions[$deviceKey] = [
            'trip_id' => $tripId,
            'start_time' => $now,
            'start_location' => $data['location'],
            'last_update' => $now
        ];
        
        $this->saveTripSessions($sessions);
        
        // Log the driving start event
        $data['trip_id'] = $tripId;
        $data['event_type'] = 'driving_start';
        $this->insertDrivingToFile($data);
        
        return [
            'status' => 'success',
            'message' => 'Driving trip started',
            'trip_id' => $tripId
        ];
    }
    
    private function handleDrivingDataFile($data) {
        $sessions = $this->loadTripSessions();
        $this->cleanExpiredSessions($sessions);
        
        $deviceKey = $data['id'];
        $now = time();
        
        // Check if has active trip
        if (!isset($sessions[$deviceKey])) {
            return [
                'status' => 'error',
                'message' => 'No active trip found for this device'
            ];
        }
        
        // Update session
        $sessions[$deviceKey]['last_update'] = $now;
        $this->saveTripSessions($sessions);
        
        // Log the driving data event
        $data['trip_id'] = $sessions[$deviceKey]['trip_id'];
        $data['event_type'] = 'driving_data';
        $this->insertDrivingToFile($data);
        
        return [
            'status' => 'success',
            'message' => 'Driving data received',
            'trip_id' => $sessions[$deviceKey]['trip_id']
        ];
    }
    
    private function handleDrivingStopFile($data) {
        $sessions = $this->loadTripSessions();
        $deviceKey = $data['id'];
        
        if (!isset($sessions[$deviceKey])) {
            return [
                'status' => 'error',
                'message' => 'No active trip found for this device'
            ];
        }
        
        $tripId = $sessions[$deviceKey]['trip_id'];
        
        // Remove session
        unset($sessions[$deviceKey]);
        $this->saveTripSessions($sessions);
        
        // Log the driving stop event
        $data['trip_id'] = $tripId;
        $data['event_type'] = 'driving_stop';
        $this->insertDrivingToFile($data);
        
        return [
            'status' => 'success',
            'message' => 'Driving trip stopped',
            'trip_id' => $tripId
        ];
    }
    
    private function loadTripSessions() {
        $sessionsFile = $this->logDir . '/trip_sessions.json';
        if (!file_exists($sessionsFile)) {
            return [];
        }
        
        $content = file_get_contents($sessionsFile);
        $sessions = json_decode($content, true);
        return is_array($sessions) ? $sessions : [];
    }
    
    private function saveTripSessions($sessions) {
        $sessionsFile = $this->logDir . '/trip_sessions.json';
        file_put_contents($sessionsFile, json_encode($sessions, JSON_PRETTY_PRINT));
    }
    
    private function cleanExpiredSessions(&$sessions) {
        $now = time();
        $expireTime = 24 * 60 * 60; // 24 hours
        
        foreach ($sessions as $deviceKey => $session) {
            if (($now - $session['last_update']) > $expireTime) {
                unset($sessions[$deviceKey]);
            }
        }
    }
    
    private function getDrivingSessionsFromDatabase($username, $filters = []) {
        // Implementation for database queries
        return [];
    }
    
    private function getDrivingSessionsFromFiles($username, $filters = []) {
        // Implementation for file-based queries
        return [];
    }
}
?>
