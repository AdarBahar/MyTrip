<?php
/**
 * Locations Endpoint
 * 
 * GET /api/locations.php
 * 
 * Returns location records with comprehensive filtering options.
 * 
 * Filters:
 * - user: Filter by username
 * - date_from: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
 * - date_to: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
 * - accuracy_max: Maximum accuracy in meters
 * - anomaly_status: Filter by anomaly status (marked, suspected, normal)
 * - lat, lng, radius: Geographic radius search (radius in meters, default 100)
 * - limit: Maximum records to return (default 1000, max 10000)
 * - offset: Pagination offset (default 0)
 * - include_anomaly_status: Include anomaly information (default true)
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
$requestId = uniqid('locations_', true);
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
    $accuracyMax = isset($_GET['accuracy_max']) ? (float)$_GET['accuracy_max'] : null;
    $anomalyStatus = $_GET['anomaly_status'] ?? null;
    $lat = isset($_GET['lat']) ? (float)$_GET['lat'] : null;
    $lng = isset($_GET['lng']) ? (float)$_GET['lng'] : null;
    $radius = isset($_GET['radius']) ? (float)$_GET['radius'] : 100;
    $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 1000;
    $offset = isset($_GET['offset']) ? (int)$_GET['offset'] : 0;
    $includeAnomalyStatus = filter_var($_GET['include_anomaly_status'] ?? 'true', FILTER_VALIDATE_BOOLEAN);
    
    // Validate limit
    if ($limit < 1 || $limit > 10000) {
        ApiResponse::error('Limit must be between 1 and 10000', 400);
    }
    
    // Validate offset
    if ($offset < 0) {
        ApiResponse::error('Offset must be non-negative', 400);
    }
    
    // Validate anomaly_status
    if ($anomalyStatus && !in_array($anomalyStatus, ['marked', 'suspected', 'normal', 'confirmed'])) {
        ApiResponse::error('Invalid anomaly_status. Must be: marked, suspected, normal, or confirmed', 400);
    }
    
    // Validate geographic search parameters
    if (($lat !== null || $lng !== null) && ($lat === null || $lng === null)) {
        ApiResponse::error('Both lat and lng are required for geographic search', 400);
    }
    
    // Build query
    $sql = "
        SELECT lr.*, u.username, u.display_name
    ";
    
    if ($includeAnomalyStatus) {
        $sql .= ",
               CASE WHEN as_lr.status IS NOT NULL THEN as_lr.status ELSE 'normal' END as anomaly_status,
               CASE WHEN as_lr.marked_by_user = 1 THEN 1 ELSE 0 END as marked_by_user
        ";
    }
    
    $sql .= "
        FROM location_records lr
        JOIN users u ON lr.user_id = u.id
    ";
    
    if ($includeAnomalyStatus) {
        $sql .= "
        LEFT JOIN anomaly_status as_lr ON (
            as_lr.record_type = 'location' AND 
            (as_lr.record_id = lr.id OR as_lr.legacy_unique_id = lr.legacy_unique_id)
        )
        ";
    }
    
    $sql .= " WHERE 1=1";
    
    $params = [];
    
    // Apply filters
    if ($user) {
        $sql .= " AND u.username = ?";
        $params[] = $user;
    }
    
    if ($dateFrom) {
        $sql .= " AND lr.server_time >= ?";
        $params[] = $dateFrom;
    }
    
    if ($dateTo) {
        $sql .= " AND lr.server_time <= ?";
        $params[] = $dateTo;
    }
    
    if ($accuracyMax !== null) {
        $sql .= " AND lr.accuracy <= ?";
        $params[] = $accuracyMax;
    }
    
    if ($anomalyStatus) {
        if ($anomalyStatus === 'marked') {
            $sql .= " AND as_lr.marked_by_user = 1";
        } elseif ($anomalyStatus === 'normal') {
            $sql .= " AND (as_lr.status IS NULL OR as_lr.status = 'normal')";
        } else {
            $sql .= " AND as_lr.status = ?";
            $params[] = $anomalyStatus;
        }
    }
    
    // Geographic radius search using Haversine formula
    if ($lat !== null && $lng !== null) {
        $sql .= " AND (
            6371000 * acos(
                cos(radians(?)) * cos(radians(lr.latitude)) * 
                cos(radians(lr.longitude) - radians(?)) + 
                sin(radians(?)) * sin(radians(lr.latitude))
            ) <= ?
        )";
        $params[] = $lat;
        $params[] = $lng;
        $params[] = $lat;
        $params[] = $radius;
    }
    
    // Order by server_time descending (most recent first)
    $sql .= " ORDER BY lr.server_time DESC";
    
    // Add pagination
    $sql .= " LIMIT ? OFFSET ?";
    $params[] = $limit;
    $params[] = $offset;
    
    // Execute query
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $locations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Get total count (without pagination)
    $countSql = "SELECT COUNT(*) FROM location_records lr JOIN users u ON lr.user_id = u.id";
    
    if ($includeAnomalyStatus && $anomalyStatus) {
        $countSql .= " LEFT JOIN anomaly_status as_lr ON (
            as_lr.record_type = 'location' AND 
            (as_lr.record_id = lr.id OR as_lr.legacy_unique_id = lr.legacy_unique_id)
        )";
    }
    
    $countSql .= " WHERE 1=1";
    $countParams = [];
    
    if ($user) {
        $countSql .= " AND u.username = ?";
        $countParams[] = $user;
    }
    
    if ($dateFrom) {
        $countSql .= " AND lr.server_time >= ?";
        $countParams[] = $dateFrom;
    }
    
    if ($dateTo) {
        $countSql .= " AND lr.server_time <= ?";
        $countParams[] = $dateTo;
    }
    
    if ($accuracyMax !== null) {
        $countSql .= " AND lr.accuracy <= ?";
        $countParams[] = $accuracyMax;
    }
    
    if ($anomalyStatus) {
        if ($anomalyStatus === 'marked') {
            $countSql .= " AND as_lr.marked_by_user = 1";
        } elseif ($anomalyStatus === 'normal') {
            $countSql .= " AND (as_lr.status IS NULL OR as_lr.status = 'normal')";
        } else {
            $countSql .= " AND as_lr.status = ?";
            $countParams[] = $anomalyStatus;
        }
    }
    
    if ($lat !== null && $lng !== null) {
        $countSql .= " AND (
            6371000 * acos(
                cos(radians(?)) * cos(radians(lr.latitude)) * 
                cos(radians(lr.longitude) - radians(?)) + 
                sin(radians(?)) * sin(radians(lr.latitude))
            ) <= ?
        )";
        $countParams[] = $lat;
        $countParams[] = $lng;
        $countParams[] = $lat;
        $countParams[] = $radius;
    }
    
    $countStmt = $pdo->prepare($countSql);
    $countStmt->execute($countParams);
    $total = (int)$countStmt->fetchColumn();
    
    // Log successful request
    logApiRequest('locations', [
        'count' => count($locations),
        'total' => $total,
        'user' => $user,
        'date_from' => $dateFrom,
        'date_to' => $dateTo,
        'limit' => $limit,
        'offset' => $offset,
        'request_id' => $requestId
    ]);
    
    // Return response
    ApiResponse::success([
        'locations' => $locations,
        'count' => count($locations),
        'total' => $total,
        'limit' => $limit,
        'offset' => $offset,
        'source' => 'database'
    ], 'Locations retrieved successfully');
    
} catch (PDOException $e) {
    // Database errors
    error_log("Locations endpoint database error: " . $e->getMessage());
    ApiResponse::error('Database error occurred', 500, [
        'request_id' => $requestId,
        'error_type' => 'database_error'
    ]);
    
} catch (Exception $e) {
    // General errors
    error_log("Locations endpoint error: " . $e->getMessage());
    ApiResponse::error('An error occurred while retrieving locations', 500, [
        'request_id' => $requestId,
        'error_type' => 'general_error'
    ]);
}

