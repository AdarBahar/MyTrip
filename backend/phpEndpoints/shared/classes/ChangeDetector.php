<?php
/**
 * Change Detector
 * 
 * Detects significant changes in location data to reduce unnecessary updates.
 * Uses distance, time, speed, and bearing thresholds.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

class ChangeDetector {
    private $distanceThreshold;  // meters
    private $timeThreshold;      // seconds
    private $speedThreshold;     // km/h
    private $bearingThreshold;   // degrees
    
    /**
     * Constructor
     * 
     * @param float $distanceThreshold Distance threshold in meters (default: 20)
     * @param int $timeThreshold Time threshold in seconds (default: 300 = 5 min)
     * @param float $speedThreshold Speed change threshold in km/h (default: 5)
     * @param float $bearingThreshold Bearing change threshold in degrees (default: 15)
     */
    public function __construct(
        $distanceThreshold = 20,
        $timeThreshold = 300,
        $speedThreshold = 5,
        $bearingThreshold = 15
    ) {
        $this->distanceThreshold = $distanceThreshold;
        $this->timeThreshold = $timeThreshold;
        $this->speedThreshold = $speedThreshold;
        $this->bearingThreshold = $bearingThreshold;
    }
    
    /**
     * Check if location should be emitted based on change detection
     * 
     * @param array $newLocation New location data
     * @param array|null $lastEmitted Last emitted location (null if first)
     * @return array ['should_emit' => bool, 'reason' => string, 'metrics' => array]
     */
    public function shouldEmit($newLocation, $lastEmitted = null) {
        // Always emit first location
        if (!$lastEmitted) {
            return [
                'should_emit' => true,
                'reason' => 'first',
                'metrics' => []
            ];
        }
        
        $metrics = [];
        
        // Calculate distance
        $distance = $this->haversineDistance(
            $lastEmitted['latitude'],
            $lastEmitted['longitude'],
            $newLocation['latitude'],
            $newLocation['longitude']
        );
        $metrics['distance_meters'] = round($distance, 2);
        
        if ($distance > $this->distanceThreshold) {
            return [
                'should_emit' => true,
                'reason' => 'distance',
                'metrics' => $metrics
            ];
        }
        
        // Calculate time difference
        $lastTime = $lastEmitted['client_time'] ?? $lastEmitted['timestamp'] ?? 0;
        $newTime = $newLocation['client_time'] ?? $newLocation['timestamp'] ?? 0;
        $timeDiff = abs($newTime - $lastTime) / 1000; // Convert ms to seconds
        $metrics['time_diff_seconds'] = round($timeDiff, 0);
        
        if ($timeDiff > $this->timeThreshold) {
            return [
                'should_emit' => true,
                'reason' => 'time',
                'metrics' => $metrics
            ];
        }
        
        // Calculate speed change
        $lastSpeed = $lastEmitted['speed'] ?? 0;
        $newSpeed = $newLocation['speed'] ?? 0;
        $speedChange = abs($newSpeed - $lastSpeed);
        $metrics['speed_change_kmh'] = round($speedChange, 2);
        
        if ($speedChange > $this->speedThreshold) {
            return [
                'should_emit' => true,
                'reason' => 'speed',
                'metrics' => $metrics
            ];
        }
        
        // Calculate bearing change
        if (isset($lastEmitted['bearing']) && isset($newLocation['bearing'])) {
            $bearingChange = $this->bearingDifference(
                $lastEmitted['bearing'],
                $newLocation['bearing']
            );
            $metrics['bearing_change_degrees'] = round($bearingChange, 2);
            
            if ($bearingChange > $this->bearingThreshold) {
                return [
                    'should_emit' => true,
                    'reason' => 'bearing',
                    'metrics' => $metrics
                ];
            }
        }
        
        // No significant change
        return [
            'should_emit' => false,
            'reason' => 'no_change',
            'metrics' => $metrics
        ];
    }
    
    /**
     * Calculate distance between two coordinates using Haversine formula
     * 
     * @param float $lat1 Latitude 1
     * @param float $lon1 Longitude 1
     * @param float $lat2 Latitude 2
     * @param float $lon2 Longitude 2
     * @return float Distance in meters
     */
    public function haversineDistance($lat1, $lon1, $lat2, $lon2) {
        $earthRadius = 6371000; // meters
        
        $lat1Rad = deg2rad($lat1);
        $lat2Rad = deg2rad($lat2);
        $deltaLat = deg2rad($lat2 - $lat1);
        $deltaLon = deg2rad($lon2 - $lon1);
        
        $a = sin($deltaLat / 2) * sin($deltaLat / 2) +
             cos($lat1Rad) * cos($lat2Rad) *
             sin($deltaLon / 2) * sin($deltaLon / 2);
        
        $c = 2 * atan2(sqrt($a), sqrt(1 - $a));
        
        return $earthRadius * $c;
    }
    
    /**
     * Calculate the smallest difference between two bearings
     * Handles wraparound (e.g., 350° to 10° = 20° difference, not 340°)
     * 
     * @param float $bearing1 Bearing 1 (0-360)
     * @param float $bearing2 Bearing 2 (0-360)
     * @return float Smallest difference in degrees
     */
    private function bearingDifference($bearing1, $bearing2) {
        $diff = abs($bearing2 - $bearing1);
        
        if ($diff > 180) {
            $diff = 360 - $diff;
        }
        
        return $diff;
    }
    
    /**
     * Get current thresholds
     * 
     * @return array Threshold configuration
     */
    public function getThresholds() {
        return [
            'distance_meters' => $this->distanceThreshold,
            'time_seconds' => $this->timeThreshold,
            'speed_kmh' => $this->speedThreshold,
            'bearing_degrees' => $this->bearingThreshold
        ];
    }
    
    /**
     * Update thresholds
     * 
     * @param array $thresholds New threshold values
     */
    public function setThresholds($thresholds) {
        if (isset($thresholds['distance_meters'])) {
            $this->distanceThreshold = $thresholds['distance_meters'];
        }
        if (isset($thresholds['time_seconds'])) {
            $this->timeThreshold = $thresholds['time_seconds'];
        }
        if (isset($thresholds['speed_kmh'])) {
            $this->speedThreshold = $thresholds['speed_kmh'];
        }
        if (isset($thresholds['bearing_degrees'])) {
            $this->bearingThreshold = $thresholds['bearing_degrees'];
        }
    }
}

