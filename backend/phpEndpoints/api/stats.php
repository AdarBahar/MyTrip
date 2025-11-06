<?php
/**
 * Stats Endpoint
 * 
 * GET/POST /api/stats
 * 
 * Returns statistics for a device including location updates,
 * driving sessions, and other metrics for specified timeframes.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Prevent direct access
if (!defined('STDIN') && php_sapi_name() !== 'cli') {
    // This is a web request
}

// Include required files
require_once __DIR__ . '/../shared/logging.php';
require_once __DIR__ . '/../shared/classes/ApiResponse.php';
require_once __DIR__ . '/../db-config.php';
require_once __DIR__ . '/middleware/authentication.php';
require_once __DIR__ . '/classes/StatsManager.php';

// Generate unique request ID
$requestId = uniqid('stats_', true);
$GLOBALS['requestId'] = $requestId;

// Set CORS headers
ApiResponse::setCorsHeaders();

// Handle OPTIONS request
ApiResponse::handleOptionsRequest(['GET', 'POST', 'OPTIONS']);

// Allow both GET and POST
if (!in_array($_SERVER['REQUEST_METHOD'], ['GET', 'POST'])) {
    ApiResponse::methodNotAllowed(['GET', 'POST']);
}

// Authenticate request
if (!authenticateRequest()) {
    ApiResponse::unauthorized('Valid API token required');
}

// Rate limiting - same as other endpoints
if (!checkRateLimit($_SERVER['REMOTE_ADDR'] ?? 'unknown', 1000)) {
    ApiResponse::rateLimitExceeded('Rate limit exceeded. Maximum 1000 requests per hour.');
}

try {
    // Get request data
    $data = [];
    
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        // Parse JSON body
        $rawInput = file_get_contents('php://input');
        $data = json_decode($rawInput, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            ApiResponse::badRequest('Invalid JSON: ' . json_last_error_msg());
        }
    } else {
        // GET request - use query parameters
        $data = $_GET;
    }
    
    // Validate required parameters
    if (empty($data['device_name'])) {
        ApiResponse::error('device_name is required', 400);
    }

    $deviceName = trim($data['device_name']);
    $timeframe = $data['timeframe'] ?? 'today';
    $customFrom = $data['from'] ?? null;
    $customTo = $data['to'] ?? null;
    
    // Validate timeframe
    $validTimeframes = ['today', 'last_24h', 'last_7d', 'last_week', 'total', 'custom'];
    if (!in_array($timeframe, $validTimeframes)) {
        ApiResponse::error('Invalid timeframe. Must be one of: ' . implode(', ', $validTimeframes), 400);
    }

    // Validate custom timeframe
    if ($timeframe === 'custom') {
        if (empty($customFrom) || empty($customTo)) {
            ApiResponse::error('custom timeframe requires both from and to parameters', 400);
        }

        // Validate date formats
        if (!strtotime($customFrom) || !strtotime($customTo)) {
            ApiResponse::error('Invalid date format. Use ISO 8601 format (e.g., 2025-10-01T00:00:00Z)', 400);
        }
    }
    
    // Get database connection
    $pdo = null;
    try {
        if (DatabaseConfig::isDatabaseMode()) {
            $db = DatabaseConfig::getInstance();
            if ($db->testConnection() && $db->tablesExist()) {
                $pdo = $db->getConnection();
            }
        }
    } catch (Exception $e) {
        error_log("Stats endpoint: Database connection failed - " . $e->getMessage());
        // Continue with file mode
    }
    
    // Create stats manager
    $statsManager = new StatsManager($pdo);

    // Get statistics
    $stats = $statsManager->getStats($deviceName, $timeframe, $customFrom, $customTo);

    // Log successful request
    logApiRequest('stats', [
        'device_name' => $deviceName,
        'device_id' => $stats['device_id'] ?? null,
        'timeframe' => $timeframe,
        'cached' => $stats['meta']['cached'] ?? false,
        'request_id' => $requestId
    ]);
    
    // Return response
    ApiResponse::success($stats, 'Statistics retrieved successfully');
    
} catch (InvalidArgumentException $e) {
    // Validation errors
    ApiResponse::error($e->getMessage(), 400);
    
} catch (PDOException $e) {
    // Database errors
    error_log("Stats endpoint database error: " . $e->getMessage());
    ApiResponse::error('Database error occurred', 500, [
        'request_id' => $requestId,
        'error_type' => 'database_error'
    ]);
    
} catch (Exception $e) {
    // General errors
    error_log("Stats endpoint error: " . $e->getMessage());
    ApiResponse::error('An error occurred while retrieving statistics', 500, [
        'request_id' => $requestId,
        'error_type' => 'general_error'
    ]);
}

