<?php
/**
 * Stats Cache Manager
 * 
 * Provides caching for stats endpoint to reduce database load
 * Uses APCu if available, falls back to file-based cache
 * 
 * @version 1.0
 * @author Adar Bahar
 */

class StatsCache {
    private $cacheDir;
    private $useApcu;
    private $defaultTtl = 60; // 60 seconds for recent data
    private $historicalTtl = 300; // 5 minutes for historical data
    
    public function __construct($cacheDir = null) {
        $this->cacheDir = $cacheDir ?? __DIR__ . '/../cache/stats';
        $this->useApcu = function_exists('apcu_fetch') && apcu_enabled();
        
        // Create cache directory if using file-based cache
        if (!$this->useApcu && !is_dir($this->cacheDir)) {
            @mkdir($this->cacheDir, 0755, true);
        }
    }
    
    /**
     * Generate cache key from parameters
     */
    public function generateKey($deviceId, $timeframe, $from = null, $to = null) {
        $parts = ['stats', $deviceId, $timeframe];
        
        if ($from) {
            $parts[] = date('YmdHis', strtotime($from));
        }
        if ($to) {
            $parts[] = date('YmdHis', strtotime($to));
        }
        
        return implode('_', $parts);
    }
    
    /**
     * Get cached stats
     */
    public function get($key) {
        if ($this->useApcu) {
            return $this->getFromApcu($key);
        }
        
        return $this->getFromFile($key);
    }
    
    /**
     * Set cached stats
     */
    public function set($key, $data, $ttl = null) {
        if ($ttl === null) {
            $ttl = $this->defaultTtl;
        }
        
        if ($this->useApcu) {
            return $this->setToApcu($key, $data, $ttl);
        }
        
        return $this->setToFile($key, $data, $ttl);
    }
    
    /**
     * Determine TTL based on timeframe
     */
    public function getTtlForTimeframe($timeframe) {
        // Recent data: shorter TTL
        if (in_array($timeframe, ['today', 'last_24h'])) {
            return $this->defaultTtl; // 60 seconds
        }
        
        // Historical data: longer TTL
        return $this->historicalTtl; // 5 minutes
    }
    
    /**
     * Clear cache for a specific device
     */
    public function clearDevice($deviceId) {
        if ($this->useApcu) {
            // APCu doesn't support pattern deletion, so we'd need to track keys
            // For now, just let them expire naturally
            return true;
        }
        
        // File-based: delete all files matching pattern
        $pattern = $this->cacheDir . '/stats_' . $deviceId . '_*.cache';
        $files = glob($pattern);
        
        foreach ($files as $file) {
            @unlink($file);
        }
        
        return true;
    }
    
    /**
     * Cleanup old cache files
     */
    public function cleanup() {
        if ($this->useApcu) {
            // APCu handles expiration automatically
            return true;
        }
        
        // File-based: delete expired files
        if (!is_dir($this->cacheDir)) {
            return false;
        }
        
        $files = glob($this->cacheDir . '/*.cache');
        $now = time();
        $deleted = 0;
        
        foreach ($files as $file) {
            $mtime = @filemtime($file);
            if ($mtime && ($now - $mtime) > $this->historicalTtl) {
                if (@unlink($file)) {
                    $deleted++;
                }
            }
        }
        
        return $deleted;
    }
    
    // ==================== Private Methods ====================
    
    private function getFromApcu($key) {
        $success = false;
        $data = apcu_fetch($key, $success);
        
        if ($success) {
            return json_decode($data, true);
        }
        
        return null;
    }
    
    private function setToApcu($key, $data, $ttl) {
        return apcu_store($key, json_encode($data), $ttl);
    }
    
    private function getFromFile($key) {
        $filename = $this->getCacheFilename($key);
        
        if (!file_exists($filename)) {
            return null;
        }
        
        // Check if expired
        $mtime = @filemtime($filename);
        if ($mtime && (time() - $mtime) > $this->historicalTtl) {
            @unlink($filename);
            return null;
        }
        
        $content = @file_get_contents($filename);
        if ($content === false) {
            return null;
        }
        
        $data = json_decode($content, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return null;
        }
        
        // Check embedded expiration time
        if (isset($data['_cache_expires']) && time() > $data['_cache_expires']) {
            @unlink($filename);
            return null;
        }
        
        // Remove cache metadata before returning
        unset($data['_cache_expires']);
        
        return $data;
    }
    
    private function setToFile($key, $data, $ttl) {
        $filename = $this->getCacheFilename($key);
        
        // Add expiration metadata
        $data['_cache_expires'] = time() + $ttl;
        
        $content = json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        
        // Write atomically using temp file
        $tempFile = $filename . '.tmp';
        $success = @file_put_contents($tempFile, $content, LOCK_EX);
        
        if ($success !== false) {
            return @rename($tempFile, $filename);
        }
        
        return false;
    }
    
    private function getCacheFilename($key) {
        // Sanitize key for filesystem
        $safeKey = preg_replace('/[^a-zA-Z0-9_-]/', '_', $key);
        return $this->cacheDir . '/' . $safeKey . '.cache';
    }
    
    /**
     * Get cache statistics
     */
    public function getStats() {
        $stats = [
            'type' => $this->useApcu ? 'apcu' : 'file',
            'cache_dir' => $this->cacheDir,
            'default_ttl' => $this->defaultTtl,
            'historical_ttl' => $this->historicalTtl
        ];
        
        if ($this->useApcu) {
            $info = apcu_cache_info();
            $stats['apcu_memory_size'] = $info['mem_size'] ?? 0;
            $stats['apcu_num_entries'] = $info['num_entries'] ?? 0;
        } else {
            $files = glob($this->cacheDir . '/*.cache');
            $stats['file_count'] = count($files);
            $stats['total_size'] = array_sum(array_map('filesize', $files));
        }
        
        return $stats;
    }
}

