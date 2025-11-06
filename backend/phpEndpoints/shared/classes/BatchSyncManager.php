<?php
/**
 * Batch Sync Manager Class
 * 
 * Handles the batch synchronization logic with database and file fallback
 * 
 * @version 1.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/../db-config.php';
require_once __DIR__ . '/LocationDataManager.php';
require_once __DIR__ . '/DrivingDataManager.php';

class BatchSyncManager {
    private $useDatabaseStorage;
    private $pdo;
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
    
    public function processBatchPart($data) {
        if ($this->useDatabaseStorage) {
            return $this->processBatchDatabase($data);
        } else {
            return $this->processBatchFiles($data);
        }
    }
    
    private function processBatchDatabase($data) {
        try {
            // Simplified database processing - just use individual record insertion
            $locationManager = new LocationDataManager();
            $drivingManager = new DrivingDataManager();

            $processed = [
                'location' => 0,
                'driving' => 0,
                'errors' => 0
            ];

            foreach ($data['records'] as $record) {
                try {
                    // Add batch metadata
                    $record['id'] = $data['device_id'];
                    $record['name'] = $data['user_name'];
                    $record['client_time'] = $record['timestamp'];
                    $record['ip'] = $data['ip'] ?? null;
                    $record['user_agent'] = $data['user_agent'] ?? null;

                    if ($record['type'] === 'location') {
                        $result = $locationManager->insertLocationRecord($record);
                        if ($result && isset($result['success']) && $result['success']) {
                            $processed['location']++;
                        } else {
                            $processed['errors']++;
                        }
                    } elseif ($record['type'] === 'driving') {
                        // For driving records, we need to restructure the data
                        $drivingData = [
                            'id' => $record['id'],
                            'name' => $record['name'],
                            'event' => $record['event_type'] ?? 'data',
                            'timestamp' => $record['timestamp'],
                            'location' => $record['location'] ?? [
                                'latitude' => $record['latitude'],
                                'longitude' => $record['longitude'],
                                'accuracy' => $record['accuracy'] ?? null
                            ],
                            'speed' => $record['speed'] ?? null,
                            'bearing' => $record['bearing'] ?? null,
                            'altitude' => $record['altitude'] ?? null
                        ];

                        $result = $drivingManager->insertDrivingEvent($drivingData);
                        if ($result && isset($result['success']) && $result['success']) {
                            $processed['driving']++;
                        } else {
                            $processed['errors']++;
                        }
                    }
                } catch (Exception $e) {
                    error_log("Failed to process record: " . $e->getMessage());
                    $processed['errors']++;
                }
            }

            return [
                'success' => true,
                'storage_mode' => 'database',
                'sync_complete' => true, // Simplified - assume single part completion
                'processing_results' => $processed
            ];

        } catch (Exception $e) {
            error_log("Database batch sync failed: " . $e->getMessage());

            // Fallback to file storage
            return $this->processBatchFiles($data);
        }
    }
    
    private function processBatchFiles($data) {
        // Group records by type and date
        $locationRecords = [];
        $drivingRecords = [];
        
        foreach ($data['records'] as $record) {
            $date = date('Y-m-d', intval($record['timestamp'] / 1000));
            
            if ($record['type'] === 'location') {
                if (!isset($locationRecords[$date])) $locationRecords[$date] = [];
                $locationRecords[$date][] = $record;
            } elseif ($record['type'] === 'driving') {
                if (!isset($drivingRecords[$date])) $drivingRecords[$date] = [];
                $drivingRecords[$date][] = $record;
            }
        }
        
        // Write to log files
        $results = [];
        $sanitizedName = preg_replace('/[^a-zA-Z0-9_-]/', '_', $data['user_name']);
        $userDir = $this->logDir . '/' . $sanitizedName;
        if (!is_dir($userDir)) @mkdir($userDir, 0755, true);
        
        // Process location records
        foreach ($locationRecords as $date => $records) {
            $logFile = $userDir . '/location-' . $sanitizedName . '-' . $date . '.log';
            $written = 0;
            
            foreach ($records as $record) {
                $logEntry = [
                    'server_time' => date('c'),
                    'id' => $data['device_id'],
                    'name' => $data['user_name'],
                    'client_time' => $record['timestamp'],
                    'latitude' => $record['latitude'],
                    'longitude' => $record['longitude'],
                    'accuracy' => $record['accuracy'] ?? null,
                    'altitude' => $record['altitude'] ?? null,
                    'speed' => $record['speed'] ?? null,
                    'bearing' => $record['bearing'] ?? null,
                    'battery_level' => $record['battery_level'] ?? null,
                    'network_type' => $record['network_type'] ?? null,
                    'provider' => $record['provider'] ?? null,
                    'ip' => $data['ip'] ?? null,
                    'ua' => $data['user_agent'] ?? null
                ];
                
                if (@file_put_contents($logFile, json_encode($logEntry) . "\n", FILE_APPEND | LOCK_EX)) {
                    $written++;
                }
            }
            
            $results['location'][$date] = $written;
        }
        
        // Process driving records
        foreach ($drivingRecords as $date => $records) {
            $logFile = $userDir . '/driving-' . $sanitizedName . '-' . $date . '.log';
            $written = 0;
            
            foreach ($records as $record) {
                $logEntry = [
                    'server_time' => date('c'),
                    'id' => $data['device_id'],
                    'name' => $data['user_name'],
                    'event_type' => $record['event_type'] ?? 'data',
                    'client_time' => $record['timestamp'],
                    'location' => $record['location'] ?? [
                        'latitude' => $record['latitude'],
                        'longitude' => $record['longitude']
                    ],
                    'speed' => $record['speed'] ?? null,
                    'bearing' => $record['bearing'] ?? null,
                    'altitude' => $record['altitude'] ?? null,
                    'ip' => $data['ip'] ?? null,
                    'ua' => $data['user_agent'] ?? null
                ];
                
                if (@file_put_contents($logFile, json_encode($logEntry) . "\n", FILE_APPEND | LOCK_EX)) {
                    $written++;
                }
            }
            
            $results['driving'][$date] = $written;
        }
        
        return [
            'success' => true,
            'storage_mode' => 'file',
            'sync_complete' => true, // File mode doesn't track multi-part syncs
            'processing_results' => $results
        ];
    }
}
?>
