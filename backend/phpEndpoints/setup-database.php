<?php
/**
 * Database Setup Script
 * 
 * Interactive script to set up the MySQL database for the location tracking system
 * Run this script from the command line or web browser to initialize your database
 * 
 * @version 1.0
 * @author Adar Bahar
 */

require_once __DIR__ . '/db-config.php';

// Check if running from command line
$isCLI = php_sapi_name() === 'cli';

if (!$isCLI) {
    // Web interface
    header('Content-Type: text/html; charset=utf-8');
    echo "<!DOCTYPE html><html><head><title>Database Setup</title>";
    echo "<style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.6;}";
    echo ".success{color:#28a745;background:#d4edda;padding:10px;border-radius:5px;margin:10px 0;}";
    echo ".error{color:#dc3545;background:#f8d7da;padding:10px;border-radius:5px;margin:10px 0;}";
    echo ".warning{color:#856404;background:#fff3cd;padding:10px;border-radius:5px;margin:10px 0;}";
    echo ".info{color:#0c5460;background:#d1ecf1;padding:10px;border-radius:5px;margin:10px 0;}";
    echo "pre{background:#f8f9fa;padding:15px;border-radius:5px;overflow-x:auto;}";
    echo "</style></head><body>";
    echo "<h1>🗄️ Location Tracking Database Setup</h1>";
}

function output($message, $type = 'info') {
    global $isCLI;
    
    if ($isCLI) {
        $prefix = match($type) {
            'success' => '✅ ',
            'error' => '❌ ',
            'warning' => '⚠️  ',
            default => 'ℹ️  '
        };
        echo $prefix . $message . "\n";
    } else {
        echo "<div class=\"{$type}\">{$message}</div>";
    }
}

function runSetup() {
    output("Starting database setup...");
    
    // Check if .env file exists
    if (!file_exists(__DIR__ . '/.env')) {
        output("❌ .env file not found. Please copy .env.example to .env and configure your database settings.", 'error');
        return false;
    }
    
    // Check if database configuration is present
    if (!DatabaseConfig::isDatabaseMode()) {
        output("❌ Database configuration not found in .env file. Please configure DB_* variables.", 'error');
        output("Required variables: DB_HOST, DB_NAME, DB_USER, DB_PASS", 'info');
        return false;
    }
    
    $config = DatabaseConfig::getInstance();
    $dbConfig = $config->getConfig();
    
    output("📋 Database Configuration:");
    output("   Host: {$dbConfig['host']}:{$dbConfig['port']}", 'info');
    output("   Database: {$dbConfig['database']}", 'info');
    output("   Username: {$dbConfig['username']}", 'info');
    output("   Charset: {$dbConfig['charset']}", 'info');
    
    // Test connection
    output("🔌 Testing database connection...");
    
    try {
        $pdo = $config->getConnection();
        output("✅ Database connection successful!", 'success');
    } catch (Exception $e) {
        output("❌ Database connection failed: " . $e->getMessage(), 'error');
        output("Please check your database configuration and ensure:", 'warning');
        output("1. Database server is running", 'warning');
        output("2. Database exists: {$dbConfig['database']}", 'warning');
        output("3. User has proper permissions", 'warning');
        return false;
    }
    
    // Check if tables already exist
    if ($config->tablesExist()) {
        output("⚠️  Database tables already exist. Skipping table creation.", 'warning');
        output("If you want to recreate tables, please drop them manually first.", 'info');
        return true;
    }
    
    // Detect database type and choose appropriate schema
    output("🔍 Detecting database type...");

    try {
        $stmt = $pdo->query('SELECT VERSION()');
        $version = $stmt->fetchColumn();
        $isMariaDB = stripos($version, 'mariadb') !== false;

        if ($isMariaDB) {
            output("📊 Detected MariaDB: {$version}", 'info');
            $sqlFile = __DIR__ . '/setup-database-mariadb.sql';
        } else {
            output("📊 Detected MySQL: {$version}", 'info');
            $sqlFile = __DIR__ . '/setup-database.sql';
        }
    } catch (Exception $e) {
        output("⚠️  Could not detect database type, using default schema", 'warning');
        $sqlFile = __DIR__ . '/setup-database.sql';
    }

    output("📄 Reading database schema: " . basename($sqlFile));

    if (!file_exists($sqlFile)) {
        output("❌ Database schema file not found: {$sqlFile}", 'error');
        return false;
    }
    
    $sql = file_get_contents($sqlFile);
    if (!$sql) {
        output("❌ Failed to read database schema file", 'error');
        return false;
    }
    
    output("🔨 Creating database tables...");
    
    try {
        // Split SQL into individual statements
        $statements = array_filter(
            array_map('trim', explode(';', $sql)),
            function($stmt) {
                return !empty($stmt) && 
                       !str_starts_with($stmt, '--') && 
                       !str_starts_with($stmt, 'SET') &&
                       !str_starts_with($stmt, 'START') &&
                       !str_starts_with($stmt, 'COMMIT');
            }
        );
        
        $pdo->beginTransaction();
        
        foreach ($statements as $statement) {
            if (trim($statement)) {
                $pdo->exec($statement);
            }
        }
        
        $pdo->commit();
        
        output("✅ Database tables created successfully!", 'success');
        
        // Verify table creation
        if ($config->tablesExist()) {
            output("✅ Table verification passed!", 'success');
        } else {
            output("⚠️  Table verification failed - some tables may be missing", 'warning');
        }
        
    } catch (Exception $e) {
        $pdo->rollback();
        output("❌ Failed to create database tables: " . $e->getMessage(), 'error');
        return false;
    }
    
    output("🎉 Database setup completed successfully!", 'success');
    output("Your location tracking system is now ready to use MySQL database storage.", 'info');
    
    return true;
}

// Main execution
try {
    $success = runSetup();
    
    if ($success) {
        output("📊 Next steps:", 'info');
        output("1. Your API endpoints will now use MySQL database storage", 'info');
        output("2. You can migrate existing log files using the migration script", 'info');
        output("3. Test your setup by sending location data to your API endpoints", 'info');
        
        if (!$isCLI) {
            echo "<div class='info'>";
            echo "<h3>🔧 Database Management</h3>";
            echo "<p>You can now:</p>";
            echo "<ul>";
            echo "<li>Use your existing API endpoints - they will automatically use the database</li>";
            echo "<li>View data using database management tools like phpMyAdmin</li>";
            echo "<li>Run analytics queries directly on the database</li>";
            echo "<li>Set up automated backups for your location data</li>";
            echo "</ul>";
            echo "</div>";
        }
    }
    
} catch (Exception $e) {
    output("💥 Setup failed with error: " . $e->getMessage(), 'error');
    
    if (!$isCLI) {
        echo "<div class='error'>";
        echo "<h3>🔧 Troubleshooting</h3>";
        echo "<p>Common issues and solutions:</p>";
        echo "<ul>";
        echo "<li><strong>Connection refused:</strong> Check if MySQL server is running</li>";
        echo "<li><strong>Access denied:</strong> Verify username and password in .env</li>";
        echo "<li><strong>Database doesn't exist:</strong> Create the database first</li>";
        echo "<li><strong>Permission denied:</strong> Grant proper privileges to the database user</li>";
        echo "</ul>";
        echo "</div>";
    }
}

if (!$isCLI) {
    echo "</body></html>";
}
?>
