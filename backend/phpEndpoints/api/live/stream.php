<?php
/**
 * Live Tracking - Streaming Endpoint (Polling-based)
 * 
 * GET /api/live/stream.php
 * 
 * Returns new location updates since a given cursor (timestamp).
 * Supports single user, multiple users, or all users.
 * Designed for efficient polling (every 3-5 seconds).
 * 
 * Query Parameters:
 * - user: Single username or comma-separated list
 * - users[]: Array of usernames
 * - device: Single device ID or comma-separated list
 * - devices[]: Array of device IDs
 * - all: Stream all users (default: false)
 * - since: Cursor timestamp in milliseconds (default: 0)
 * - limit: Maximum records to return (default: 100, max: 500)
 * - session_id: Optional session tracking ID
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Include required files
require_once __DIR__ . '/../../shared/logging.php';
require_once __DIR__ . '/../../shared/classes/ApiResponse.php';
require_once __DIR__ . '/../../db-config.php';
require_once __DIR__ . '/../middleware/authentication.php';

// Generate unique request ID
$requestId = uniqid('live_stream_', true);
$GLOBALS['requestId'] = $requestId;

// Set CORS headers
ApiResponse::setCorsHeaders();

// Handle OPTIONS request
ApiResponse::handleOptionsRequest(['GET', 'OPTIONS']);

// Only allow GET
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    ApiResponse::methodNotAllowed(['GET']);
}

// Authenticate request
if (!authenticateRequest()) {
    ApiResponse::unauthorized('Valid API token required');
}

// Rate limiting - very permissive for streaming (polling every 3 seconds)
if (!checkRateLimit($_SERVER['REMOTE_ADDR'] ?? 'unknown', 3000)) {
    ApiResponse::rateLimitExceeded('Rate limit exceeded. Maximum 3000 requests per hour.');
}

try {
    // Check if database mode is enabled
    if (!DatabaseConfig::isDatabaseMode()) {
        ApiResponse::error('Database mode is not enabled. This endpoint requires database mode.', 503);
    }
    
    // Get database connection
    $db = DatabaseConfig::getInstance();
    if (!$db->testConnection() || !$db->tablesExist()) {
        ApiResponse::error('Database is not available', 503);
    }
    
    $pdo = $db->getConnection();
    
    // Parse query parameters
    $since = isset($_GET['since']) ? (int)$_GET['since'] : 0;
    $limit = isset($_GET['limit']) ? min((int)$_GET['limit'], 500) : 100;
    $sessionId = $_GET['session_id'] ?? null;
    $getAll = filter_var($_GET['all'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    
    // Parse user filters
    $usernames = [];
    if (isset($_GET['user'])) {
        $usernames = array_map('trim', explode(',', $_GET['user']));
    } elseif (isset($_GET['users']) && is_array($_GET['users'])) {
        $usernames = array_map('trim', $_GET['users']);
    }
    
    // Parse device filters
    $deviceIds = [];
    if (isset($_GET['device'])) {
        $deviceIds = array_map('trim', explode(',', $_GET['device']));
    } elseif (isset($_GET['devices']) && is_array($_GET['devices'])) {
        $deviceIds = array_map('trim', $_GET['devices']);
    }
    
    // Validate: must have at least one filter unless 'all' is specified
    if (empty($usernames) && empty($deviceIds) && !$getAll) {
        ApiResponse::error('Must specify user, users[], device, devices[], or all=true', 400);
    }
    
    // Track session if provided
    if ($sessionId) {
        try {
            $stmt = $pdo->prepare("
                INSERT INTO streaming_sessions (
                    session_id, user_id, device_id, last_cursor,
                    ip_address, user_agent, expires_at
                ) VALUES (
                    :session_id, 0, :device_id, :cursor,
                    :ip, :user_agent, DATE_ADD(NOW(), INTERVAL 1 HOUR)
                )
                ON DUPLICATE KEY UPDATE
                    last_cursor = VALUES(last_cursor),
                    last_poll_at = NOW(),
                    expires_at = DATE_ADD(NOW(), INTERVAL 1 HOUR)
            ");
            
            $stmt->execute([
                ':session_id' => $sessionId,
                ':device_id' => !empty($deviceIds) ? $deviceIds[0] : null,
                ':cursor' => $since,
                ':ip' => $_SERVER['REMOTE_ADDR'] ?? null,
                ':user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? null
            ]);
        } catch (Exception $e) {
            // Session tracking is optional, don't fail on error
            error_log("Session tracking failed: " . $e->getMessage());
        }
    }
    
    // Build query for location_history_cache
    $sql = "
        SELECT 
            lhc.device_id,
            lhc.user_id,
            u.username,
            u.display_name,
            lhc.latitude,
            lhc.longitude,
            lhc.accuracy,
            lhc.altitude,
            lhc.speed,
            lhc.bearing,
            lhc.battery_level,
            lhc.recorded_at,
            lhc.server_time,
            UNIX_TIMESTAMP(lhc.server_time) * 1000 as server_timestamp
        FROM location_history_cache lhc
        JOIN users u ON lhc.user_id = u.id
        WHERE UNIX_TIMESTAMP(lhc.server_time) * 1000 > :since
    ";
    
    $params = [':since' => $since];
    
    // Apply user filter
    if (!empty($usernames) && !$getAll) {
        $placeholders = [];
        foreach ($usernames as $i => $username) {
            $key = ":username_$i";
            $placeholders[] = $key;
            $params[$key] = $username;
        }
        $sql .= " AND u.username IN (" . implode(',', $placeholders) . ")";
    }
    
    // Apply device filter
    if (!empty($deviceIds)) {
        $placeholders = [];
        foreach ($deviceIds as $i => $deviceId) {
            $key = ":device_$i";
            $placeholders[] = $key;
            $params[$key] = $deviceId;
        }
        $sql .= " AND lhc.device_id IN (" . implode(',', $placeholders) . ")";
    }
    
    $sql .= " ORDER BY lhc.server_time ASC LIMIT :limit";
    $params[':limit'] = $limit;
    
    // Execute query
    $stmt = $pdo->prepare($sql);
    
    // Bind limit separately (PDO quirk)
    foreach ($params as $key => $value) {
        if ($key === ':limit') {
            $stmt->bindValue($key, $value, PDO::PARAM_INT);
        } else {
            $stmt->bindValue($key, $value);
        }
    }
    
    $stmt->execute();
    $points = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Calculate new cursor
    $newCursor = $since;
    $hasMore = false;
    
    if (!empty($points)) {
        $lastPoint = end($points);
        $newCursor = (int)$lastPoint['server_timestamp'];
        
        // Check if there are more points
        if (count($points) >= $limit) {
            $hasMore = true;
        }
    }
    
    // Format response
    $formattedPoints = [];
    foreach ($points as $point) {
        $formattedPoints[] = [
            'device_id' => $point['device_id'],
            'user_id' => (int)$point['user_id'],
            'username' => $point['username'],
            'display_name' => $point['display_name'],
            'latitude' => (float)$point['latitude'],
            'longitude' => (float)$point['longitude'],
            'accuracy' => $point['accuracy'] !== null ? (float)$point['accuracy'] : null,
            'altitude' => $point['altitude'] !== null ? (float)$point['altitude'] : null,
            'speed' => $point['speed'] !== null ? (float)$point['speed'] : null,
            'bearing' => $point['bearing'] !== null ? (float)$point['bearing'] : null,
            'battery_level' => $point['battery_level'] !== null ? (int)$point['battery_level'] : null,
            'recorded_at' => $point['recorded_at'],
            'server_time' => $point['server_time'],
            'server_timestamp' => (int)$point['server_timestamp']
        ];
    }
    
    // Generate ETag for caching
    $etag = md5(json_encode($formattedPoints));
    $clientEtag = $_SERVER['HTTP_IF_NONE_MATCH'] ?? null;
    
    // If content hasn't changed and no new points, return 304
    if ($clientEtag === $etag && count($formattedPoints) === 0) {
        http_response_code(304);
        header("ETag: $etag");
        exit;
    }
    
    // Set caching headers
    header("ETag: $etag");
    header("Cache-Control: private, max-age=2"); // Cache for 2 seconds
    
    // Return response
    ApiResponse::success([
        'points' => $formattedPoints,
        'cursor' => $newCursor,
        'has_more' => $hasMore,
        'count' => count($formattedPoints),
        'session_id' => $sessionId,
        'filters' => [
            'usernames' => $usernames,
            'device_ids' => $deviceIds,
            'all' => $getAll,
            'since' => $since
        ],
        'timestamp' => gmdate('Y-m-d\TH:i:s\Z')
    ], 'Location stream retrieved successfully');
    
} catch (PDOException $e) {
    error_log("Database error in live/stream.php: " . $e->getMessage());
    ApiResponse::error('Database query failed', 500);
} catch (Exception $e) {
    error_log("Error in live/stream.php: " . $e->getMessage());
    ApiResponse::error('Failed to retrieve location stream: ' . $e->getMessage(), 500);
}

