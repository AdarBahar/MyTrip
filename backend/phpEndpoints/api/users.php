<?php
/**
 * Users Endpoint
 * 
 * GET /api/users.php
 * 
 * Returns list of users with location data, including optional counts and metadata.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Include required files
require_once __DIR__ . '/../shared/logging.php';
require_once __DIR__ . '/../shared/classes/ApiResponse.php';
require_once __DIR__ . '/../db-config.php';
require_once __DIR__ . '/middleware/authentication.php';

// Generate unique request ID
$requestId = uniqid('users_', true);
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
    // Get query parameters
    $withLocationData = filter_var($_GET['with_location_data'] ?? 'true', FILTER_VALIDATE_BOOLEAN);
    $includeCounts = filter_var($_GET['include_counts'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    $includeMetadata = filter_var($_GET['include_metadata'] ?? 'false', FILTER_VALIDATE_BOOLEAN);
    
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
    
    // Build query
    if ($withLocationData) {
        // Get users who have location data
        $sql = "
            SELECT DISTINCT u.id, u.username, u.display_name, u.created_at
            FROM users u
            INNER JOIN location_records lr ON u.id = lr.user_id
            ORDER BY u.username ASC
        ";
    } else {
        // Get all users
        $sql = "
            SELECT u.id, u.username, u.display_name, u.created_at
            FROM users u
            ORDER BY u.username ASC
        ";
    }
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $users = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Add counts and metadata if requested
    if ($includeCounts || $includeMetadata) {
        foreach ($users as &$user) {
            if ($includeCounts) {
                // Count location records
                $stmt = $pdo->prepare("
                    SELECT COUNT(*) as count 
                    FROM location_records 
                    WHERE user_id = ?
                ");
                $stmt->execute([$user['id']]);
                $user['location_count'] = (int)$stmt->fetchColumn();
                
                // Count driving records
                $stmt = $pdo->prepare("
                    SELECT COUNT(*) as count 
                    FROM driving_records 
                    WHERE user_id = ?
                ");
                $stmt->execute([$user['id']]);
                $user['driving_count'] = (int)$stmt->fetchColumn();
            }
            
            if ($includeMetadata) {
                // Get last location time
                $stmt = $pdo->prepare("
                    SELECT MAX(server_time) as last_time 
                    FROM location_records 
                    WHERE user_id = ?
                ");
                $stmt->execute([$user['id']]);
                $lastLocation = $stmt->fetchColumn();
                $user['last_location_time'] = $lastLocation ?: null;
                
                // Get last driving time
                $stmt = $pdo->prepare("
                    SELECT MAX(server_time) as last_time 
                    FROM driving_records 
                    WHERE user_id = ?
                ");
                $stmt->execute([$user['id']]);
                $lastDriving = $stmt->fetchColumn();
                $user['last_driving_time'] = $lastDriving ?: null;
            }
        }
        unset($user); // Break reference
    }
    
    // Log successful request
    logApiRequest('users', [
        'count' => count($users),
        'with_location_data' => $withLocationData,
        'include_counts' => $includeCounts,
        'include_metadata' => $includeMetadata,
        'request_id' => $requestId
    ]);
    
    // Return response
    ApiResponse::success([
        'users' => $users,
        'count' => count($users),
        'source' => 'database'
    ], 'Users retrieved successfully');
    
} catch (PDOException $e) {
    // Database errors
    error_log("Users endpoint database error: " . $e->getMessage());
    ApiResponse::error('Database error occurred', 500, [
        'request_id' => $requestId,
        'error_type' => 'database_error'
    ]);
    
} catch (Exception $e) {
    // General errors
    error_log("Users endpoint error: " . $e->getMessage());
    ApiResponse::error('An error occurred while retrieving users', 500, [
        'request_id' => $requestId,
        'error_type' => 'general_error'
    ]);
}

