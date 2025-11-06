<?php
/**
 * Live Streaming - Session Management
 * 
 * POST /api/live/session - Create new streaming session
 * DELETE /api/live/session/{session_id} - Revoke session
 * 
 * Creates JWT-based session tokens for secure streaming connections.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/../../shared/db-config.php';
require_once __DIR__ . '/../../shared/classes/ApiResponse.php';
require_once __DIR__ . '/../../shared/classes/JwtSessionManager.php';
require_once __DIR__ . '/../middleware/authentication.php';

// Set CORS headers
ApiResponse::setCorsHeaders();

// Handle OPTIONS request
ApiResponse::handleOptionsRequest(['POST', 'DELETE', 'OPTIONS']);

// Authenticate request
if (!authenticateRequest()) {
    ApiResponse::unauthorized('Valid API token required');
}

// Get database connection
try {
    $db = DatabaseConfig::getInstance();
    if (!$db->testConnection()) {
        ApiResponse::error('Database is not available', 503);
    }
    
    $pdo = $db->getConnection();
} catch (Exception $e) {
    error_log("Database connection failed: " . $e->getMessage());
    ApiResponse::error('Database connection failed', 503);
}

// Initialize session manager
$sessionManager = new JwtSessionManager($pdo);

// Handle POST - Create session
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Get input
    $input = file_get_contents('php://input');
    if (empty($input)) {
        ApiResponse::validationError(['request_body' => 'Request body is required'], 'Empty request body');
    }
    
    $data = json_decode($input, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        ApiResponse::validationError(['json' => 'Invalid JSON format'], 'Invalid JSON in request body');
    }
    
    // Get user ID from authenticated token
    // For now, we'll use a default user ID or extract from token
    // TODO: Implement proper user extraction from API token
    $userId = $data['user_id'] ?? 1; // Default to user 1 for testing
    
    // Get device IDs (optional)
    $deviceIds = $data['device_ids'] ?? [];
    if (!is_array($deviceIds)) {
        ApiResponse::validationError(['device_ids' => 'Must be an array'], 'Invalid device_ids format');
    }
    
    // Get duration (optional)
    $duration = $data['duration'] ?? null;
    if ($duration !== null && (!is_numeric($duration) || $duration < 60 || $duration > 86400)) {
        ApiResponse::validationError(
            ['duration' => 'Must be between 60 and 86400 seconds'],
            'Invalid duration'
        );
    }
    
    // Create session
    try {
        $result = $sessionManager->createSession($userId, $deviceIds, $duration);

        if (!$result['success']) {
            error_log("Session creation failed for user $userId: " . ($result['error'] ?? 'Unknown error'));
            ApiResponse::error($result['error'] ?? 'Failed to create session', 500);
        }
    } catch (Exception $e) {
        error_log("Session creation exception for user $userId: " . $e->getMessage());
        error_log("Stack trace: " . $e->getTraceAsString());
        ApiResponse::error('Failed to create session: ' . $e->getMessage(), 500);
    }
    
    // Return session data
    ApiResponse::success([
        'session_id' => $result['session_id'],
        'session_token' => $result['session_token'],
        'expires_at' => $result['expires_at'],
        'duration' => $result['duration'],
        'stream_url' => $result['stream_url'],
        'device_ids' => $deviceIds
    ], 'Session created successfully');
}

// Handle DELETE - Revoke session
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    // Get session ID from URL path
    $path = $_SERVER['REQUEST_URI'];
    $pathParts = explode('/', trim($path, '/'));
    $sessionId = end($pathParts);
    
    if (empty($sessionId) || $sessionId === 'session.php') {
        ApiResponse::validationError(['session_id' => 'Session ID is required'], 'Missing session ID');
    }
    
    // Get user ID from authenticated token
    // TODO: Implement proper user extraction from API token
    $userId = $_GET['user_id'] ?? 1; // Default to user 1 for testing
    
    // Revoke session
    $success = $sessionManager->revokeSession($sessionId, $userId);
    
    if (!$success) {
        ApiResponse::error('Session not found or already revoked', 404);
    }
    
    ApiResponse::success([
        'session_id' => $sessionId,
        'revoked' => true
    ], 'Session revoked successfully');
}

// Method not allowed
ApiResponse::methodNotAllowed(['POST', 'DELETE']);

