<?php
/**
 * Location Data API Endpoint
 * 
 * Receives and stores individual location data points with database and file fallback support
 * Enhanced with proper validation, error handling, and response formatting
 * 
 * @version 2.0
 * @author Adar Bahar
 */

// Include required classes
require_once __DIR__ . '/../shared/logging.php';
require_once __DIR__ . '/../shared/classes/LocationDataManager.php';
require_once __DIR__ . '/../shared/classes/ApiResponse.php';
require_once __DIR__ . '/middleware/authentication.php';

// Generate unique request ID for tracking
$requestId = uniqid('loc_', true);
$GLOBALS['requestId'] = $requestId;

// Set CORS headers
ApiResponse::setCorsHeaders();

// Handle OPTIONS request for CORS preflight
ApiResponse::handleOptionsRequest(['POST', 'OPTIONS']);

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    ApiResponse::methodNotAllowed(['POST']);
}

// Authenticate request
if (!authenticateRequest()) {
    ApiResponse::unauthorized('Valid API token required');
}

// Get and validate input
$input = file_get_contents('php://input');
if (empty($input)) {
    ApiResponse::validationError(['request_body' => 'Request body is required'], 'Empty request body');
}

$data = json_decode($input, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    ApiResponse::validationError(['json' => 'Invalid JSON format'], 'Invalid JSON in request body');
}

// Validate required fields
ApiResponse::validateRequired($data, ['id', 'name', 'latitude', 'longitude']);

// Validate coordinates
ApiResponse::validateCoordinates($data['latitude'], $data['longitude']);

// Sanitize input data
$sanitizationRules = [
    'id' => ['type' => 'string', 'max_length' => 100],
    'name' => ['type' => 'string', 'max_length' => 100],
    'latitude' => ['type' => 'float'],
    'longitude' => ['type' => 'float'],
    'accuracy' => ['type' => 'float'],
    'altitude' => ['type' => 'float'],
    'speed' => ['type' => 'float'],
    'bearing' => ['type' => 'float'],
    'battery_level' => ['type' => 'int'],
    'network_type' => ['type' => 'string', 'max_length' => 20],
    'provider' => ['type' => 'string', 'max_length' => 20],
    'timestamp' => ['type' => 'int']
];

$sanitizedData = ApiResponse::sanitizeInput($data, $sanitizationRules);

// Add request metadata
$sanitizedData['ip'] = $_SERVER['REMOTE_ADDR'] ?? null;
$sanitizedData['user_agent'] = $_SERVER['HTTP_USER_AGENT'] ?? null;
$sanitizedData['client_time'] = $sanitizedData['timestamp'] ?? null;

// Additional validation
$errors = [];

// Validate coordinate ranges (already done by validateCoordinates, but double-check)
if ($sanitizedData['latitude'] < -90 || $sanitizedData['latitude'] > 90) {
    $errors['latitude'] = 'Latitude must be between -90 and 90';
}

if ($sanitizedData['longitude'] < -180 || $sanitizedData['longitude'] > 180) {
    $errors['longitude'] = 'Longitude must be between -180 and 180';
}

// Validate optional numeric fields
if (isset($sanitizedData['accuracy']) && $sanitizedData['accuracy'] < 0) {
    $errors['accuracy'] = 'Accuracy must be non-negative';
}

if (isset($sanitizedData['speed']) && $sanitizedData['speed'] < 0) {
    $errors['speed'] = 'Speed must be non-negative';
}

if (isset($sanitizedData['bearing']) && ($sanitizedData['bearing'] < 0 || $sanitizedData['bearing'] > 360)) {
    $errors['bearing'] = 'Bearing must be between 0 and 360 degrees';
}

if (isset($sanitizedData['battery_level']) && ($sanitizedData['battery_level'] < 0 || $sanitizedData['battery_level'] > 100)) {
    $errors['battery_level'] = 'Battery level must be between 0 and 100';
}

if (!empty($errors)) {
    ApiResponse::validationError($errors, 'Validation failed');
}

// Process the location data
try {
    $locationManager = new LocationDataManager();
    $result = $locationManager->insertLocationRecord($sanitizedData);
    
    if ($result['success']) {
        // Log successful request
        ApiResponse::logRequest('getloc.php', $sanitizedData, $result);
        
        // Prepare response data
        $responseData = [
            'id' => $sanitizedData['id'],
            'name' => $sanitizedData['name'],
            'storage_mode' => $result['storage_mode'],
            'request_id' => $requestId
        ];
        
        // Add record ID if available (database mode)
        if (isset($result['record_id'])) {
            $responseData['record_id'] = $result['record_id'];
        }
        
        // Add file path if available (file mode)
        if (isset($result['file_path'])) {
            $responseData['file_path'] = basename($result['file_path']);
        }
        
        ApiResponse::locationSuccess($responseData, $requestId);
        
    } else {
        // Log failed request
        ApiResponse::logRequest('getloc.php', $sanitizedData, ['error' => 'Storage failed']);
        
        ApiResponse::serverError('Failed to store location data');
    }
    
} catch (Exception $e) {
    // Log exception
    error_log("Location API error: " . $e->getMessage());
    ApiResponse::logRequest('getloc.php', $sanitizedData, ['error' => $e->getMessage()]);
    
    ApiResponse::serverError('An unexpected error occurred');
}




?>
