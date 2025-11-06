<?php
/**
 * Driving Data API Endpoint
 * 
 * Handles driving events (start, data, stop) with database and file fallback support
 * Enhanced with proper validation, error handling, and response formatting
 * 
 * @version 2.0
 * @author Adar Bahar
 */

// Include required classes
require_once __DIR__ . '/../shared/logging.php';
require_once __DIR__ . '/../shared/classes/DrivingDataManager.php';
require_once __DIR__ . '/../shared/classes/ApiResponse.php';
require_once __DIR__ . '/middleware/authentication.php';

// Generate unique request ID for tracking
$requestId = uniqid('drv_', true);
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
ApiResponse::validateRequired($data, ['id', 'name', 'event', 'timestamp', 'location']);

// Validate event type
$validEvents = ['start', 'data', 'stop'];
if (!in_array($data['event'], $validEvents)) {
    ApiResponse::validationError(['event' => 'Event must be one of: ' . implode(', ', $validEvents)], 'Invalid event type');
}

// Validate location object
if (!is_array($data['location']) || !isset($data['location']['latitude']) || !isset($data['location']['longitude'])) {
    ApiResponse::validationError(['location' => 'Location must contain latitude and longitude'], 'Invalid location data');
}

// Validate coordinates
ApiResponse::validateCoordinates($data['location']['latitude'], $data['location']['longitude']);

// Sanitize input data
$sanitizationRules = [
    'id' => ['type' => 'string', 'max_length' => 100],
    'name' => ['type' => 'string', 'max_length' => 100],
    'event' => ['type' => 'string', 'max_length' => 20],
    'timestamp' => ['type' => 'int'],
    'speed' => ['type' => 'float'],
    'bearing' => ['type' => 'float'],
    'altitude' => ['type' => 'float'],
    'trip_id' => ['type' => 'string', 'max_length' => 100]
];

$sanitizedData = ApiResponse::sanitizeInput($data, $sanitizationRules);

// Sanitize location data
if (isset($data['location'])) {
    $locationRules = [
        'latitude' => ['type' => 'float'],
        'longitude' => ['type' => 'float'],
        'accuracy' => ['type' => 'float'],
        'altitude' => ['type' => 'float']
    ];
    $sanitizedData['location'] = ApiResponse::sanitizeInput($data['location'], $locationRules);
}

// Sanitize trip summary if present
if (isset($data['trip_summary']) && is_array($data['trip_summary'])) {
    $sanitizedData['trip_summary'] = $data['trip_summary'];
}

// Add request metadata
$sanitizedData['ip'] = $_SERVER['REMOTE_ADDR'] ?? null;
$sanitizedData['user_agent'] = $_SERVER['HTTP_USER_AGENT'] ?? null;
$sanitizedData['client_time'] = $sanitizedData['timestamp'] ?? null;
$sanitizedData['event_type'] = $sanitizedData['event']; // Normalize field name

// Additional validation
$errors = [];

// Validate optional numeric fields
if (isset($sanitizedData['speed']) && $sanitizedData['speed'] < 0) {
    $errors['speed'] = 'Speed must be non-negative';
}

if (isset($sanitizedData['bearing']) && ($sanitizedData['bearing'] < 0 || $sanitizedData['bearing'] > 360)) {
    $errors['bearing'] = 'Bearing must be between 0 and 360 degrees';
}

if (isset($sanitizedData['location']['accuracy']) && $sanitizedData['location']['accuracy'] < 0) {
    $errors['location.accuracy'] = 'Accuracy must be non-negative';
}

if (!empty($errors)) {
    ApiResponse::validationError($errors, 'Validation failed');
}

// Process the driving event
try {
    $drivingManager = new DrivingDataManager();
    
    // Handle different event types
    switch ($sanitizedData['event_type']) {
        case 'start':
            $result = $drivingManager->handleDrivingStart($sanitizedData);
            break;
            
        case 'data':
            $result = $drivingManager->handleDrivingData($sanitizedData);
            break;
            
        case 'stop':
            $result = $drivingManager->handleDrivingStop($sanitizedData);
            break;
            
        default:
            ApiResponse::validationError(['event' => 'Invalid event type'], 'Unsupported event type');
    }
    
    // Log request
    ApiResponse::logRequest('driving.php', $sanitizedData, $result);
    
    // Prepare response data
    $responseData = [
        'id' => $sanitizedData['id'],
        'name' => $sanitizedData['name'],
        'event_type' => $sanitizedData['event_type'],
        'status' => $result['status'],
        'message' => $result['message'],
        'request_id' => $requestId
    ];
    
    // Add trip ID if available
    if (isset($result['trip_id'])) {
        $responseData['trip_id'] = $result['trip_id'];
    }
    
    // Add storage mode if available
    if (isset($result['storage_mode'])) {
        $responseData['storage_mode'] = $result['storage_mode'];
    }
    
    // Add record ID if available (database mode)
    if (isset($result['record_id'])) {
        $responseData['record_id'] = $result['record_id'];
    }
    
    // Determine HTTP status code based on result
    $statusCode = 200;
    if ($result['status'] === 'error') {
        $statusCode = 400;
    } elseif ($result['status'] === 'warning') {
        $statusCode = 200; // Warnings are still successful
    }
    
    if ($result['status'] === 'error') {
        ApiResponse::error($result['message'], $statusCode, $responseData);
    } else {
        ApiResponse::drivingSuccess($responseData, $requestId);
    }
    
} catch (Exception $e) {
    // Log exception
    error_log("Driving API error: " . $e->getMessage());
    ApiResponse::logRequest('driving.php', $sanitizedData, ['error' => $e->getMessage()]);
    
    ApiResponse::serverError('An unexpected error occurred');
}

/**
 * Validate trip summary data
 */
function validateTripSummary($tripSummary) {
    if (!is_array($tripSummary)) {
        return ['trip_summary' => 'Trip summary must be an object'];
    }
    
    $errors = [];
    
    // Validate numeric fields if present
    $numericFields = ['distance', 'duration', 'max_speed', 'avg_speed'];
    foreach ($numericFields as $field) {
        if (isset($tripSummary[$field]) && (!is_numeric($tripSummary[$field]) || $tripSummary[$field] < 0)) {
            $errors["trip_summary.{$field}"] = "{$field} must be a non-negative number";
        }
    }
    
    // Validate coordinates if present
    if (isset($tripSummary['start_location'])) {
        if (!is_array($tripSummary['start_location']) || 
            !isset($tripSummary['start_location']['latitude']) || 
            !isset($tripSummary['start_location']['longitude'])) {
            $errors['trip_summary.start_location'] = 'Start location must contain latitude and longitude';
        }
    }
    
    if (isset($tripSummary['end_location'])) {
        if (!is_array($tripSummary['end_location']) || 
            !isset($tripSummary['end_location']['latitude']) || 
            !isset($tripSummary['end_location']['longitude'])) {
            $errors['trip_summary.end_location'] = 'End location must contain latitude and longitude';
        }
    }
    
    return $errors;
}


?>
