<?php
/**
 * Location Analyzer
 * 
 * Analyzes location data to detect dwells, drives, and simplify routes.
 * Provides analytics for location history.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/ChangeDetector.php';

class LocationAnalyzer {
    private $changeDetector;
    private $dwellRadiusMeters;
    private $dwellMinDurationSeconds;
    
    /**
     * Constructor
     * 
     * @param float $dwellRadiusMeters Radius for dwell detection (default: 50m)
     * @param int $dwellMinDurationSeconds Minimum duration for dwell (default: 300s = 5min)
     */
    public function __construct($dwellRadiusMeters = 50, $dwellMinDurationSeconds = 300) {
        $this->changeDetector = new ChangeDetector();
        $this->dwellRadiusMeters = $dwellRadiusMeters;
        $this->dwellMinDurationSeconds = $dwellMinDurationSeconds;
    }
    
    /**
     * Detect dwell periods in location history
     * 
     * @param array $locations Array of location points (sorted by time)
     * @return array Array of dwell periods
     */
    public function detectDwells($locations) {
        if (empty($locations)) {
            return [];
        }
        
        $dwells = [];
        $currentDwell = null;
        
        foreach ($locations as $loc) {
            if (!$currentDwell) {
                // Start new dwell
                $currentDwell = [
                    'center' => $loc,
                    'start_time' => $this->getTimestamp($loc),
                    'points' => [$loc],
                    'lat_sum' => $loc['latitude'],
                    'lon_sum' => $loc['longitude']
                ];
                continue;
            }
            
            // Calculate distance from dwell center
            $distance = $this->changeDetector->haversineDistance(
                $currentDwell['center']['latitude'],
                $currentDwell['center']['longitude'],
                $loc['latitude'],
                $loc['longitude']
            );
            
            if ($distance <= $this->dwellRadiusMeters) {
                // Still in dwell area
                $currentDwell['points'][] = $loc;
                $currentDwell['end_time'] = $this->getTimestamp($loc);
                $currentDwell['lat_sum'] += $loc['latitude'];
                $currentDwell['lon_sum'] += $loc['longitude'];
            } else {
                // Left dwell area - finalize current dwell
                $duration = ($currentDwell['end_time'] ?? $currentDwell['start_time']) - $currentDwell['start_time'];
                
                if ($duration >= $this->dwellMinDurationSeconds * 1000) { // Convert to ms
                    $dwells[] = $this->finalizeDwell($currentDwell);
                }
                
                // Start new dwell
                $currentDwell = [
                    'center' => $loc,
                    'start_time' => $this->getTimestamp($loc),
                    'points' => [$loc],
                    'lat_sum' => $loc['latitude'],
                    'lon_sum' => $loc['longitude']
                ];
            }
        }
        
        // Finalize last dwell if it meets duration requirement
        if ($currentDwell) {
            $duration = ($currentDwell['end_time'] ?? $currentDwell['start_time']) - $currentDwell['start_time'];
            if ($duration >= $this->dwellMinDurationSeconds * 1000) {
                $dwells[] = $this->finalizeDwell($currentDwell);
            }
        }
        
        return $dwells;
    }
    
    /**
     * Segment drives from location history
     * 
     * @param array $locations Array of location points (sorted by time)
     * @param array $dwells Array of detected dwells
     * @return array Array of drive segments
     */
    public function segmentDrives($locations, $dwells) {
        if (empty($locations)) {
            return [];
        }
        
        $drives = [];
        $currentDrive = null;
        
        foreach ($locations as $loc) {
            $timestamp = $this->getTimestamp($loc);
            $inDwell = false;
            
            // Check if location is within any dwell period
            foreach ($dwells as $dwell) {
                if ($timestamp >= $dwell['start_time'] && $timestamp <= $dwell['end_time']) {
                    $inDwell = true;
                    break;
                }
            }
            
            if (!$inDwell) {
                // In drive mode
                if (!$currentDrive) {
                    $currentDrive = [
                        'points' => [],
                        'start_time' => $timestamp
                    ];
                }
                $currentDrive['points'][] = $loc;
                $currentDrive['end_time'] = $timestamp;
            } else {
                // In dwell - finalize current drive if exists
                if ($currentDrive && count($currentDrive['points']) > 1) {
                    $drives[] = $this->finalizeDrive($currentDrive);
                }
                $currentDrive = null;
            }
        }
        
        // Finalize last drive
        if ($currentDrive && count($currentDrive['points']) > 1) {
            $drives[] = $this->finalizeDrive($currentDrive);
        }
        
        return $drives;
    }
    
    /**
     * Simplify route using Ramer-Douglas-Peucker algorithm
     * 
     * @param array $points Array of location points
     * @param float $epsilon Tolerance in meters (default: 10m)
     * @return array Simplified points
     */
    public function simplifyRoute($points, $epsilon = 10) {
        if (count($points) < 3) {
            return $points;
        }
        
        return $this->rdpSimplify($points, $epsilon);
    }
    
    /**
     * Finalize dwell period with calculated metrics
     * 
     * @param array $dwell Dwell data
     * @return array Finalized dwell
     */
    private function finalizeDwell($dwell) {
        $pointCount = count($dwell['points']);
        
        // Calculate average center
        $centerLat = $dwell['lat_sum'] / $pointCount;
        $centerLon = $dwell['lon_sum'] / $pointCount;
        
        $duration = ($dwell['end_time'] ?? $dwell['start_time']) - $dwell['start_time'];
        
        return [
            'center' => [
                'latitude' => round($centerLat, 6),
                'longitude' => round($centerLon, 6)
            ],
            'start_time' => $dwell['start_time'],
            'end_time' => $dwell['end_time'] ?? $dwell['start_time'],
            'duration_seconds' => round($duration / 1000, 0),
            'point_count' => $pointCount,
            'radius_meters' => $this->dwellRadiusMeters
        ];
    }
    
    /**
     * Finalize drive segment with calculated metrics
     * 
     * @param array $drive Drive data
     * @return array Finalized drive
     */
    private function finalizeDrive($drive) {
        $points = $drive['points'];
        $pointCount = count($points);
        
        // Calculate total distance
        $totalDistance = 0;
        for ($i = 1; $i < $pointCount; $i++) {
            $totalDistance += $this->changeDetector->haversineDistance(
                $points[$i-1]['latitude'],
                $points[$i-1]['longitude'],
                $points[$i]['latitude'],
                $points[$i]['longitude']
            );
        }
        
        // Calculate duration
        $duration = $drive['end_time'] - $drive['start_time'];
        $durationHours = $duration / 1000 / 3600;
        
        // Calculate average speed
        $avgSpeed = $durationHours > 0 ? ($totalDistance / 1000) / $durationHours : 0;
        
        // Simplify route
        $simplifiedPoints = $this->simplifyRoute($points, 10);
        
        return [
            'start_time' => $drive['start_time'],
            'end_time' => $drive['end_time'],
            'duration_seconds' => round($duration / 1000, 0),
            'distance_meters' => round($totalDistance, 2),
            'avg_speed_kmh' => round($avgSpeed, 2),
            'point_count' => $pointCount,
            'simplified_point_count' => count($simplifiedPoints),
            'simplified_points' => array_map(function($p) {
                return [
                    'latitude' => (float)$p['latitude'],
                    'longitude' => (float)$p['longitude'],
                    'timestamp' => $this->getTimestamp($p)
                ];
            }, $simplifiedPoints)
        ];
    }
    
    /**
     * Ramer-Douglas-Peucker algorithm implementation
     * 
     * @param array $points Points to simplify
     * @param float $epsilon Tolerance in meters
     * @return array Simplified points
     */
    private function rdpSimplify($points, $epsilon) {
        if (count($points) < 3) {
            return $points;
        }
        
        // Find point with maximum distance from line
        $maxDistance = 0;
        $maxIndex = 0;
        $end = count($points) - 1;
        
        for ($i = 1; $i < $end; $i++) {
            $distance = $this->perpendicularDistance(
                $points[$i],
                $points[0],
                $points[$end]
            );
            
            if ($distance > $maxDistance) {
                $maxDistance = $distance;
                $maxIndex = $i;
            }
        }
        
        // If max distance is greater than epsilon, recursively simplify
        if ($maxDistance > $epsilon) {
            // Recursive call
            $left = $this->rdpSimplify(array_slice($points, 0, $maxIndex + 1), $epsilon);
            $right = $this->rdpSimplify(array_slice($points, $maxIndex), $epsilon);
            
            // Merge results
            array_pop($left); // Remove duplicate point
            return array_merge($left, $right);
        } else {
            // All points between start and end can be removed
            return [$points[0], $points[$end]];
        }
    }
    
    /**
     * Calculate perpendicular distance from point to line
     * 
     * @param array $point Point to measure
     * @param array $lineStart Line start point
     * @param array $lineEnd Line end point
     * @return float Distance in meters
     */
    private function perpendicularDistance($point, $lineStart, $lineEnd) {
        // Simplified approximation using Haversine for small distances
        // For more accuracy, use proper geodesic calculations
        
        $lat = $point['latitude'];
        $lon = $point['longitude'];
        $lat1 = $lineStart['latitude'];
        $lon1 = $lineStart['longitude'];
        $lat2 = $lineEnd['latitude'];
        $lon2 = $lineEnd['longitude'];
        
        // If line start and end are the same, return distance to that point
        if ($lat1 === $lat2 && $lon1 === $lon2) {
            return $this->changeDetector->haversineDistance($lat, $lon, $lat1, $lon1);
        }
        
        // Calculate perpendicular distance (approximation)
        $distToStart = $this->changeDetector->haversineDistance($lat, $lon, $lat1, $lon1);
        $distToEnd = $this->changeDetector->haversineDistance($lat, $lon, $lat2, $lon2);
        $lineLength = $this->changeDetector->haversineDistance($lat1, $lon1, $lat2, $lon2);
        
        // Use Heron's formula for triangle area, then calculate height
        $s = ($distToStart + $distToEnd + $lineLength) / 2;
        $area = sqrt(max(0, $s * ($s - $distToStart) * ($s - $distToEnd) * ($s - $lineLength)));
        
        return $lineLength > 0 ? (2 * $area / $lineLength) : $distToStart;
    }
    
    /**
     * Get timestamp from location (handles different formats)
     * 
     * @param array $loc Location data
     * @return int Timestamp in milliseconds
     */
    private function getTimestamp($loc) {
        return $loc['recorded_at'] ?? $loc['client_time'] ?? $loc['timestamp'] ?? 0;
    }
}

