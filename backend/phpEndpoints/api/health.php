<?php
/**
 * Health Check Endpoint
 * 
 * Simple health check endpoint that should bypass ModSecurity
 * Provides basic system status without complex headers or content
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Simple headers to avoid ModSecurity triggers
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Pragma: no-cache');
header('Expires: 0');

// Handle OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Allow: GET, OPTIONS');
    http_response_code(200);
    exit;
}

// Only allow GET requests
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Basic health check
$health = [
    'status' => 'ok',
    'timestamp' => date('c'),
    'version' => '2.0.0',
    'php_version' => PHP_VERSION,
    'server_time' => time()
];

// Check if we can write to logs directory
$logDir = __DIR__ . '/../logs';
if (is_dir($logDir) && is_writable($logDir)) {
    $health['logs'] = 'writable';
} else {
    $health['logs'] = 'not_writable';
}

// Check database connection (simple)
try {
    require_once __DIR__ . '/../shared/db-config.php';
    if (DatabaseConfig::isDatabaseMode()) {
        $pdo = DatabaseConfig::getInstance()->getConnection();
        $stmt = $pdo->query('SELECT 1');
        $health['database'] = 'connected';
    } else {
        $health['database'] = 'file_mode';
    }
} catch (Exception $e) {
    $health['database'] = 'error';
}

echo json_encode($health, JSON_UNESCAPED_SLASHES);
?>
