<?php
/**
 * Live Tracking - Latest Locations Endpoint
 * 
 * GET /api/live/latest.php
 * 
 * Returns the most recent location for specified user(s) or device(s).
 * Supports single user, multiple users, or all users.
 * 
 * Query Parameters:
 * - user: Single username or comma-separated list (e.g., "john_doe" or "john_doe,jane_smith")
 * - users[]: Array of usernames (e.g., users[]=john_doe&users[]=jane_smith)
 * - device: Single device ID or comma-separated list
 * - devices[]: Array of device IDs
 * - all: Get latest for all active users (default: false)
 * - max_age: Maximum age in seconds (default: 3600 = 1 hour)
 * - include_inactive: Include users with no recent location (default: false)
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
$requestId = uniqid('live_latest_', true);
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

// Rate limiting - more permissive for live tracking
if (!checkRateLimit($_SERVER['REMOTE_ADDR'] ?? 'unknown', 2000)) {
    ApiResponse::rateLimitExceeded('Rate limit exceeded. Maximum 2000 requests per hour.');
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
    $maxAge = isset($_GET['max_age']) ? (int)$_GET['max_age'] : 3600; // Default 1 hour
    $includeInactive = filter_var($_GET['include_inactive'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    $getAll = filter_var($_GET['all'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    
    // Parse user filters
    $usernames = [];
    if (isset($_GET['user'])) {
        // Single user or comma-separated list
        $usernames = array_map('trim', explode(',', $_GET['user']));
    } elseif (isset($_GET['users']) && is_array($_GET['users'])) {
        // Array of users
        $usernames = array_map('trim', $_GET['users']);
    }
    
    // Parse device filters
    $deviceIds = [];
    if (isset($_GET['device'])) {
        // Single device or comma-separated list
        $deviceIds = array_map('trim', explode(',', $_GET['device']));
    } elseif (isset($_GET['devices']) && is_array($_GET['devices'])) {
        // Array of devices
        $deviceIds = array_map('trim', $_GET['devices']);
    }
    
    // Build query
    $sql = "
        SELECT 
            dlp.device_id,
            dlp.user_id,
            u.username,
            u.display_name,
            dlp.latitude,
            dlp.longitude,
            dlp.accuracy,
            dlp.altitude,
            dlp.speed,
            dlp.bearing,
            dlp.battery_level,
            dlp.network_type,
            dlp.provider,
            dlp.recorded_at,
            dlp.server_time,
            TIMESTAMPDIFF(SECOND, dlp.server_time, NOW()) as age_seconds
        FROM device_last_position dlp
        JOIN users u ON dlp.user_id = u.id
        WHERE 1=1
    ";
    
    $params = [];
    
    // Apply max age filter (unless include_inactive is true)
    if (!$includeInactive) {
        $sql .= " AND dlp.server_time >= DATE_SUB(NOW(), INTERVAL :max_age SECOND)";
        $params[':max_age'] = $maxAge;
    }
    
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
        $sql .= " AND dlp.device_id IN (" . implode(',', $placeholders) . ")";
    }
    
    $sql .= " ORDER BY dlp.server_time DESC";
    
    // Execute query
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $locations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Format response
    $formattedLocations = [];
    foreach ($locations as $loc) {
        $formattedLocations[] = [
            'device_id' => $loc['device_id'],
            'user_id' => (int)$loc['user_id'],
            'username' => $loc['username'],
            'display_name' => $loc['display_name'],
            'latitude' => (float)$loc['latitude'],
            'longitude' => (float)$loc['longitude'],
            'accuracy' => $loc['accuracy'] !== null ? (float)$loc['accuracy'] : null,
            'altitude' => $loc['altitude'] !== null ? (float)$loc['altitude'] : null,
            'speed' => $loc['speed'] !== null ? (float)$loc['speed'] : null,
            'bearing' => $loc['bearing'] !== null ? (float)$loc['bearing'] : null,
            'battery_level' => $loc['battery_level'] !== null ? (int)$loc['battery_level'] : null,
            'network_type' => $loc['network_type'],
            'provider' => $loc['provider'],
            'recorded_at' => $loc['recorded_at'],
            'server_time' => $loc['server_time'],
            'age_seconds' => (int)$loc['age_seconds'],
            'is_recent' => (int)$loc['age_seconds'] < 300 // Less than 5 minutes
        ];
    }
    
    // Return response
    ApiResponse::success([
        'locations' => $formattedLocations,
        'count' => count($formattedLocations),
        'max_age' => $maxAge,
        'filters' => [
            'usernames' => $usernames,
            'device_ids' => $deviceIds,
            'all' => $getAll
        ],
        'source' => 'database',
        'timestamp' => gmdate('Y-m-d\TH:i:s\Z')
    ], 'Latest locations retrieved successfully');
    
} catch (PDOException $e) {
    error_log("Database error in live/latest.php: " . $e->getMessage());
    ApiResponse::error('Database query failed', 500);
} catch (Exception $e) {
    error_log("Error in live/latest.php: " . $e->getMessage());
    ApiResponse::error('Failed to retrieve latest locations: ' . $e->getMessage(), 500);
}

