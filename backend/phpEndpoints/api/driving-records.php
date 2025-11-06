<?php
/**
 * Driving Records Endpoint
 * 
 * GET /api/driving-records.php
 * 
 * Returns driving records with filtering options.
 * 
 * Filters:
 * - user: Filter by username
 * - date_from: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
 * - date_to: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
 * - event_type: Filter by event type (start, data, stop)
 * - trip_id: Filter by specific trip ID
 * - limit: Maximum records to return (default 1000, max 10000)
 * - offset: Pagination offset (default 0)
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Include required files
require_once __DIR__ . '/../shared/logging.php';
require_once __DIR__ . '/../shared/classes/ApiResponse.php';
require_once __DIR__ . '/../db-config.php';
require_once __DIR__ . '/middleware/authentication.php';

// Generate unique request ID
$requestId = uniqid('driving_', true);
$GLOBALS['requestId'] = $requestId;

// Set CORS headers
ApiResponse::setCorsHeaders();

// Handle OPTIONS request
ApiResponse::handleOptionsRequest(['GET', 'OPTIONS']);

// Only allow GET
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    ApiResponse::methodNotAllowed(['GET']);
}

// Authenticate request
if (!authenticateRequest()) {
    ApiResponse::unauthorized('Valid API token required');
}

// Rate limiting
if (!checkRateLimit($_SERVER['REMOTE_ADDR'] ?? 'unknown', 1000)) {
    ApiResponse::rateLimitExceeded('Rate limit exceeded. Maximum 1000 requests per hour.');
}

try {
    // Check if database mode is enabled
    if (!DatabaseConfig::isDatabaseMode()) {
        ApiResponse::error('Database mode is not enabled. This endpoint requires database mode.', 503);
    }
    
    // Get database connection
    $db = DatabaseConfig::getInstance();
    if (!$db->testConnection() || !$db->tablesExist()) {
        ApiResponse::error('Database is not available', 503);
    }
    
    $pdo = $db->getConnection();
    
    // Get query parameters
    $user = $_GET['user'] ?? null;
    $dateFrom = $_GET['date_from'] ?? null;
    $dateTo = $_GET['date_to'] ?? null;
    $eventType = $_GET['event_type'] ?? null;
    $tripId = $_GET['trip_id'] ?? null;
    $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 1000;
    $offset = isset($_GET['offset']) ? (int)$_GET['offset'] : 0;
    
    // Validate limit
    if ($limit < 1 || $limit > 10000) {
        ApiResponse::error('Limit must be between 1 and 10000', 400);
    }
    
    // Validate offset
    if ($offset < 0) {
        ApiResponse::error('Offset must be non-negative', 400);
    }
    
    // Validate event_type
    if ($eventType && !in_array($eventType, ['start', 'data', 'stop'])) {
        ApiResponse::error('Invalid event_type. Must be: start, data, or stop', 400);
    }
    
    // Build query
    $sql = "
        SELECT dr.*, u.username, u.display_name
        FROM driving_records dr
        JOIN users u ON dr.user_id = u.id
        WHERE 1=1
    ";
    
    $params = [];
    
    // Apply filters
    if ($user) {
        $sql .= " AND u.username = ?";
        $params[] = $user;
    }
    
    if ($dateFrom) {
        $sql .= " AND dr.server_time >= ?";
        $params[] = $dateFrom;
    }
    
    if ($dateTo) {
        $sql .= " AND dr.server_time <= ?";
        $params[] = $dateTo;
    }
    
    if ($eventType) {
        $sql .= " AND dr.event_type = ?";
        $params[] = $eventType;
    }
    
    if ($tripId) {
        $sql .= " AND dr.trip_id = ?";
        $params[] = $tripId;
    }
    
    // Order by server_time descending (most recent first)
    $sql .= " ORDER BY dr.server_time DESC";
    
    // Add pagination
    $sql .= " LIMIT ? OFFSET ?";
    $params[] = $limit;
    $params[] = $offset;
    
    // Execute query
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $drivingRecords = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Get total count (without pagination)
    $countSql = "
        SELECT COUNT(*) 
        FROM driving_records dr 
        JOIN users u ON dr.user_id = u.id 
        WHERE 1=1
    ";
    $countParams = [];
    
    if ($user) {
        $countSql .= " AND u.username = ?";
        $countParams[] = $user;
    }
    
    if ($dateFrom) {
        $countSql .= " AND dr.server_time >= ?";
        $countParams[] = $dateFrom;
    }
    
    if ($dateTo) {
        $countSql .= " AND dr.server_time <= ?";
        $countParams[] = $dateTo;
    }
    
    if ($eventType) {
        $countSql .= " AND dr.event_type = ?";
        $countParams[] = $eventType;
    }
    
    if ($tripId) {
        $countSql .= " AND dr.trip_id = ?";
        $countParams[] = $tripId;
    }
    
    $countStmt = $pdo->prepare($countSql);
    $countStmt->execute($countParams);
    $total = (int)$countStmt->fetchColumn();
    
    // Log successful request
    logApiRequest('driving-records', [
        'count' => count($drivingRecords),
        'total' => $total,
        'user' => $user,
        'date_from' => $dateFrom,
        'date_to' => $dateTo,
        'event_type' => $eventType,
        'trip_id' => $tripId,
        'limit' => $limit,
        'offset' => $offset,
        'request_id' => $requestId
    ]);
    
    // Return response
    ApiResponse::success([
        'driving_records' => $drivingRecords,
        'count' => count($drivingRecords),
        'total' => $total,
        'limit' => $limit,
        'offset' => $offset,
        'source' => 'database'
    ], 'Driving records retrieved successfully');
    
} catch (PDOException $e) {
    // Database errors
    error_log("Driving records endpoint database error: " . $e->getMessage());
    ApiResponse::error('Database error occurred', 500, [
        'request_id' => $requestId,
        'error_type' => 'database_error'
    ]);
    
} catch (Exception $e) {
    // General errors
    error_log("Driving records endpoint error: " . $e->getMessage());
    ApiResponse::error('An error occurred while retrieving driving records', 500, [
        'request_id' => $requestId,
        'error_type' => 'general_error'
    ]);
}

