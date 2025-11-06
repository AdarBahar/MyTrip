<?php
/**
 * Simple Ping Endpoint
 *
 * Minimal endpoint to test basic connectivity
 * Designed to bypass ModSecurity restrictions
 *
 * @version 1.0
 * @author Adar Bahar
 */

// Check if running from CLI
$isCli = php_sapi_name() === 'cli';

if (!$isCli) {
    // Minimal headers to avoid triggering ModSecurity
    header('Content-Type: text/plain; charset=utf-8');

    // Handle OPTIONS
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
        header('Allow: GET, OPTIONS');
        http_response_code(200);
        exit;
    }

    // Only allow GET
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
        http_response_code(405);
        echo 'Method Not Allowed';
        exit;
    }
}

// Simple response
echo 'pong';
?>
