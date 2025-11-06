<?php
/**
 * CSRF Protection Helper for Dashboard
 * 
 * Provides Cross-Site Request Forgery protection for dashboard forms and AJAX requests
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Load environment variables using security-helpers
require_once __DIR__ . '/security-helpers.php';

// Load environment variables if not already loaded
if (!getenv('CSRF_PROTECTION_ENABLED')) {
    // Try multiple possible locations for .env file (same pattern as db-config.php)
    $envPaths = [
        __DIR__ . '/../.env',  // Root directory (most common)
        __DIR__ . '/.env',     // Shared directory
        dirname(__DIR__) . '/.env'  // Parent directory
    ];

    foreach ($envPaths as $envPath) {
        if (file_exists($envPath)) {
            load_env_file($envPath);
            break;
        }
    }
}

/**
 * Check if CSRF protection is enabled
 */
function isCsrfProtectionEnabled() {
    $enabled = getenv('CSRF_PROTECTION_ENABLED');
    return filter_var($enabled, FILTER_VALIDATE_BOOLEAN);
}

/**
 * Get CSRF configuration values
 */
function getCsrfConfig() {
    return [
        'enabled' => isCsrfProtectionEnabled(),
        'token_name' => getenv('CSRF_TOKEN_NAME') ?: 'csrf_token',
        'session_key' => getenv('CSRF_SESSION_KEY') ?: 'dashboard_csrf_token',
        'header_name' => getenv('CSRF_HEADER_NAME') ?: 'X-CSRF-Token'
    ];
}

/**
 * Initialize CSRF protection
 * Call this at the beginning of each dashboard page
 */
function initCsrfProtection() {
    if (!isCsrfProtectionEnabled()) {
        return; // CSRF protection disabled
    }

    // Start session if not already started
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }

    $config = getCsrfConfig();
    
    // Generate CSRF token if not exists
    if (empty($_SESSION[$config['session_key']])) {
        $_SESSION[$config['session_key']] = bin2hex(random_bytes(32));
    }
}

/**
 * Get current CSRF token
 */
function getCsrfToken() {
    if (!isCsrfProtectionEnabled()) {
        return ''; // CSRF protection disabled
    }

    $config = getCsrfConfig();
    return $_SESSION[$config['session_key']] ?? '';
}

/**
 * Generate CSRF token HTML input field
 */
function getCsrfTokenField() {
    if (!isCsrfProtectionEnabled()) {
        return ''; // CSRF protection disabled
    }

    $config = getCsrfConfig();
    $token = getCsrfToken();
    return '<input type="hidden" name="' . htmlspecialchars($config['token_name']) . '" value="' . htmlspecialchars($token) . '">';
}

/**
 * Validate CSRF token from POST request
 * Call this before processing any POST data
 */
function validateCsrfToken() {
    if (!isCsrfProtectionEnabled()) {
        return true; // CSRF protection disabled
    }

    // Only validate for POST requests
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        return true;
    }

    $config = getCsrfConfig();
    $sessionToken = $_SESSION[$config['session_key']] ?? '';
    
    // Check token from POST data first
    $submittedToken = $_POST[$config['token_name']] ?? '';
    
    // If not in POST data, check headers (for AJAX requests)
    if (empty($submittedToken)) {
        $headerName = 'HTTP_' . str_replace('-', '_', strtoupper($config['header_name']));
        $submittedToken = $_SERVER[$headerName] ?? '';
    }

    // Validate token using timing-safe comparison
    if (empty($sessionToken) || empty($submittedToken)) {
        return false;
    }

    return hash_equals($sessionToken, $submittedToken);
}

/**
 * Handle CSRF validation failure
 * Call this when CSRF validation fails
 */
function handleCsrfFailure($isAjax = false) {
    // Log security event
    error_log('CSRF validation failed - IP: ' . ($_SERVER['REMOTE_ADDR'] ?? 'unknown') . 
              ' - User Agent: ' . ($_SERVER['HTTP_USER_AGENT'] ?? 'unknown'));

    http_response_code(403);
    
    if ($isAjax) {
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'error' => 'CSRF token validation failed. Please refresh the page and try again.',
            'csrf_error' => true
        ]);
    } else {
        echo '<!DOCTYPE html>
<html>
<head>
    <title>Security Error</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }
        .error-box { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .back-btn { background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>🔒 Security Error</h1>
    <div class="error-box">
        <h3>⚠️ CSRF Token Validation Failed</h3>
        <p>Your request could not be processed due to a security token mismatch.</p>
        <p>This usually happens when:</p>
        <ul style="text-align: left; display: inline-block;">
            <li>Your session has expired</li>
            <li>You have multiple tabs open</li>
            <li>Your browser cache needs to be cleared</li>
        </ul>
    </div>
    <a href="javascript:history.back()" class="back-btn">← Go Back</a>
    <a href="?" class="back-btn">🔄 Refresh Page</a>
</body>
</html>';
    }
    exit;
}

/**
 * Check if current request is AJAX
 */
function isAjaxRequest() {
    return !empty($_SERVER['HTTP_X_REQUESTED_WITH']) && 
           strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';
}

/**
 * Validate CSRF and handle failure automatically
 * Convenience function that combines validation and error handling
 */
function requireValidCsrfToken() {
    if (!validateCsrfToken()) {
        handleCsrfFailure(isAjaxRequest());
    }
}
