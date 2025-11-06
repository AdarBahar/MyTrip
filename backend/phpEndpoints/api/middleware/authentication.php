<?php
/**
 * API Authentication Middleware
 *
 * Handles authentication for API endpoints using Bearer tokens or API keys
 * Supports multiple authentication methods with proper security logging
 *
 * @version 2.0
 * @author Adar Bahar
 */

/**
 * Authenticate API request
 * 
 * @return bool True if authenticated, false otherwise
 */
function authenticateRequest() {
    // Get authentication token from various sources
    $token = getAuthToken();

    if (!$token) {
        if (function_exists('logSecurityEvent')) {
            logSecurityEvent('auth_missing', ['reason' => 'No authentication token provided']);
        }
        return false;
    }

    // Validate token
    if (validateToken($token)) {
        if (function_exists('logSecurityEvent')) {
            logSecurityEvent('auth_success', ['token_type' => getTokenType()]);
        }
        return true;
    } else {
        if (function_exists('logSecurityEvent')) {
            logSecurityEvent('auth_failure', ['reason' => 'Invalid token', 'token_preview' => substr($token, 0, 8) . '...']);
        }
        return false;
    }
}

/**
 * Get authentication token from request headers
 *
 * @return string|null The authentication token or null if not found
 */
function getAuthToken() {
    // Check Authorization header (Bearer token) - multiple sources
    $authHeader = '';

    // Method 1: Standard $_SERVER['HTTP_AUTHORIZATION']
    if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
        $authHeader = $_SERVER['HTTP_AUTHORIZATION'];
    }
    // Method 2: Alternative $_SERVER key
    elseif (isset($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
        $authHeader = $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];
    }
    // Method 3: getallheaders() function
    elseif (function_exists('getallheaders')) {
        $headers = getallheaders();
        if (isset($headers['Authorization'])) {
            $authHeader = $headers['Authorization'];
        } elseif (isset($headers['authorization'])) {
            $authHeader = $headers['authorization'];
        }
    }

    // Method 4: Check for custom header that bypasses ModSecurity (PRIORITY)
    if (isset($_SERVER['HTTP_X_AUTH_TOKEN'])) {
        // Custom header to bypass ModSecurity - treat as Bearer token
        return trim($_SERVER['HTTP_X_AUTH_TOKEN']);
    }

    // Parse Bearer token from Authorization header
    if ($authHeader && preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
        return trim($matches[1]);
    }

    // Fallback: Check X-API-Token header (for backward compatibility)
    if (isset($_SERVER['HTTP_X_API_TOKEN'])) {
        return trim($_SERVER['HTTP_X_API_TOKEN']);
    }

    // Check Authorization header for API key format
    if ($authHeader && preg_match('/ApiKey\s+(.*)$/i', $authHeader, $matches)) {
        return trim($matches[1]);
    }

    // Check query parameter (less secure, for testing only)
    if (isset($_GET['api_token'])) {
        return trim($_GET['api_token']);
    }

    return null;
}

/**
 * Get the type of token being used
 *
 * @return string The token type
 */
function getTokenType() {
    $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';

    // Check for Bearer token first (priority)
    if (preg_match('/Bearer\s+/i', $authHeader)) {
        return 'bearer';
    }

    // Check for custom auth header (ModSecurity bypass)
    if (isset($_SERVER['HTTP_X_AUTH_TOKEN'])) {
        return 'bearer'; // Treat as bearer token
    }

    // Fallback to API key methods
    if (isset($_SERVER['HTTP_X_API_TOKEN'])) {
        return 'api_key';
    }

    if (preg_match('/ApiKey\s+/i', $authHeader)) {
        return 'api_key';
    }

    if (isset($_GET['api_token'])) {
        return 'query_param';
    }

    return 'unknown';
}

/**
 * Validate authentication token
 * 
 * @param string $token The token to validate
 * @return bool True if valid, false otherwise
 */
function validateToken($token) {
    // Load valid tokens from environment or configuration
    $validTokens = getValidTokens();
    
    // Check if token exists in valid tokens list
    if (in_array($token, $validTokens)) {
        return true;
    }
    
    // Check if it's a JWT token (for future implementation)
    if (isJwtToken($token)) {
        return validateJwtToken($token);
    }
    
    return false;
}

/**
 * Get list of valid API tokens
 * 
 * @return array Array of valid tokens
 */
function getValidTokens() {
    // Load environment variables from .env file if not already loaded
    if (!getenv('LOC_API_TOKEN')) {
        require_once __DIR__ . '/../../shared/db-config.php';
    }

    // Load from environment variables
    $envTokens = [];

    // Primary API token (LOC_API_TOKEN from .env file)
    if ($token = getenv('LOC_API_TOKEN')) {
        $envTokens[] = $token;
    }

    // Fallback to API_TOKEN for backward compatibility
    if ($token = getenv('API_TOKEN')) {
        $envTokens[] = $token;
    }

    // Additional API tokens (comma-separated)
    if ($tokens = getenv('API_TOKENS')) {
        $additionalTokens = array_map('trim', explode(',', $tokens));
        $envTokens = array_merge($envTokens, $additionalTokens);
    }
    
    // Load from configuration file if exists
    $configFile = __DIR__ . '/../config/api-tokens.json';
    if (file_exists($configFile)) {
        $content = file_get_contents($configFile);
        $config = json_decode($content, true);
        
        if (is_array($config) && isset($config['tokens'])) {
            $envTokens = array_merge($envTokens, $config['tokens']);
        }
    }
    
    // Default tokens for development (should be removed in production)
    if (empty($envTokens) && (getenv('ENVIRONMENT') === 'development' || getenv('APP_ENV') === 'dev')) {
        $envTokens = [
            'dev-token-12345',
            'test-api-key-67890'
        ];
    }
    
    return array_unique($envTokens);
}

/**
 * Check if token is a JWT token
 * 
 * @param string $token The token to check
 * @return bool True if it's a JWT token
 */
function isJwtToken($token) {
    // JWT tokens have 3 parts separated by dots
    $parts = explode('.', $token);
    return count($parts) === 3;
}

/**
 * Validate JWT token (placeholder for future implementation)
 * 
 * @param string $token The JWT token to validate
 * @return bool True if valid, false otherwise
 */
function validateJwtToken($token) {
    // TODO: Implement JWT validation
    // This would include:
    // - Signature verification
    // - Expiration check
    // - Issuer validation
    // - Audience validation
    
    return false; // Not implemented yet
}

/**
 * Get user information from token (for future use)
 * 
 * @param string $token The authentication token
 * @return array|null User information or null if not available
 */
function getUserFromToken($token) {
    // For simple API keys, we might not have user info
    // For JWT tokens, we could decode the payload
    
    if (isJwtToken($token)) {
        // TODO: Decode JWT payload and extract user info
        return null;
    }
    
    // For API keys, we might have a mapping file
    $mappingFile = __DIR__ . '/../config/token-users.json';
    if (file_exists($mappingFile)) {
        $content = file_get_contents($mappingFile);
        $mapping = json_decode($content, true);
        
        if (isset($mapping[$token])) {
            return $mapping[$token];
        }
    }
    
    return null;
}

/**
 * Check if request is from allowed IP
 * 
 * @return bool True if IP is allowed, false otherwise
 */
function checkIpWhitelist() {
    $allowedIps = getenv('ALLOWED_IPS');
    
    if (!$allowedIps) {
        return true; // No IP restriction
    }
    
    $clientIp = $_SERVER['REMOTE_ADDR'] ?? '';
    $allowedList = array_map('trim', explode(',', $allowedIps));
    
    // Check for exact match or CIDR range
    foreach ($allowedList as $allowedIp) {
        if ($clientIp === $allowedIp) {
            return true;
        }
        
        // Check CIDR range (basic implementation)
        if (strpos($allowedIp, '/') !== false) {
            if (ipInRange($clientIp, $allowedIp)) {
                return true;
            }
        }
    }
    
    if (function_exists('logSecurityEvent')) {
        logSecurityEvent('ip_blocked', ['client_ip' => $clientIp, 'allowed_ips' => $allowedList]);
    }
    return false;
}

/**
 * Check if IP is in CIDR range
 * 
 * @param string $ip The IP to check
 * @param string $cidr The CIDR range
 * @return bool True if IP is in range
 */
function ipInRange($ip, $cidr) {
    list($subnet, $mask) = explode('/', $cidr);
    
    if ((ip2long($ip) & ~((1 << (32 - $mask)) - 1)) == ip2long($subnet)) {
        return true;
    }
    
    return false;
}

/**
 * Rate limiting check with improved error handling
 *
 * @param string $identifier The identifier for rate limiting (IP, token, etc.)
 * @param int $maxRequests Maximum requests per hour
 * @return bool True if within limits, false if exceeded
 */
function checkRateLimit($identifier = null, $maxRequests = 1000) {
    if (!$identifier) {
        $identifier = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    }

    // Ensure logs directory exists
    $logDir = __DIR__ . '/../logs';
    if (!is_dir($logDir)) {
        @mkdir($logDir, 0755, true);
    }

    $rateLimitFile = $logDir . '/rate_limits.json';
    $limits = [];

    // Read existing limits with error handling
    if (file_exists($rateLimitFile)) {
        $content = @file_get_contents($rateLimitFile);
        if ($content !== false) {
            $decoded = json_decode($content, true);
            $limits = is_array($decoded) ? $decoded : [];
        }
    }

    $now = time();
    $hourWindow = floor($now / 3600);
    $key = $identifier . '_' . $hourWindow;

    // Clean old entries (keep only current and previous hour)
    $keysToRemove = [];
    foreach ($limits as $k => $v) {
        if (strpos($k, '_') !== false) {
            $parts = explode('_', $k);
            if (count($parts) >= 2) {
                $window = (int)$parts[count($parts) - 1];
                if ($window < $hourWindow - 1) {
                    $keysToRemove[] = $k;
                }
            }
        }
    }

    foreach ($keysToRemove as $k) {
        unset($limits[$k]);
    }

    // Check current limit
    $currentCount = $limits[$key] ?? 0;

    if ($currentCount >= $maxRequests) {
        if (function_exists('logSecurityEvent')) {
            logSecurityEvent('rate_limit_exceeded', [
                'identifier' => $identifier,
                'current_count' => $currentCount,
                'max_requests' => $maxRequests,
                'window' => $hourWindow
            ]);
        }
        return false;
    }

    // Increment counter
    $limits[$key] = $currentCount + 1;

    // Save limits with error handling
    $success = @file_put_contents($rateLimitFile, json_encode($limits, JSON_UNESCAPED_SLASHES), LOCK_EX);
    if ($success === false) {
        error_log("Failed to write rate limit file: $rateLimitFile");
    }

    return true;
}

/**
 * Enhanced authentication with multiple checks
 * 
 * @return bool True if all authentication checks pass
 */
function authenticateRequestEnhanced() {
    // Check IP whitelist if configured
    if (!checkIpWhitelist()) {
        return false;
    }
    
    // Check rate limits
    if (!checkRateLimit()) {
        return false;
    }
    
    // Check authentication token
    return authenticateRequest();
}
?>
