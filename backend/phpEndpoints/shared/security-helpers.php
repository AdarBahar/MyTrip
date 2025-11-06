<?php
/**
 * Security Helper Functions
 * 
 * Comprehensive security utilities for the location tracking dashboard
 * Includes XSS protection, path traversal prevention, rate limiting, and audit logging
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Load environment variables if not already loaded
if (!function_exists('load_env_file')) {
    function load_env_file($file) {
        if (!file_exists($file)) return;
        $lines = file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            if (strpos($line, '=') !== false) {
                list($key, $value) = explode('=', $line, 2);
                $key = trim($key);
                $value = trim($value);

                // Remove quotes from value if present (restore original db-config.php logic)
                if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') ||
                    (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
                    $value = substr($value, 1, -1);
                }

                if (!empty($key)) {
                    putenv("$key=$value");
                }
            }
        }
    }
}

// Only load environment if not already loaded by another file
if (!getenv('LOC_LOG_DIR') && !getenv('DB_HOST')) {
    load_env_file(__DIR__ . '/../.env');
}



/**
 * XSS Protection Helper
 * 
 * Escapes HTML entities to prevent XSS attacks
 * 
 * @param mixed $s The string to escape
 * @return string The escaped string
 */
function e($s) {
    return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
}

/**
 * Get allowed users from logs directory
 * 
 * @param string $root The logs root directory
 * @return array Array of valid user directory names
 */
function allowedUsers($root) {
    if (!is_dir($root)) {
        return [];
    }
    
    $users = array_values(array_filter(scandir($root), function($d) use ($root) {
        return $d[0] !== '.' && is_dir("$root/$d");
    }));
    
    return $users;
}

/**
 * Validate and sanitize user input for path construction
 * 
 * @param string $root The logs root directory
 * @param string $u The user input to validate
 * @return string The validated path
 * @throws Exception If user is invalid
 */
function assertValidUser($root, $u) {
    // Sanitize user input - only allow alphanumeric, underscore, and dash
    $u = preg_replace('/[^A-Za-z0-9_\-]/', '', $u);
    
    // Check if user exists in allowed users list
    $allowedUsersList = allowedUsers($root);
    $ok = in_array($u, $allowedUsersList, true);
    
    if (!$ok) {
        logSecurityEvent('invalid_user_access_attempt', [
            'attempted_user' => $u,
            'allowed_users' => $allowedUsersList,
            'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
        ]);
        http_response_code(400);
        exit('Invalid user');
    }
    
    return "$root/$u";
}

/**
 * Get allowed users from database
 *
 * @return array Array of valid usernames from database
 */
function getAllowedUsersFromDatabase() {
    try {
        $dbConfigPath = __DIR__ . '/db-config.php';
        if (!file_exists($dbConfigPath)) {
            error_log("Database config file not found: $dbConfigPath");
            return [];
        }

        require_once $dbConfigPath;

        if (!class_exists('DatabaseConfig')) {
            error_log("DatabaseConfig class not found");
            return [];
        }

        $pdo = DatabaseConfig::getInstance()->getConnection();

        $stmt = $pdo->query("SELECT DISTINCT username FROM users ORDER BY username");
        $users = $stmt->fetchAll(PDO::FETCH_COLUMN);

        return $users;
    } catch (Exception $e) {
        error_log("Error getting users from database: " . $e->getMessage());
        return [];
    }
}

/**
 * Validate user against database users
 * 
 * @param string $username The username to validate
 * @return bool True if user is valid
 */
function isValidDatabaseUser($username) {
    $allowedUsers = getAllowedUsersFromDatabase();
    return in_array($username, $allowedUsers, true);
}

/**
 * Security headers setup
 * 
 * Sets comprehensive security headers for dashboard pages
 */
function setSecurityHeaders() {
    // Prevent MIME type sniffing
    header('X-Content-Type-Options: nosniff');
    
    // Prevent framing (clickjacking protection)
    header('X-Frame-Options: DENY');
    
    // XSS protection (legacy browsers)
    header('X-XSS-Protection: 1; mode=block');
    
    // Referrer policy - same origin only
    header('Referrer-Policy: same-origin');
    
    // Permissions policy - disable geolocation for dashboard
    header('Permissions-Policy: geolocation=()');
    
    // Cache control for sensitive pages
    header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
    header('Pragma: no-cache');
    header('Expires: Thu, 01 Jan 1970 00:00:00 GMT');
}

/**
 * Admin action logging
 *
 * @param string $action The action performed
 * @param array $details Additional details about the action
 */
function logAdminAction($action, $details = []) {
    try {
        $logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../logs'), '/');
        $logFile = $logDir . '/admin-actions.log';

        // Ensure log directory exists
        if (!is_dir($logDir)) {
            $created = @mkdir($logDir, 0755, true);
            if (!$created) {
                error_log("Failed to create log directory: $logDir");
                return;
            }
        }

        $entry = [
            'timestamp' => date('c'),
            'action' => $action,
            'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
            'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
            'session_id' => session_id() ?: 'no_session',
            'details' => $details
        ];

        $result = @file_put_contents($logFile, json_encode($entry) . "\n", FILE_APPEND | LOCK_EX);
        if ($result === false) {
            error_log("Failed to write to admin actions log: $logFile");
        }
    } catch (Exception $e) {
        error_log("Error in logAdminAction: " . $e->getMessage());
    }
}

/**
 * Security event logging (reuse existing function if available)
 */
if (!function_exists('logSecurityEvent')) {
    function logSecurityEvent($event, $details = []) {
        try {
            $logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../logs'), '/');
            $logFile = $logDir . '/security.log';

            // Ensure log directory exists
            if (!is_dir($logDir)) {
                $created = @mkdir($logDir, 0755, true);
                if (!$created) {
                    error_log("Failed to create log directory: $logDir");
                    return;
                }
            }

            $entry = [
                'timestamp' => date('c'),
                'event' => $event,
                'endpoint' => basename($_SERVER['SCRIPT_NAME'] ?? 'unknown'),
                'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
                'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
                'details' => $details
            ];

            $result = @file_put_contents($logFile, json_encode($entry) . "\n", FILE_APPEND | LOCK_EX);
            if ($result === false) {
                error_log("Failed to write to security log: $logFile");
            }
        } catch (Exception $e) {
            error_log("Error in logSecurityEvent: " . $e->getMessage());
        }
    }
}

/**
 * Admin rate limiting
 * 
 * @param string $action The action being performed
 * @param int $maxPerHour Maximum actions per hour per IP
 * @return bool True if within limits, false if exceeded
 */
function checkAdminRateLimit($action, $maxPerHour = 100) {
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $identifier = $ip . '_' . $action;
    
    $logDir = rtrim(getenv('LOC_LOG_DIR') ?: (__DIR__ . '/../logs'), '/');
    $rateLimitFile = $logDir . '/admin-rate-limits.json';
    
    // Ensure log directory exists
    @mkdir($logDir, 0755, true);
    
    // Load existing limits
    $limits = [];
    if (file_exists($rateLimitFile)) {
        $content = @file_get_contents($rateLimitFile);
        if ($content !== false) {
            $limits = json_decode($content, true) ?: [];
        }
    }
    
    // Clean old entries (older than 1 hour)
    $currentTime = time();
    $hourAgo = $currentTime - 3600;
    
    foreach ($limits as $key => $data) {
        if ($data['window'] < $hourAgo) {
            unset($limits[$key]);
        }
    }
    
    // Get current hour window
    $hourWindow = floor($currentTime / 3600) * 3600;
    $key = $identifier . '_' . $hourWindow;
    
    // Check current limit
    $currentCount = $limits[$key]['count'] ?? 0;
    
    if ($currentCount >= $maxPerHour) {
        logSecurityEvent('admin_rate_limit_exceeded', [
            'action' => $action,
            'ip' => $ip,
            'current_count' => $currentCount,
            'max_per_hour' => $maxPerHour
        ]);
        return false;
    }
    
    // Increment counter
    $limits[$key] = [
        'count' => $currentCount + 1,
        'window' => $hourWindow
    ];
    
    // Save limits
    @file_put_contents($rateLimitFile, json_encode($limits), LOCK_EX);
    
    return true;
}

/**
 * Require admin rate limit check
 * 
 * @param string $action The action being performed
 * @param int $maxPerHour Maximum actions per hour per IP
 */
function requireAdminRateLimit($action, $maxPerHour = 100) {
    if (!checkAdminRateLimit($action, $maxPerHour)) {
        http_response_code(429);
        header('Retry-After: 3600');
        
        if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
            // AJAX request
            header('Content-Type: application/json');
            echo json_encode([
                'success' => false,
                'error' => 'Rate limit exceeded. Please try again later.',
                'retry_after' => 3600
            ]);
        } else {
            // Regular request
            echo '<h1>Rate Limit Exceeded</h1><p>Too many requests. Please try again later.</p>';
        }
        exit;
    }
}

/**
 * Content Security Policy header for dashboard
 * 
 * @param bool $allowInlineScripts Whether to allow inline scripts (for pages that need it)
 */
function setContentSecurityPolicy($allowInlineScripts = false) {
    $scriptSrc = $allowInlineScripts
        ? "'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com"
        : "'self' https://unpkg.com https://cdnjs.cloudflare.com";

    $csp = "default-src 'self'; " .
           "script-src $scriptSrc; " .
           "style-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com; " .
           "font-src 'self' https://cdnjs.cloudflare.com; " .
           "img-src 'self' data: https:; " .
           "connect-src 'self' https://unpkg.com https://cdnjs.cloudflare.com; " .
           "frame-ancestors 'none';";

    header("Content-Security-Policy: $csp");
}
