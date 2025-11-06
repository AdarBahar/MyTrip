<?php
/**
 * Location Tracking API Index
 * 
 * Provides API discovery, status information, and documentation links
 * Shows available endpoints, authentication methods, and system status
 * 
 * @version 2.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/../shared/db-config.php';

// Production-safe headers
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('X-XSS-Protection: 1; mode=block');
header('Referrer-Policy: strict-origin-when-cross-origin');

// CORS headers
$allowedOrigins = getenv('ALLOWED_ORIGINS') ? explode(',', getenv('ALLOWED_ORIGINS')) : ['*'];
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';

if (in_array('*', $allowedOrigins) || in_array($origin, $allowedOrigins) || in_array('mobile', $allowedOrigins)) {
    header('Access-Control-Allow-Origin: ' . ($origin ?: '*'));
}

header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Token, Accept');
header('Access-Control-Max-Age: 86400');

// Handle OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Only allow GET requests
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed', 'allowed_methods' => ['GET']]);
    exit;
}

// Check database status
$databaseStatus = 'unknown';
$databaseMode = false;
try {
    if (DatabaseConfig::isDatabaseMode()) {
        $pdo = DatabaseConfig::getInstance()->getConnection();
        $stmt = $pdo->query('SELECT 1');
        $databaseStatus = 'operational';
        $databaseMode = true;
    } else {
        $databaseStatus = 'file_mode';
    }
} catch (Exception $e) {
    $databaseStatus = 'error';
    error_log("Database status check failed: " . $e->getMessage());
}

// Get system information
$systemInfo = [
    'php_version' => PHP_VERSION,
    'server_time' => date('c'),
    'timezone' => date_default_timezone_get(),
    'memory_usage' => memory_get_usage(true),
    'memory_limit' => ini_get('memory_limit')
];

// Check log directory
$logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../logs'), '/');
$logDirWritable = is_dir($logDir) && is_writable($logDir);

// API information
$apiInfo = [
    'name' => 'Location Tracking API',
    'version' => '2.0.0',
    'description' => 'Comprehensive location and driving data collection API with offline synchronization support',
    'status' => 'operational',
    'documentation' => [
        'swagger_ui' => './docs/',
        'openapi_spec' => './docs/openapi.json',
        'examples' => './docs/examples/',
        'postman_collection' => './docs/postman-collection.json'
    ],
    'endpoints' => [
        'location' => [
            'url' => './getloc.php',
            'method' => 'POST',
            'description' => 'Submit individual location data points',
            'content_type' => 'application/json',
            'authentication' => 'required'
        ],
        'driving' => [
            'url' => './driving.php', 
            'method' => 'POST',
            'description' => 'Submit driving event data (start, data, stop)',
            'content_type' => 'application/json',
            'authentication' => 'required'
        ],
        'batch_sync' => [
            'url' => './batch-sync.php',
            'method' => 'POST', 
            'description' => 'Batch synchronization for offline data',
            'content_type' => 'application/json',
            'authentication' => 'required'
        ]
    ],
    'authentication' => [
        'methods' => [
            'bearer_token' => [
                'header' => 'Authorization: Bearer {token}',
                'description' => 'Preferred method - JWT or API token in Authorization header',
                'priority' => 1
            ],
            'bearer_fallback' => [
                'header' => 'X-Auth-Token: {token}',
                'description' => 'Alternative Bearer token header (bypasses some firewalls)',
                'priority' => 2
            ],
            'api_key' => [
                'header' => 'X-API-Token: {token}',
                'description' => 'API key in custom header (legacy support)',
                'priority' => 3
            ]
        ],
        'note' => 'All endpoints require valid authentication. Use Bearer token for best compatibility.'
    ],
    'rate_limits' => [
        'location' => '1000 requests/hour per IP',
        'driving' => '500 requests/hour per IP', 
        'batch_sync' => '100 requests/hour per IP',
        'note' => 'Rate limits are enforced per IP address'
    ],
    'data_formats' => [
        'request' => 'application/json',
        'response' => 'application/json',
        'timestamp' => 'Unix timestamp in milliseconds',
        'coordinates' => 'Decimal degrees (WGS84)'
    ],
    'storage' => [
        'mode' => $databaseMode ? 'database' : 'files',
        'database_status' => $databaseStatus,
        'fallback' => 'Automatic fallback to file storage if database unavailable'
    ],
    'system' => [
        'status' => 'operational',
        'database' => $databaseStatus,
        'log_directory' => $logDirWritable ? 'writable' : 'not_writable',
        'php_version' => $systemInfo['php_version'],
        'server_time' => $systemInfo['server_time'],
        'timezone' => $systemInfo['timezone']
    ],
    'features' => [
        'real_time_location' => 'Individual location point submission',
        'driving_events' => 'Trip tracking with start/data/stop events',
        'batch_synchronization' => 'Offline data upload with multi-part support',
        'anomaly_detection' => 'Automatic GPS anomaly detection',
        'data_validation' => 'Comprehensive input validation',
        'rate_limiting' => 'Per-IP rate limiting protection',
        'cors_support' => 'Cross-origin resource sharing enabled',
        'fallback_storage' => 'Automatic database to file fallback'
    ],
    'response_format' => [
        'success' => [
            'status' => 'success',
            'message' => 'Description of the result',
            'timestamp' => 'ISO 8601 timestamp',
            'data' => 'Response data object'
        ],
        'error' => [
            'status' => 'error',
            'message' => 'Error description',
            'timestamp' => 'ISO 8601 timestamp',
            'error_code' => 'HTTP status code',
            'details' => 'Additional error details (optional)'
        ]
    ],
    'examples' => [
        'location_request' => [
            'id' => 'device-12345',
            'name' => 'john_doe',
            'latitude' => 32.0853,
            'longitude' => 34.7818,
            'accuracy' => 5.0,
            'timestamp' => 1726588200000,
            'speed' => 25.3,
            'bearing' => 180.0,
            'battery' => 85
        ],
        'driving_start_request' => [
            'id' => 'device-12345',
            'name' => 'john_doe',
            'event' => 'start',
            'timestamp' => 1726588200000,
            'location' => [
                'latitude' => 32.0853,
                'longitude' => 34.7818,
                'accuracy' => 5.0
            ]
        ]
    ],
    'support' => [
        'documentation' => 'https://www.bahar.co.il/location/api/docs/',
        'issues' => 'Contact system administrator',
        'version_history' => 'See documentation for changelog'
    ]
];

// Add health check information
$healthChecks = [
    'api_endpoints' => checkEndpointsHealth(),
    'database_connection' => $databaseStatus === 'operational',
    'log_directory' => $logDirWritable,
    'memory_usage' => $systemInfo['memory_usage'] < (1024 * 1024 * 100), // Less than 100MB
];

$apiInfo['health'] = [
    'overall' => array_reduce($healthChecks, function($carry, $check) { return $carry && $check; }, true) ? 'healthy' : 'degraded',
    'checks' => $healthChecks,
    'last_check' => date('c')
];

echo json_encode($apiInfo, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

/**
 * Check if API endpoints are accessible
 */
function checkEndpointsHealth() {
    $endpoints = ['getloc.php', 'driving.php', 'batch-sync.php'];
    $healthy = true;
    
    foreach ($endpoints as $endpoint) {
        if (!file_exists(__DIR__ . '/' . $endpoint)) {
            $healthy = false;
            break;
        }
    }
    
    return $healthy;
}
?>
