<?php
/**
 * API Endpoints Test Script
 * 
 * Comprehensive testing script for all API endpoints
 * Can be run from command line or browser
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Set content type
if (php_sapi_name() !== 'cli') {
    header('Content-Type: application/json; charset=utf-8');
}

// Load environment
require_once __DIR__ . '/../shared/db-config.php';

/**
 * Test API endpoint
 */
function testEndpoint($url, $method = 'GET', $data = null, $headers = []) {
    $ch = curl_init();
    
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_USERAGENT => 'LocationAPI-Test/1.0'
    ]);
    
    if ($data && in_array($method, ['POST', 'PUT', 'PATCH'])) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, is_array($data) ? json_encode($data) : $data);
    }
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    return [
        'http_code' => $httpCode,
        'response' => $response,
        'error' => $error,
        'success' => $httpCode >= 200 && $httpCode < 300
    ];
}

/**
 * Run all tests
 */
function runTests($baseUrl) {
    $results = [];
    $token = getenv('LOC_API_TOKEN') ?: '4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI=';
    
    $tests = [
        'ping' => [
            'url' => $baseUrl . '/ping.php',
            'method' => 'GET',
            'expected_code' => 200
        ],
        'health' => [
            'url' => $baseUrl . '/health.php',
            'method' => 'GET',
            'expected_code' => 200
        ],
        'index' => [
            'url' => $baseUrl . '/',
            'method' => 'GET',
            'expected_code' => 200
        ],
        'location_no_auth' => [
            'url' => $baseUrl . '/getloc.php',
            'method' => 'POST',
            'data' => [
                'id' => 'test-device',
                'name' => 'test_user',
                'latitude' => 32.0853,
                'longitude' => 34.7818
            ],
            'headers' => ['Content-Type: application/json'],
            'expected_code' => 401
        ],
        'location_with_auth' => [
            'url' => $baseUrl . '/getloc.php',
            'method' => 'POST',
            'data' => [
                'id' => 'test-device',
                'name' => 'test_user',
                'latitude' => 32.0853,
                'longitude' => 34.7818,
                'accuracy' => 5.0,
                'timestamp' => time() * 1000
            ],
            'headers' => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $token
            ],
            'expected_code' => 200
        ]
    ];
    
    foreach ($tests as $testName => $test) {
        $result = testEndpoint(
            $test['url'],
            $test['method'],
            $test['data'] ?? null,
            $test['headers'] ?? []
        );
        
        $results[$testName] = [
            'test' => $test,
            'result' => $result,
            'passed' => $result['http_code'] === $test['expected_code']
        ];
    }
    
    return $results;
}

// Main execution
$baseUrl = $_GET['base_url'] ?? 'http://localhost:8888/location/api';

if (isset($_GET['test'])) {
    $results = runTests($baseUrl);
    
    $summary = [
        'base_url' => $baseUrl,
        'timestamp' => date('c'),
        'total_tests' => count($results),
        'passed' => array_sum(array_column($results, 'passed')),
        'failed' => count($results) - array_sum(array_column($results, 'passed')),
        'results' => $results
    ];
    
    if (php_sapi_name() === 'cli') {
        echo "API Test Results\n";
        echo "================\n";
        echo "Base URL: {$summary['base_url']}\n";
        echo "Total Tests: {$summary['total_tests']}\n";
        echo "Passed: {$summary['passed']}\n";
        echo "Failed: {$summary['failed']}\n\n";
        
        foreach ($results as $testName => $result) {
            $status = $result['passed'] ? 'PASS' : 'FAIL';
            echo "[{$status}] {$testName}: HTTP {$result['result']['http_code']}\n";
            if (!$result['passed']) {
                echo "  Expected: {$result['test']['expected_code']}\n";
                echo "  Response: " . substr($result['result']['response'], 0, 100) . "\n";
            }
        }
    } else {
        echo json_encode($summary, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    }
} else {
    // Show test interface
    if (php_sapi_name() !== 'cli') {
        echo json_encode([
            'message' => 'API Test Script',
            'usage' => [
                'run_tests' => $baseUrl . '/test-endpoints.php?test=1',
                'test_production' => $baseUrl . '/test-endpoints.php?test=1&base_url=https://www.bahar.co.il/location/api',
                'test_localhost' => $baseUrl . '/test-endpoints.php?test=1&base_url=http://localhost:8888/location/api'
            ]
        ], JSON_PRETTY_PRINT);
    } else {
        echo "Usage: php test-endpoints.php [base_url]\n";
        echo "Example: php test-endpoints.php https://www.bahar.co.il/location/api\n";
    }
}
?>
