<?php
/**
 * Shared Logging Functions
 * 
 * Provides centralized logging functionality for all API endpoints
 * 
 * @version 1.0
 * @author Adar Bahar
 */

/**
 * Security logging function
 * 
 * @param string $event The event type
 * @param array $details Additional event details
 */
function logSecurityEvent($event, $details = []) {
    global $requestId;
    
    $logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../logs'), '/');
    $logFile = $logDir . '/security.log';
    
    // Ensure log directory exists
    @mkdir($logDir, 0755, true);
    
    $entry = [
        'timestamp' => date('c'),
        'request_id' => $requestId ?? uniqid('log_', true),
        'event' => $event,
        'endpoint' => basename($_SERVER['SCRIPT_NAME'] ?? 'unknown'),
        'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
        'details' => $details
    ];
    
    @file_put_contents($logFile, json_encode($entry) . "\n", FILE_APPEND | LOCK_EX);
}

/**
 * API request logging function
 * 
 * @param string $endpoint The endpoint name
 * @param array $data Request data
 * @param mixed $response Response data
 */
function logApiRequest($endpoint, $data = [], $response = null) {
    global $requestId;
    
    $logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../logs'), '/');
    $logFile = $logDir . '/api-requests.log';
    
    // Ensure log directory exists
    @mkdir($logDir, 0755, true);
    
    $entry = [
        'timestamp' => date('c'),
        'request_id' => $requestId ?? uniqid('api_', true),
        'endpoint' => $endpoint,
        'method' => $_SERVER['REQUEST_METHOD'] ?? 'UNKNOWN',
        'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
        'request_data' => $data,
        'response' => $response
    ];
    
    @file_put_contents(
        $logFile,
        json_encode($entry, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL,
        FILE_APPEND | LOCK_EX
    );
}
?>
