<?php
/**
 * Database Configuration Helper
 * 
 * Provides database connection management for the location tracking system
 * Supports both log file and MySQL database storage modes
 * 
 * @version 1.0
 * @author Adar Bahar
 */

// Load environment variables using the function from security-helpers.php
require_once __DIR__ . '/security-helpers.php';

// Load environment variables if not already loaded
if (!getenv('LOC_API_TOKEN')) {
    // Try multiple possible locations for .env file
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
 * Database Configuration Class
 */
class DatabaseConfig {
    private static $instance = null;
    private $pdo = null;
    private $config = [];
    
    private function __construct() {
        $this->loadConfig();
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function loadConfig() {
        $this->config = [
            'host' => getenv('DB_HOST') ?: 'localhost',
            'port' => getenv('DB_PORT') ?: '3306',
            'database' => getenv('DB_NAME') ?: 'location_tracking',
            'username' => getenv('DB_USER') ?: 'location_user',
            'password' => getenv('DB_PASS') ?: '',
            'charset' => getenv('DB_CHARSET') ?: 'utf8mb4',
            'collation' => getenv('DB_COLLATION') ?: 'utf8mb4_unicode_ci',
            'timeout' => (int)(getenv('DB_TIMEOUT') ?: 30),
            'persistent' => filter_var(getenv('DB_PERSISTENT') ?: 'false', FILTER_VALIDATE_BOOLEAN)
        ];
    }
    
    /**
     * Get database connection
     */
    public function getConnection() {
        if ($this->pdo === null) {
            $this->connect();
        }
        return $this->pdo;
    }

    /**
     * Establish database connection
     */
    private function connect() {
        $dsn = sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=%s',
            $this->config['host'],
            $this->config['port'],
            $this->config['database'],
            $this->config['charset']
        );

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_TIMEOUT => $this->config['timeout'],
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES {$this->config['charset']} COLLATE {$this->config['collation']}"
        ];

        if ($this->config['persistent']) {
            $options[PDO::ATTR_PERSISTENT] = true;
        }

        try {
            $this->pdo = new PDO($dsn, $this->config['username'], $this->config['password'], $options);
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw new Exception("Database connection failed. Please check your configuration.");
        }
    }

    /**
     * Reset the connection (force reconnect on next getConnection call)
     * Useful for long-running processes that need to recover from connection loss
     */
    public function resetConnection() {
        $this->pdo = null;
    }

    /**
     * Force a new connection (close old one if exists and create new)
     */
    public function reconnect() {
        $this->pdo = null;
        return $this->getConnection();
    }
    
    /**
     * Test database connection
     */
    public function testConnection() {
        try {
            $pdo = $this->getConnection();
            $stmt = $pdo->query('SELECT 1');
            return $stmt !== false;
        } catch (Exception $e) {
            return false;
        }
    }
    
    /**
     * Check if database tables exist
     */
    public function tablesExist() {
        try {
            $pdo = $this->getConnection();
            $stmt = $pdo->prepare("
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = ? 
                AND table_name IN ('users', 'devices', 'location_records', 'driving_records', 'anomaly_detections', 'anomaly_status')
            ");
            $stmt->execute([$this->config['database']]);
            $result = $stmt->fetch();
            return $result['table_count'] >= 6;
        } catch (Exception $e) {
            return false;
        }
    }
    
    /**
     * Get database configuration (without password)
     */
    public function getConfig() {
        $config = $this->config;
        unset($config['password']);
        return $config;
    }
    
    /**
     * Check if MySQL database mode is enabled
     */
    public static function isDatabaseMode() {
        return !empty(getenv('DB_NAME')) && !empty(getenv('DB_USER'));
    }
    
    /**
     * Get storage mode (database or file)
     */
    public static function getStorageMode() {
        return self::isDatabaseMode() ? 'database' : 'file';
    }
}

/**
 * Helper function to get database connection
 */
function getDatabase() {
    return DatabaseConfig::getInstance()->getConnection();
}

/**
 * Helper function to check if database is available
 */
function isDatabaseAvailable() {
    if (!DatabaseConfig::isDatabaseMode()) {
        return false;
    }
    
    try {
        $db = DatabaseConfig::getInstance();
        return $db->testConnection() && $db->tablesExist();
    } catch (Exception $e) {
        return false;
    }
}

/**
 * Helper function to get storage mode
 */
function getStorageMode() {
    return DatabaseConfig::getStorageMode();
}

/**
 * Migration helper - check if we should use database or fall back to files
 */
function shouldUseDatabaseStorage() {
    // Only use database if explicitly configured and available
    return DatabaseConfig::isDatabaseMode() && isDatabaseAvailable();
}

/**
 * Get appropriate storage backend message
 */
function getStorageBackendInfo() {
    if (shouldUseDatabaseStorage()) {
        $config = DatabaseConfig::getInstance()->getConfig();
        return [
            'mode' => 'database',
            'message' => "Using MySQL database: {$config['database']} on {$config['host']}:{$config['port']}",
            'status' => 'active'
        ];
    } else {
        $logDir = getenv('LOC_LOG_DIR') ?: (__DIR__ . '/logs');
        return [
            'mode' => 'file',
            'message' => "Using file storage: {$logDir}",
            'status' => DatabaseConfig::isDatabaseMode() ? 'fallback' : 'configured'
        ];
    }
}
?>
