<?php
/**
 * Duplicate Detector
 * 
 * Detects duplicate and stale location updates to maintain data quality.
 * Uses in-memory cache (APCu) or database fallback.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

class DuplicateDetector {
    private $pdo;
    private $useApcu;
    private $cacheTtl;
    private $staleThreshold;
    
    /**
     * Constructor
     * 
     * @param PDO|null $pdo Database connection (optional, for fallback)
     * @param int $cacheTtl Cache TTL in seconds (default: 300 = 5 min)
     * @param int $staleThreshold Stale threshold in seconds (default: 300 = 5 min)
     */
    public function __construct($pdo = null, $cacheTtl = 300, $staleThreshold = 300) {
        $this->pdo = $pdo;
        $this->useApcu = extension_loaded('apcu') && apcu_enabled();
        $this->cacheTtl = $cacheTtl;
        $this->staleThreshold = $staleThreshold;
    }
    
    /**
     * Check if location is a duplicate
     * 
     * @param string $deviceId Device ID
     * @param array $location Location data
     * @return bool True if duplicate, false otherwise
     */
    public function isDuplicate($deviceId, $location) {
        $hash = $this->generateHash($deviceId, $location);
        
        if ($this->useApcu) {
            return $this->checkApcuCache($hash);
        } else {
            return $this->checkMemoryCache($hash);
        }
    }
    
    /**
     * Mark location as seen (to detect future duplicates)
     * 
     * @param string $deviceId Device ID
     * @param array $location Location data
     */
    public function markAsSeen($deviceId, $location) {
        $hash = $this->generateHash($deviceId, $location);
        
        if ($this->useApcu) {
            $this->storeInApcuCache($hash);
        } else {
            $this->storeInMemoryCache($hash);
        }
    }
    
    /**
     * Check if location is stale (too old)
     * 
     * @param array $location Location data
     * @return array ['is_stale' => bool, 'age_seconds' => int]
     */
    public function isStale($location) {
        $clientTime = $location['client_time'] ?? $location['timestamp'] ?? null;
        
        if (!$clientTime) {
            // No timestamp, assume not stale
            return [
                'is_stale' => false,
                'age_seconds' => 0
            ];
        }
        
        // Convert milliseconds to seconds if needed
        if ($clientTime > 10000000000) {
            $clientTime = $clientTime / 1000;
        }
        
        $serverTime = time();
        $age = $serverTime - $clientTime;
        
        return [
            'is_stale' => $age > $this->staleThreshold,
            'age_seconds' => (int)$age
        ];
    }
    
    /**
     * Generate hash for location
     * 
     * @param string $deviceId Device ID
     * @param array $location Location data
     * @return string Hash
     */
    private function generateHash($deviceId, $location) {
        // Round coordinates to 6 decimal places (~0.1 meter precision)
        $lat = round($location['latitude'], 6);
        $lon = round($location['longitude'], 6);
        $time = $location['client_time'] ?? $location['timestamp'] ?? 0;
        
        return md5("$deviceId:$lat:$lon:$time");
    }
    
    /**
     * Check APCu cache for hash
     * 
     * @param string $hash Hash to check
     * @return bool True if exists, false otherwise
     */
    private function checkApcuCache($hash) {
        $key = "loc:hash:$hash";
        return apcu_exists($key);
    }
    
    /**
     * Store hash in APCu cache
     * 
     * @param string $hash Hash to store
     */
    private function storeInApcuCache($hash) {
        $key = "loc:hash:$hash";
        apcu_store($key, 1, $this->cacheTtl);
    }
    
    /**
     * Check in-memory cache for hash (session-based fallback)
     * 
     * @param string $hash Hash to check
     * @return bool True if exists, false otherwise
     */
    private function checkMemoryCache($hash) {
        if (!isset($_SESSION)) {
            session_start();
        }
        
        if (!isset($_SESSION['location_hashes'])) {
            $_SESSION['location_hashes'] = [];
        }
        
        // Clean up expired hashes
        $now = time();
        $_SESSION['location_hashes'] = array_filter(
            $_SESSION['location_hashes'],
            function($expiry) use ($now) {
                return $expiry > $now;
            }
        );
        
        return isset($_SESSION['location_hashes'][$hash]);
    }
    
    /**
     * Store hash in in-memory cache (session-based fallback)
     * 
     * @param string $hash Hash to store
     */
    private function storeInMemoryCache($hash) {
        if (!isset($_SESSION)) {
            session_start();
        }
        
        if (!isset($_SESSION['location_hashes'])) {
            $_SESSION['location_hashes'] = [];
        }
        
        $_SESSION['location_hashes'][$hash] = time() + $this->cacheTtl;
    }
    
    /**
     * Get cache statistics
     * 
     * @return array Cache stats
     */
    public function getCacheStats() {
        $stats = [
            'cache_type' => $this->useApcu ? 'apcu' : 'session',
            'ttl_seconds' => $this->cacheTtl,
            'stale_threshold_seconds' => $this->staleThreshold
        ];
        
        if ($this->useApcu) {
            $info = apcu_cache_info();
            $stats['apcu_memory_size'] = $info['mem_size'] ?? 0;
            $stats['apcu_num_entries'] = $info['num_entries'] ?? 0;
        } else {
            if (!isset($_SESSION)) {
                session_start();
            }
            $stats['session_hash_count'] = count($_SESSION['location_hashes'] ?? []);
        }
        
        return $stats;
    }
    
    /**
     * Clear cache
     */
    public function clearCache() {
        if ($this->useApcu) {
            apcu_clear_cache();
        } else {
            if (!isset($_SESSION)) {
                session_start();
            }
            $_SESSION['location_hashes'] = [];
        }
    }
}

