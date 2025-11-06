<?php
/**
 * Live Tracking - History Endpoint
 * 
 * GET /api/live/history.php
 * 
 * Returns recent tracking history from the cache table.
 * Useful for "replay" functionality or showing recent path.
 * 
 * Query Parameters:
 * - user: Single username or comma-separated list
 * - users[]: Array of usernames
 * - device: Single device ID or comma-separated list
 * - devices[]: Array of device IDs
 * - all: Get history for all users (default: false)
 * - duration: Time window in seconds (default: 3600 = 1 hour, max: 86400 = 24 hours)
 * - limit: Maximum records to return (default: 500, max: 5000)
 * - offset: Pagination offset (default: 0)
 * - segments: Include dwell/drive segment analysis (default: false)
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Include required files
require_once __DIR__ . '/../../shared/logging.php';
require_once __DIR__ . '/../../shared/classes/ApiResponse.php';
require_once __DIR__ . '/../../shared/classes/LocationAnalyzer.php';
require_once __DIR__ . '/../../db-config.php';
require_once __DIR__ . '/../middleware/authentication.php';

// Generate unique request ID
$requestId = uniqid('live_history_', true);
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

// Rate limiting
if (!checkRateLimit($_SERVER['REMOTE_ADDR'] ?? 'unknown', 1000)) {
    ApiResponse::rateLimitExceeded('Rate limit exceeded. Maximum 1000 requests per hour.');
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
    $duration = isset($_GET['duration']) ? min((int)$_GET['duration'], 86400) : 3600; // Max 24 hours
    $limit = isset($_GET['limit']) ? min((int)$_GET['limit'], 5000) : 500;
    $offset = isset($_GET['offset']) ? (int)$_GET['offset'] : 0;
    $getAll = filter_var($_GET['all'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    $includeSegments = filter_var($_GET['segments'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    
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
        WHERE lhc.server_time >= DATE_SUB(NOW(), INTERVAL :duration SECOND)
    ";
    
    $params = [':duration' => $duration];
    
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
    
    // Get total count for pagination
    $countSql = "SELECT COUNT(*) as total FROM (" . $sql . ") as subquery";
    $countStmt = $pdo->prepare($countSql);
    $countStmt->execute($params);
    $total = (int)$countStmt->fetch(PDO::FETCH_ASSOC)['total'];
    
    // Add ordering and pagination
    $sql .= " ORDER BY lhc.server_time DESC LIMIT :limit OFFSET :offset";
    $params[':limit'] = $limit;
    $params[':offset'] = $offset;
    
    // Execute query
    $stmt = $pdo->prepare($sql);
    
    // Bind parameters
    foreach ($params as $key => $value) {
        if ($key === ':limit' || $key === ':offset') {
            $stmt->bindValue($key, $value, PDO::PARAM_INT);
        } else {
            $stmt->bindValue($key, $value);
        }
    }
    
    $stmt->execute();
    $points = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
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

    // Analyze segments if requested
    $dwells = [];
    $drives = [];

    if ($includeSegments && !empty($formattedPoints)) {
        $analyzer = new LocationAnalyzer();

        // Detect dwells
        $dwells = $analyzer->detectDwells($formattedPoints);

        // Segment drives
        $drives = $analyzer->segmentDrives($formattedPoints, $dwells);
    }

    // Build response data
    $responseData = [
        'points' => $formattedPoints,
        'count' => count($formattedPoints),
        'total' => $total,
        'limit' => $limit,
        'offset' => $offset,
        'duration' => $duration,
        'filters' => [
            'usernames' => $usernames,
            'device_ids' => $deviceIds,
            'all' => $getAll
        ],
        'source' => 'cache',
        'timestamp' => gmdate('Y-m-d\TH:i:s\Z')
    ];

    // Add segments if requested
    if ($includeSegments) {
        $responseData['segments'] = [
            'dwells' => $dwells,
            'drives' => $drives,
            'dwell_count' => count($dwells),
            'drive_count' => count($drives)
        ];
    }

    // Return response
    ApiResponse::success($responseData, 'Tracking history retrieved successfully');
    
} catch (PDOException $e) {
    error_log("Database error in live/history.php: " . $e->getMessage());
    ApiResponse::error('Database query failed', 500);
} catch (Exception $e) {
    error_log("Error in live/history.php: " . $e->getMessage());
    ApiResponse::error('Failed to retrieve tracking history: ' . $e->getMessage(), 500);
}

