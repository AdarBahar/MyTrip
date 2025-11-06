<?php
/**
 * Dwell Session Manager
 * 
 * Handles advanced dwell calculation and storage with spatial optimization
 * Implements incremental processing and quality-based filtering
 * 
 * @version 1.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/../db-config.php';

class DwellSessionManager {
    private $pdo;
    private $maxGapMs = 3600000; // 1 hour
    private $minDwellSeconds = 60; // 1 minute
    private $maxAccuracyThreshold = 100; // 100 meters
    private $maxSpeedKmh = 5; // 5 km/h
    private $mergeGapMs = 300000; // 5 minutes
    
    public function __construct() {
        $this->pdo = DatabaseConfig::getInstance()->getConnection();
    }
    
    /**
     * Process new location points for a device and create/update dwell sessions
     */
    public function processLocationPoints($deviceId, $fromTime = null, $toTime = null) {
        try {
            // Get processing state
            $state = $this->getProcessingState($deviceId);
            
            if ($fromTime === null) {
                $fromTime = $state['last_processed_time'] ?? 0;
            }
            
            if ($toTime === null) {
                $toTime = time() * 1000; // Current time in milliseconds
            }
            
            // Get new points to process
            $points = $this->getLocationPoints($deviceId, $fromTime, $toTime);
            
            if (empty($points)) {
                return ['processed' => 0, 'sessions_created' => 0];
            }
            
            // Calculate dwell sessions
            $sessions = $this->calculateDwellSessions($points, $state);
            
            // Store sessions in database
            $sessionsCreated = 0;
            foreach ($sessions as $session) {
                if ($this->storeDwellSession($session)) {
                    $sessionsCreated++;
                    $this->updateDailyRollup($session);
                }
            }
            
            // Update processing state
            $this->updateProcessingState($deviceId, $toTime, $sessions);
            
            return [
                'processed' => count($points),
                'sessions_created' => $sessionsCreated,
                'last_processed_time' => $toTime
            ];
            
        } catch (Exception $e) {
            error_log("Error processing dwell sessions for device $deviceId: " . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Get location points for processing with quality filters
     */
    private function getLocationPoints($deviceId, $fromTime, $toTime) {
        $sql = "
            SELECT id, device_id, user_id, latitude, longitude, client_time, 
                   accuracy, speed, battery_level,
                   CONCAT('g_', 
                          FLOOR(latitude / 0.00135), '_',
                          FLOOR(longitude / (0.00135 / COS(RADIANS(latitude)))))
                   AS cluster_id
            FROM location_records 
            WHERE device_id = ? 
              AND client_time > ? 
              AND client_time <= ?
              AND (accuracy IS NULL OR accuracy <= ?)
            ORDER BY client_time
        ";
        
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$deviceId, $fromTime, $toTime, $this->maxAccuracyThreshold]);
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    /**
     * Calculate dwell sessions from location points
     */
    private function calculateDwellSessions($points, $state) {
        $sessions = [];
        $currentSession = null;
        
        // Resume current session if exists
        if (!empty($state['current_session_id'])) {
            $currentSession = $this->getDwellSession($state['current_session_id']);
        }
        
        foreach ($points as $point) {
            // Quality filters
            if ($this->shouldSkipPoint($point)) {
                continue;
            }
            
            $clusterId = $point['cluster_id'];
            $pointTime = intval($point['client_time']);
            
            // Determine if we should start a new session
            $shouldStartNew = false;
            
            if ($currentSession === null) {
                $shouldStartNew = true;
            } else {
                $timeDiff = $pointTime - $currentSession['last_time'];
                $clusterChanged = $currentSession['cluster_id'] !== $clusterId;
                
                if ($timeDiff > $this->maxGapMs || $clusterChanged) {
                    // Close current session if it meets minimum duration
                    if ($currentSession['duration_ms'] >= $this->minDwellSeconds * 1000) {
                        $sessions[] = $this->finalizeDwellSession($currentSession);
                    }
                    $shouldStartNew = true;
                }
            }
            
            if ($shouldStartNew) {
                $currentSession = $this->createNewDwellSession($point);
            } else {
                $this->extendDwellSession($currentSession, $point);
            }
        }
        
        // Handle final session
        if ($currentSession !== null && $currentSession['duration_ms'] >= $this->minDwellSeconds * 1000) {
            $sessions[] = $this->finalizeDwellSession($currentSession);
        }
        
        return $this->mergeAdjacentSessions($sessions);
    }
    
    /**
     * Check if point should be skipped based on quality filters
     */
    private function shouldSkipPoint($point) {
        // Skip if accuracy is too poor
        if (isset($point['accuracy']) && $point['accuracy'] > $this->maxAccuracyThreshold) {
            return true;
        }
        
        // Skip if moving too fast (not dwelling)
        if (isset($point['speed']) && $point['speed'] * 3.6 > $this->maxSpeedKmh) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Create new dwell session
     */
    private function createNewDwellSession($point) {
        return [
            'device_id' => $point['device_id'],
            'user_id' => $point['user_id'],
            'cluster_id' => $point['cluster_id'],
            'start_time' => intval($point['client_time']),
            'last_time' => intval($point['client_time']),
            'duration_ms' => 0,
            'points_count' => 1,
            'centroid_lat' => floatval($point['latitude']),
            'centroid_lon' => floatval($point['longitude']),
            'accuracy_sum' => isset($point['accuracy']) ? floatval($point['accuracy']) : 0,
            'accuracy_count' => isset($point['accuracy']) ? 1 : 0,
            'max_gap_ms' => 0,
            'points' => [$point]
        ];
    }
    
    /**
     * Extend existing dwell session with new point
     */
    private function extendDwellSession(&$session, $point) {
        $timeDiff = intval($point['client_time']) - $session['last_time'];
        
        // Only add time if gap is reasonable
        if ($timeDiff <= $this->maxGapMs) {
            $session['duration_ms'] += $timeDiff;
            $session['max_gap_ms'] = max($session['max_gap_ms'], $timeDiff);
        }
        
        $session['last_time'] = intval($point['client_time']);
        $session['points_count']++;
        $session['points'][] = $point;
        
        // Update centroid (weighted average)
        $session['centroid_lat'] = (($session['centroid_lat'] * ($session['points_count'] - 1)) + 
                                   floatval($point['latitude'])) / $session['points_count'];
        $session['centroid_lon'] = (($session['centroid_lon'] * ($session['points_count'] - 1)) + 
                                   floatval($point['longitude'])) / $session['points_count'];
        
        // Update accuracy stats
        if (isset($point['accuracy'])) {
            $session['accuracy_sum'] += floatval($point['accuracy']);
            $session['accuracy_count']++;
        }
    }
    
    /**
     * Finalize dwell session for storage
     */
    private function finalizeDwellSession($session) {
        $session['end_time'] = $session['start_time'] + $session['duration_ms'];
        $session['duration_s'] = intval($session['duration_ms'] / 1000);
        $session['accuracy_avg'] = $session['accuracy_count'] > 0 ? 
                                  $session['accuracy_sum'] / $session['accuracy_count'] : null;
        $session['confidence_score'] = $this->calculateConfidenceScore($session);
        
        return $session;
    }
    
    /**
     * Calculate confidence score for dwell session
     */
    private function calculateConfidenceScore($session) {
        $score = 100;
        
        // Reduce score based on average accuracy
        if ($session['accuracy_count'] > 0) {
            $avgAccuracy = $session['accuracy_sum'] / $session['accuracy_count'];
            if ($avgAccuracy > 50) {
                $score -= min(30, ($avgAccuracy - 50) / 2);
            }
        }
        
        // Reduce score if too few points for the duration
        $pointsPerMinute = $session['points_count'] / ($session['duration_ms'] / 60000);
        if ($pointsPerMinute < 0.5) {
            $score -= 20;
        }
        
        // Reduce score for large gaps
        if ($session['max_gap_ms'] > 30 * 60 * 1000) {
            $score -= 15;
        }
        
        // Boost score for longer dwells
        if ($session['duration_ms'] > 30 * 60 * 1000) {
            $score += 10;
        }
        
        return max(0, min(100, intval($score)));
    }
    
    /**
     * Store dwell session in database
     */
    private function storeDwellSession($session) {
        $sql = "
            INSERT INTO dwell_sessions (
                device_id, user_id, cluster_id, centroid_lat, centroid_lon,
                start_time, end_time, duration_s, points_count, max_gap_ms,
                accuracy_avg, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ";
        
        $stmt = $this->pdo->prepare($sql);
        return $stmt->execute([
            $session['device_id'],
            $session['user_id'],
            $session['cluster_id'],
            $session['centroid_lat'],
            $session['centroid_lon'],
            $session['start_time'],
            $session['end_time'],
            $session['duration_s'],
            $session['points_count'],
            $session['max_gap_ms'],
            $session['accuracy_avg'],
            $session['confidence_score']
        ]);
    }

    /**
     * Update daily rollup table
     */
    private function updateDailyRollup($session) {
        $day = date('Y-m-d', $session['start_time'] / 1000);

        $sql = "
            INSERT INTO dwell_daily (
                device_id, user_id, day, cluster_id, centroid_lat, centroid_lon,
                total_dwell_s, visits, avg_confidence, first_visit_time, last_visit_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                total_dwell_s = total_dwell_s + VALUES(total_dwell_s),
                visits = visits + 1,
                avg_confidence = (avg_confidence * (visits - 1) + VALUES(avg_confidence)) / visits,
                first_visit_time = LEAST(first_visit_time, VALUES(first_visit_time)),
                last_visit_time = GREATEST(last_visit_time, VALUES(last_visit_time))
        ";

        $stmt = $this->pdo->prepare($sql);
        return $stmt->execute([
            $session['device_id'],
            $session['user_id'],
            $day,
            $session['cluster_id'],
            $session['centroid_lat'],
            $session['centroid_lon'],
            $session['duration_s'],
            $session['confidence_score'],
            $session['start_time'],
            $session['end_time']
        ]);
    }

    /**
     * Merge adjacent sessions if user left briefly and returned
     */
    private function mergeAdjacentSessions($sessions) {
        if (count($sessions) < 2) return $sessions;

        $merged = [];
        $current = $sessions[0];

        for ($i = 1; $i < count($sessions); $i++) {
            $next = $sessions[$i];

            // Check if sessions are adjacent in time and space
            $timeBetween = $next['start_time'] - $current['end_time'];
            $distance = $this->haversineDistance(
                $current['centroid_lat'], $current['centroid_lon'],
                $next['centroid_lat'], $next['centroid_lon']
            );

            // Merge if gap is small and locations are close
            if ($timeBetween <= $this->mergeGapMs && $distance <= 30) { // 30m radius
                // Merge sessions
                $totalPoints = $current['points_count'] + $next['points_count'];
                $current['duration_ms'] += $timeBetween + $next['duration_ms'];
                $current['duration_s'] = intval($current['duration_ms'] / 1000);
                $current['end_time'] = $next['end_time'];
                $current['points_count'] = $totalPoints;
                $current['max_gap_ms'] = max($current['max_gap_ms'], $timeBetween, $next['max_gap_ms']);

                // Recalculate centroid
                $current['centroid_lat'] = (($current['centroid_lat'] * $current['points_count']) +
                                           ($next['centroid_lat'] * $next['points_count'])) / $totalPoints;
                $current['centroid_lon'] = (($current['centroid_lon'] * $current['points_count']) +
                                           ($next['centroid_lon'] * $next['points_count'])) / $totalPoints;

                // Merge accuracy stats
                $current['accuracy_sum'] += $next['accuracy_sum'];
                $current['accuracy_count'] += $next['accuracy_count'];
                $current['accuracy_avg'] = $current['accuracy_count'] > 0 ?
                                          $current['accuracy_sum'] / $current['accuracy_count'] : null;

                // Recalculate confidence
                $current['confidence_score'] = $this->calculateConfidenceScore($current);
            } else {
                // Don't merge - add current to results and move to next
                $merged[] = $current;
                $current = $next;
            }
        }

        // Add final session
        $merged[] = $current;

        return $merged;
    }

    /**
     * Get processing state for a device
     */
    private function getProcessingState($deviceId) {
        $sql = "SELECT * FROM dwell_processing_state WHERE device_id = ?";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$deviceId]);

        $state = $stmt->fetch(PDO::FETCH_ASSOC);
        return $state ?: [
            'device_id' => $deviceId,
            'last_processed_time' => 0,
            'last_cluster_id' => null,
            'current_session_id' => null
        ];
    }

    /**
     * Update processing state
     */
    private function updateProcessingState($deviceId, $lastProcessedTime, $sessions) {
        $lastClusterId = null;
        $currentSessionId = null;

        if (!empty($sessions)) {
            $lastSession = end($sessions);
            $lastClusterId = $lastSession['cluster_id'];
            // If session is ongoing, we might want to track it
        }

        $sql = "
            INSERT INTO dwell_processing_state (
                device_id, last_processed_time, last_cluster_id, current_session_id
            ) VALUES (?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                last_processed_time = VALUES(last_processed_time),
                last_cluster_id = VALUES(last_cluster_id),
                current_session_id = VALUES(current_session_id)
        ";

        $stmt = $this->pdo->prepare($sql);
        return $stmt->execute([$deviceId, $lastProcessedTime, $lastClusterId, $currentSessionId]);
    }

    /**
     * Get dwell session by ID
     */
    private function getDwellSession($sessionId) {
        $sql = "SELECT * FROM dwell_sessions WHERE id = ?";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$sessionId]);

        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    /**
     * Calculate distance between two points using Haversine formula
     */
    private function haversineDistance($lat1, $lon1, $lat2, $lon2) {
        $R = 6371000; // Earth's radius in meters
        $dLat = deg2rad($lat2 - $lat1);
        $dLon = deg2rad($lon2 - $lon1);
        $a = sin($dLat/2) * sin($dLat/2) + cos(deg2rad($lat1)) * cos(deg2rad($lat2)) * sin($dLon/2) * sin($dLon/2);
        return 2 * $R * atan2(sqrt($a), sqrt(1 - $a));
    }

    /**
     * Get dwell sessions for display (with caching support)
     */
    public function getDwellSessionsForDisplay($deviceId, $fromTime = null, $toTime = null, $useCache = true) {
        // If using cache and sessions exist, return from database
        if ($useCache) {
            $sql = "
                SELECT * FROM dwell_sessions
                WHERE device_id = ?
                AND (? IS NULL OR start_time >= ?)
                AND (? IS NULL OR end_time <= ?)
                ORDER BY start_time
            ";

            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$deviceId, $fromTime, $fromTime, $toTime, $toTime]);

            $sessions = $stmt->fetchAll(PDO::FETCH_ASSOC);

            if (!empty($sessions)) {
                return $this->convertDbSessionsToDisplayFormat($sessions);
            }
        }

        // Fallback to real-time calculation
        return null;
    }

    /**
     * Convert database sessions to display format
     */
    private function convertDbSessionsToDisplayFormat($dbSessions) {
        $markers = [];

        foreach ($dbSessions as $session) {
            $markers[] = [
                'lat' => floatval($session['centroid_lat']),
                'lon' => floatval($session['centroid_lon']),
                'count' => intval($session['points_count']),
                'dwell_s' => intval($session['duration_s']),
                'first_t' => intval($session['start_time']),
                'last_t' => intval($session['end_time']),
                'avg_acc' => $session['accuracy_avg'] ? floatval($session['accuracy_avg']) : null,
                'points' => [], // Points not stored in sessions table
                'has_anomalies' => false, // Would need to check separately
                'anomaly_reasons' => [],
                'is_marked_anomaly' => false,
                'cluster_id' => $session['cluster_id'],
                'max_gap_ms' => intval($session['max_gap_ms']),
                'confidence_score' => intval($session['confidence_score'])
            ];
        }

        return $markers;
    }
}
