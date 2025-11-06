<?php
/**
 * Stats Manager
 * 
 * Handles statistics calculation for devices
 * Supports multiple timeframes with timezone awareness
 * 
 * @version 1.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/StatsCache.php';

class StatsManager {
    private $pdo;
    private $cache;
    private $timezone;
    private $queryTimeout = 5; // 5 seconds max per query
    
    public function __construct($pdo = null) {
        $this->pdo = $pdo;
        $this->cache = new StatsCache();
        $this->timezone = new DateTimeZone('Asia/Jerusalem');
    }
    
    /**
     * Get stats for a device by device_name
     */
    public function getStats($deviceName, $timeframe = 'today', $customFrom = null, $customTo = null) {
        // Validate inputs
        if (empty($deviceName)) {
            throw new InvalidArgumentException('device_name is required');
        }

        // Resolve device_name to device id
        $deviceId = $this->resolveDeviceName($deviceName);
        if (!$deviceId) {
            throw new InvalidArgumentException('Device not found: ' . $deviceName);
        }

        // Resolve timeframe to date range
        $range = $this->resolveTimeframe($timeframe, $customFrom, $customTo);
        
        // Check cache (use device_name for cache key)
        $cacheKey = $this->cache->generateKey($deviceName, $timeframe, $range['from'], $range['to']);
        $cached = $this->cache->get($cacheKey);

        if ($cached !== null) {
            $cached['meta']['cached'] = true;
            return $cached;
        }

        // Calculate stats
        $stats = [
            'device_name' => $deviceName,
            'device_id' => $deviceId,
            'timeframe' => $timeframe,
            'range' => [
                'from' => $range['from_iso'],
                'to' => $range['to_iso']
            ],
            'counts' => $this->getCounts($deviceId, $range['from'], $range['to']),
            'meta' => $this->getMeta($deviceId)
        ];
        
        // Cache the result
        $ttl = $this->cache->getTtlForTimeframe($timeframe);
        $this->cache->set($cacheKey, $stats, $ttl);
        
        $stats['meta']['cached'] = false;
        
        return $stats;
    }

    /**
     * Resolve device_name to device id
     *
     * @param string $deviceName The device name to look up
     * @return int|null The device id, or null if not found
     */
    private function resolveDeviceName($deviceName) {
        if (!$this->pdo) {
            // In file mode, just return the device name as-is
            return $deviceName;
        }

        try {
            $stmt = $this->pdo->prepare("
                SELECT id
                FROM devices
                WHERE device_name = ?
                LIMIT 1
            ");
            $stmt->execute([$deviceName]);
            $result = $stmt->fetch(PDO::FETCH_ASSOC);

            return $result ? $result['id'] : null;
        } catch (PDOException $e) {
            error_log("Error resolving device name: " . $e->getMessage());
            return null;
        }
    }

    /**
     * Resolve timeframe to actual date range
     */
    private function resolveTimeframe($timeframe, $customFrom = null, $customTo = null) {
        $now = new DateTime('now', $this->timezone);
        
        switch ($timeframe) {
            case 'today':
                $from = new DateTime('today', $this->timezone);
                $to = clone $now;
                break;
                
            case 'last_24h':
                $from = (clone $now)->modify('-24 hours');
                $to = clone $now;
                break;
                
            case 'last_7d':
                $from = (clone $now)->modify('-7 days');
                $to = clone $now;
                break;
                
            case 'last_week':
                // Last Monday to Sunday
                $from = new DateTime('last monday', $this->timezone);
                $to = (clone $from)->modify('+6 days 23:59:59');
                break;
                
            case 'total':
                $from = new DateTime('2000-01-01', $this->timezone);
                $to = clone $now;
                break;
                
            case 'custom':
                if (!$customFrom || !$customTo) {
                    throw new InvalidArgumentException('custom timeframe requires from and to parameters');
                }
                $from = new DateTime($customFrom, $this->timezone);
                $to = new DateTime($customTo, $this->timezone);
                break;
                
            default:
                throw new InvalidArgumentException('Invalid timeframe: ' . $timeframe);
        }
        
        return [
            'from' => $from->format('Y-m-d H:i:s'),
            'to' => $to->format('Y-m-d H:i:s'),
            'from_iso' => $from->format('c'),
            'to_iso' => $to->format('c')
        ];
    }
    
    /**
     * Get counts for the specified range
     */
    private function getCounts($deviceId, $from, $to) {
        if (!$this->pdo) {
            return $this->getCountsFromFiles($deviceId, $from, $to);
        }
        
        $counts = [
            'location_updates' => 0,
            'driving_sessions' => 0,
            'updates_realtime' => 0,
            'updates_batched' => 0
        ];
        
        try {
            // Set query timeout
            $this->pdo->setAttribute(PDO::ATTR_TIMEOUT, $this->queryTimeout);
            
            // Count location updates
            $stmt = $this->pdo->prepare("
                SELECT COUNT(*) as total
                FROM location_records
                WHERE device_id = ?
                AND server_time BETWEEN ? AND ?
            ");
            $stmt->execute([$deviceId, $from, $to]);
            $counts['location_updates'] = (int)$stmt->fetchColumn();

            // Count by source type
            $stmt = $this->pdo->prepare("
                SELECT
                    source_type,
                    COUNT(*) as count
                FROM location_records
                WHERE device_id = ?
                AND server_time BETWEEN ? AND ?
                GROUP BY source_type
            ");
            $stmt->execute([$deviceId, $from, $to]);
            
            while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
                if ($row['source_type'] === 'realtime') {
                    $counts['updates_realtime'] = (int)$row['count'];
                } elseif ($row['source_type'] === 'batch') {
                    $counts['updates_batched'] = (int)$row['count'];
                }
            }
            
            // Count driving sessions
            $stmt = $this->pdo->prepare("
                SELECT COUNT(DISTINCT trip_id) as total
                FROM driving_records
                WHERE device_id = ?
                AND server_time BETWEEN ? AND ?
                AND trip_id IS NOT NULL
            ");
            $stmt->execute([$deviceId, $from, $to]);
            $counts['driving_sessions'] = (int)$stmt->fetchColumn();
            
        } catch (PDOException $e) {
            error_log("Stats query error: " . $e->getMessage());
            // Return partial data on error
        }
        
        return $counts;
    }
    
    /**
     * Get metadata about the device
     */
    private function getMeta($deviceId) {
        $meta = [
            'first_seen_at' => null,
            'last_update_at' => null,
            'generated_at' => gmdate('c'),
            'version' => '1.0'
        ];
        
        if (!$this->pdo) {
            return $meta;
        }
        
        try {
            // Get first and last update times
            $stmt = $this->pdo->prepare("
                SELECT
                    MIN(server_time) as first_seen,
                    MAX(server_time) as last_update
                FROM location_records
                WHERE device_id = ?
            ");
            $stmt->execute([$deviceId]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($row) {
                if ($row['first_seen']) {
                    $dt = new DateTime($row['first_seen'], new DateTimeZone('UTC'));
                    $meta['first_seen_at'] = $dt->format('c');
                }
                if ($row['last_update']) {
                    $dt = new DateTime($row['last_update'], new DateTimeZone('UTC'));
                    $meta['last_update_at'] = $dt->format('c');
                }
            }
            
        } catch (PDOException $e) {
            error_log("Stats meta query error: " . $e->getMessage());
        }
        
        return $meta;
    }
    
    /**
     * Fallback: Get counts from files (when database unavailable)
     */
    private function getCountsFromFiles($deviceId, $from, $to) {
        // Simplified file-based counting
        // In production, this would scan log files
        return [
            'location_updates' => 0,
            'driving_sessions' => 0,
            'updates_realtime' => 0,
            'updates_batched' => 0
        ];
    }
    
    /**
     * Validate device exists
     */
    public function deviceExists($deviceId) {
        if (!$this->pdo) {
            return true; // Assume exists in file mode
        }
        
        try {
            $stmt = $this->pdo->prepare("
                SELECT COUNT(*) FROM devices WHERE device_id = ?
            ");
            $stmt->execute([$deviceId]);
            return $stmt->fetchColumn() > 0;
        } catch (PDOException $e) {
            return true; // Assume exists on error
        }
    }
    
    /**
     * Clear cache for a device
     */
    public function clearCache($deviceId) {
        return $this->cache->clearDevice($deviceId);
    }
    
    /**
     * Get cache statistics
     */
    public function getCacheStats() {
        return $this->cache->getStats();
    }
}

