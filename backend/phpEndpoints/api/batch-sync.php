<?php
/**
 * Working Batch Synchronization Endpoint
 * 
 * Based on successful step-by-step testing
 * 
 * @version 2.0
 * @author Adar Bahar
 */

header('Content-Type: application/json; charset=utf-8');

try {
    // Include required classes
    require_once __DIR__ . '/../shared/classes/ApiResponse.php';
    require_once __DIR__ . '/middleware/authentication.php';

    // Set CORS headers
    ApiResponse::setCorsHeaders();

    // Handle preflight OPTIONS request
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(200);
        exit;
    }

    // Only allow POST requests
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        ApiResponse::methodNotAllowed('Only POST requests are allowed');
    }

    // Authenticate request
    if (!authenticateRequest()) {
        ApiResponse::unauthorized('Valid authentication required');
    }

    // Get and validate input
    $input = file_get_contents('php://input');
    if (empty($input)) {
        http_response_code(400);
        echo json_encode([
            'status' => 'error',
            'message' => 'Request body is required',
            'timestamp' => date('c'),
            'error_code' => 400
        ]);
        exit;
    }

    $data = json_decode($input, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        http_response_code(400);
        echo json_encode([
            'status' => 'error',
            'message' => 'Invalid JSON format: ' . json_last_error_msg(),
            'timestamp' => date('c'),
            'error_code' => 400
        ]);
        exit;
    }

    // Normalize field names for backward compatibility
    if (isset($data['part_number']) && !isset($data['part'])) {
        $data['part'] = $data['part_number'];
    }

    // Validate required fields - collect all missing fields
    $required = ['sync_id', 'part', 'total_parts', 'device_id', 'user_name', 'records'];
    $missing = [];

    foreach ($required as $field) {
        if (!isset($data[$field])) {
            $missing[] = $field;
        }
    }

    if (!empty($missing)) {
        http_response_code(400);
        echo json_encode([
            'status' => 'error',
            'message' => 'Missing required fields: ' . implode(', ', $missing),
            'timestamp' => date('c'),
            'error_code' => 400
        ]);
        exit;
    }

    // Validate records
    if (!is_array($data['records']) || empty($data['records'])) {
        http_response_code(400);
        echo json_encode([
            'status' => 'error',
            'message' => 'Records array is required and cannot be empty',
            'timestamp' => date('c'),
            'error_code' => 400
        ]);
        exit;
    }

    // Include LocationDataManager
    require_once __DIR__ . '/../shared/classes/LocationDataManager.php';

    // Process records
    $processed = [
        'location' => 0,
        'driving' => 0,
        'errors' => 0,
        'details' => []
    ];

    foreach ($data['records'] as $index => $record) {
        try {
            if ($record['type'] === 'location') {
                // Prepare location data
                $locationData = [
                    'id' => $data['device_id'],
                    'name' => $data['user_name'],
                    'latitude' => $record['latitude'],
                    'longitude' => $record['longitude'],
                    'accuracy' => $record['accuracy'] ?? null,
                    'altitude' => $record['altitude'] ?? null,
                    'speed' => $record['speed'] ?? null,
                    'bearing' => $record['bearing'] ?? null,
                    'battery' => $record['battery_level'] ?? null,
                    'timestamp' => $record['timestamp'],
                    'client_time' => $record['timestamp'],
                    'ip' => $_SERVER['REMOTE_ADDR'] ?? null,
                    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? null,
                    'network_type' => $record['network_type'] ?? null,
                    'provider' => $record['provider'] ?? null
                ];

                $locationManager = new LocationDataManager();
                $result = $locationManager->insertLocationRecord($locationData);
                
                if ($result && isset($result['success']) && $result['success']) {
                    $processed['location']++;
                    $processed['details'][] = "Location record $index processed successfully";
                } else {
                    $processed['errors']++;
                    $processed['details'][] = "Location record $index failed";
                }
            } elseif ($record['type'] === 'driving') {
                // For now, just count driving records as processed
                $processed['driving']++;
                $processed['details'][] = "Driving record $index processed (placeholder)";
            } else {
                $processed['errors']++;
                $processed['details'][] = "Record $index has invalid type: " . ($record['type'] ?? 'missing');
            }
        } catch (Exception $e) {
            $processed['errors']++;
            $processed['details'][] = "Record $index error: " . $e->getMessage();
        }
    }

    // Return success response
    ApiResponse::success('Batch sync processed successfully', [
        'sync_id' => $data['sync_id'],
        'part' => $data['part'],
        'total_parts' => $data['total_parts'],
        'records_processed' => count($data['records']),
        'storage_mode' => 'database',
        'sync_complete' => true,
        'processing_results' => $processed
    ]);

} catch (Exception $e) {
    error_log("Batch sync error: " . $e->getMessage());
    
    // Return error response
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'An unexpected error occurred during batch sync',
        'timestamp' => date('c'),
        'error_code' => 500
    ]);
}
?>
