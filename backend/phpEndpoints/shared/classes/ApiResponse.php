<?php
/**
 * API Response Helper
 * 
 * Standardized API response formatting and HTTP status code management
 * Provides consistent response structure across all endpoints
 * 
 * @version 2.0
 * @author Adar Bahar
 */

class ApiResponse {
    
    /**
     * Send successful response
     */
    public static function success($data = [], $message = 'Success', $statusCode = 200) {
        http_response_code($statusCode);
        header('Content-Type: application/json');
        
        $response = [
            'status' => 'success',
            'message' => $message,
            'timestamp' => date('c'),
            'data' => $data
        ];
        
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        exit;
    }
    
    /**
     * Send error response
     */
    public static function error($message = 'An error occurred', $statusCode = 400, $details = null) {
        http_response_code($statusCode);
        header('Content-Type: application/json');
        
        $response = [
            'status' => 'error',
            'message' => $message,
            'timestamp' => date('c'),
            'error_code' => $statusCode
        ];
        
        if ($details !== null) {
            $response['details'] = $details;
        }
        
        // Add request ID if available
        if (isset($GLOBALS['requestId'])) {
            $response['request_id'] = $GLOBALS['requestId'];
        }
        
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        exit;
    }
    
    /**
     * Send validation error response
     */
    public static function validationError($errors, $message = 'Validation failed') {
        self::error($message, 422, ['validation_errors' => $errors]);
    }
    
    /**
     * Send unauthorized response
     */
    public static function unauthorized($message = 'Unauthorized access') {
        self::error($message, 401);
    }
    
    /**
     * Send forbidden response
     */
    public static function forbidden($message = 'Access forbidden') {
        self::error($message, 403);
    }
    
    /**
     * Send not found response
     */
    public static function notFound($message = 'Resource not found') {
        self::error($message, 404);
    }
    
    /**
     * Send method not allowed response
     */
    public static function methodNotAllowed($allowedMethods = []) {
        if (!empty($allowedMethods)) {
            header('Allow: ' . implode(', ', $allowedMethods));
        }
        self::error('Method not allowed', 405);
    }
    
    /**
     * Send rate limit exceeded response
     */
    public static function rateLimitExceeded($retryAfter = null) {
        if ($retryAfter) {
            header('Retry-After: ' . $retryAfter);
        }
        self::error('Rate limit exceeded', 429);
    }
    
    /**
     * Send server error response
     */
    public static function serverError($message = 'Internal server error') {
        self::error($message, 500);
    }
    
    /**
     * Send service unavailable response
     */
    public static function serviceUnavailable($message = 'Service temporarily unavailable') {
        self::error($message, 503);
    }
    
    /**
     * Send location data response
     */
    public static function locationSuccess($data, $requestId = null) {
        $response = [
            'status' => 'success',
            'message' => 'Location received',
            'timestamp' => date('c'),
            'data' => $data
        ];
        
        if ($requestId) {
            $response['request_id'] = $requestId;
        }
        
        self::success($response['data'], $response['message']);
    }
    
    /**
     * Send driving event response
     */
    public static function drivingSuccess($data, $requestId = null) {
        $response = [
            'status' => 'success',
            'message' => $data['message'] ?? 'Driving event processed',
            'timestamp' => date('c'),
            'data' => $data
        ];
        
        if ($requestId) {
            $response['request_id'] = $requestId;
        }
        
        self::success($response['data'], $response['message']);
    }
    
    /**
     * Send batch sync response
     */
    public static function batchSyncSuccess($data, $requestId = null) {
        $response = [
            'status' => 'success',
            'message' => $data['message'] ?? 'Batch sync processed',
            'timestamp' => date('c'),
            'data' => $data
        ];
        
        if ($requestId) {
            $response['request_id'] = $requestId;
        }
        
        self::success($response['data'], $response['message']);
    }
    
    /**
     * Set CORS headers with production security
     */
    public static function setCorsHeaders($allowedOrigins = ['*'], $allowedMethods = ['GET', 'POST', 'OPTIONS']) {
        $origin = $_SERVER['HTTP_ORIGIN'] ?? '';

        // Production security headers
        header('X-Content-Type-Options: nosniff');
        header('X-Frame-Options: DENY');
        header('X-XSS-Protection: 1; mode=block');
        header('Referrer-Policy: strict-origin-when-cross-origin');

        // Only allow specific origins in production
        $allowedOriginsList = getenv('ALLOWED_ORIGINS') ? explode(',', getenv('ALLOWED_ORIGINS')) : $allowedOrigins;

        if (in_array('*', $allowedOriginsList) || in_array($origin, $allowedOriginsList) || in_array('mobile', $allowedOriginsList)) {
            header('Access-Control-Allow-Origin: ' . ($origin ?: '*'));
        }

        header('Access-Control-Allow-Methods: ' . implode(', ', $allowedMethods));
        header('Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Token, X-Requested-With');
        header('Access-Control-Allow-Credentials: true');
        header('Access-Control-Max-Age: 86400'); // 24 hours
    }
    
    /**
     * Handle OPTIONS request for CORS preflight
     */
    public static function handleOptionsRequest($allowedMethods = ['GET', 'POST', 'OPTIONS']) {
        if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
            self::setCorsHeaders(['*'], $allowedMethods);
            http_response_code(200);
            exit;
        }
    }
    
    /**
     * Validate required fields
     */
    public static function validateRequired($data, $requiredFields) {
        $missing = [];
        
        foreach ($requiredFields as $field) {
            if (!isset($data[$field]) || $data[$field] === '' || $data[$field] === null) {
                $missing[] = $field;
            }
        }
        
        if (!empty($missing)) {
            self::validationError($missing, 'Missing required fields: ' . implode(', ', $missing));
        }
    }
    
    /**
     * Validate coordinate values
     */
    public static function validateCoordinates($latitude, $longitude) {
        $errors = [];
        
        if (!is_numeric($latitude) || $latitude < -90 || $latitude > 90) {
            $errors['latitude'] = 'Latitude must be a number between -90 and 90';
        }
        
        if (!is_numeric($longitude) || $longitude < -180 || $longitude > 180) {
            $errors['longitude'] = 'Longitude must be a number between -180 and 180';
        }
        
        if (!empty($errors)) {
            self::validationError($errors, 'Invalid coordinate values');
        }
    }
    
    /**
     * Sanitize input data
     */
    public static function sanitizeInput($data, $rules = []) {
        $sanitized = [];
        
        foreach ($data as $key => $value) {
            if (isset($rules[$key])) {
                $rule = $rules[$key];
                
                switch ($rule['type']) {
                    case 'string':
                        $sanitized[$key] = substr((string)$value, 0, $rule['max_length'] ?? 255);
                        break;
                    case 'int':
                        $sanitized[$key] = (int)$value;
                        break;
                    case 'float':
                        $sanitized[$key] = (float)$value;
                        break;
                    case 'bool':
                        $sanitized[$key] = (bool)$value;
                        break;
                    default:
                        $sanitized[$key] = $value;
                }
            } else {
                $sanitized[$key] = $value;
            }
        }
        
        return $sanitized;
    }
    
    /**
     * Log API request for debugging
     */
    public static function logRequest($endpoint, $data = [], $response = null) {
        $logEntry = [
            'timestamp' => date('c'),
            'endpoint' => $endpoint,
            'method' => $_SERVER['REQUEST_METHOD'] ?? 'UNKNOWN',
            'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
            'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
            'request_data' => $data,
            'response' => $response
        ];
        
        $logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../../logs'), '/');
        $logFile = $logDir . '/api-requests.log';
        
        @file_put_contents(
            $logFile,
            json_encode($logEntry, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL,
            FILE_APPEND | LOCK_EX
        );
    }
}
?>
