-- Location Tracking System Database Schema
-- Version: 1.0
-- Author: Adar Bahar
-- 
-- This script creates the complete database schema for the location tracking system
-- Run this script after creating your database and user

-- Set SQL mode for compatibility
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

-- =====================================================
-- 1. USERS TABLE
-- =====================================================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_username (username),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. DEVICES TABLE
-- =====================================================
CREATE TABLE devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id VARCHAR(100) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    device_name VARCHAR(100),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_user_device (user_id, device_id),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. LOCATION RECORDS TABLE (Main Data)
-- =====================================================
CREATE TABLE location_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Core identification
    device_id VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    
    -- Timestamps
    server_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_time BIGINT, -- Unix timestamp in milliseconds
    client_time_iso TIMESTAMP NULL, -- Converted ISO timestamp
    
    -- Location data
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy FLOAT NULL,
    altitude FLOAT NULL,
    
    -- Movement data
    speed FLOAT NULL, -- m/s
    bearing FLOAT NULL, -- degrees 0-360
    
    -- Device context
    battery_level TINYINT NULL, -- 0-100
    network_type VARCHAR(20) NULL,
    provider VARCHAR(20) NULL,
    
    -- Request metadata
    ip_address VARCHAR(45) NULL, -- IPv6 support
    user_agent TEXT NULL,
    
    -- Data source tracking
    source_type ENUM('realtime', 'batch') DEFAULT 'realtime',
    batch_sync_id VARCHAR(50) NULL,
    
    -- Legacy support
    legacy_unique_id VARCHAR(20) NULL, -- For migration from log files
    file_source VARCHAR(255) NULL, -- Original log file name
    line_number INT NULL, -- Original line number in log file
    
    -- Timestamps for tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Performance indexes
    INDEX idx_device_time (device_id, client_time),
    INDEX idx_user_time (user_id, client_time),
    INDEX idx_location (latitude, longitude),
    INDEX idx_server_time (server_time),
    INDEX idx_client_time (client_time),
    INDEX idx_batch_sync (batch_sync_id),
    INDEX idx_legacy_unique (legacy_unique_id),
    INDEX idx_source_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 4. DRIVING RECORDS TABLE
-- =====================================================
CREATE TABLE driving_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Core identification
    device_id VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    
    -- Timestamps
    server_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_time BIGINT, -- Unix timestamp in milliseconds
    client_time_iso TIMESTAMP NULL,
    
    -- Driving event data
    event_type ENUM('driving_start', 'driving_data', 'driving_stop') NOT NULL,
    trip_id VARCHAR(100) NULL,
    
    -- Location data (embedded from location object)
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy FLOAT NULL,
    altitude FLOAT NULL,
    
    -- Movement data
    speed FLOAT NULL,
    bearing FLOAT NULL,
    
    -- Trip summary (JSON for driving_stop events)
    trip_summary JSON NULL,
    
    -- Request metadata
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    
    -- Data source tracking
    source_type ENUM('realtime', 'batch') DEFAULT 'realtime',
    batch_sync_id VARCHAR(50) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_device_time (device_id, client_time),
    INDEX idx_user_time (user_id, client_time),
    INDEX idx_event_type (event_type),
    INDEX idx_trip_id (trip_id),
    INDEX idx_batch_sync (batch_sync_id),
    INDEX idx_location (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 5. ANOMALY DETECTIONS TABLE
-- =====================================================
CREATE TABLE anomaly_detections (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Reference to source record
    record_type ENUM('location', 'driving') NOT NULL,
    record_id BIGINT NOT NULL,
    
    -- Anomaly classification
    anomaly_type ENUM(
        'poor_accuracy',
        'excessive_speed', 
        'large_time_gap',
        'distance_jump',
        'impossible_speed',
        'gps_misreading'
    ) NOT NULL,
    
    -- Detection details
    confidence_score TINYINT NOT NULL, -- 0-100
    description TEXT NOT NULL,
    threshold_value FLOAT NULL, -- The threshold that was exceeded
    actual_value FLOAT NULL, -- The actual value that triggered detection
    
    -- Detection metadata
    detection_algorithm VARCHAR(50) NOT NULL,
    detection_version VARCHAR(20) DEFAULT '1.0',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Context for GPS misreading detection
    context_data JSON NULL, -- Store additional context like surrounding points
    
    INDEX idx_record (record_type, record_id),
    INDEX idx_anomaly_type (anomaly_type),
    INDEX idx_confidence (confidence_score),
    INDEX idx_detected_at (detected_at),
    
    -- Composite index for efficient anomaly queries
    INDEX idx_type_confidence (anomaly_type, confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 6. ANOMALY STATUS TABLE
-- =====================================================
CREATE TABLE anomaly_status (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Reference to source record
    record_type ENUM('location', 'driving') NOT NULL,
    record_id BIGINT NOT NULL,
    
    -- Status tracking
    status ENUM('detected', 'confirmed', 'dismissed', 'under_review') DEFAULT 'detected',
    marked_by_user BOOLEAN DEFAULT FALSE,
    
    -- User actions
    marked_by_user_id INT NULL,
    marked_at TIMESTAMP NULL,
    review_notes TEXT NULL,
    
    -- Legacy support for migration
    legacy_unique_id VARCHAR(20) NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (marked_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Ensure one status per record
    UNIQUE KEY unique_record_status (record_type, record_id),
    
    INDEX idx_status (status),
    INDEX idx_marked_by_user (marked_by_user),
    INDEX idx_legacy_unique (legacy_unique_id),
    INDEX idx_marked_at (marked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 7. BATCH SYNC SESSIONS TABLE
-- =====================================================
CREATE TABLE batch_sync_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    -- Session identification
    sync_id VARCHAR(50) NOT NULL UNIQUE,
    device_id VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,

    -- Batch details
    total_parts TINYINT NOT NULL,
    parts_received TINYINT DEFAULT 0,
    total_records INT DEFAULT 0,

    -- Status tracking
    status ENUM('in_progress', 'completed', 'failed', 'expired') DEFAULT 'in_progress',

    -- Processing results
    processing_results JSON NULL,
    error_message TEXT NULL,

    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL, -- For cleanup of stale sessions

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_sync_id (sync_id),
    INDEX idx_device_user (device_id, user_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 8. DATA QUALITY METRICS TABLE
-- =====================================================
CREATE TABLE data_quality_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    -- Scope
    user_id INT NOT NULL,
    device_id VARCHAR(100) NULL, -- NULL for user-wide metrics
    date_analyzed DATE NOT NULL,

    -- Record counts
    total_location_records INT DEFAULT 0,
    total_driving_records INT DEFAULT 0,

    -- Anomaly counts by type
    poor_accuracy_count INT DEFAULT 0,
    excessive_speed_count INT DEFAULT 0,
    large_time_gap_count INT DEFAULT 0,
    distance_jump_count INT DEFAULT 0,
    impossible_speed_count INT DEFAULT 0,
    gps_misreading_count INT DEFAULT 0,

    -- Quality scores (0-100)
    overall_quality_score TINYINT DEFAULT 100,
    accuracy_quality_score TINYINT DEFAULT 100,
    temporal_quality_score TINYINT DEFAULT 100,
    spatial_quality_score TINYINT DEFAULT 100,

    -- Analysis metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_version VARCHAR(20) DEFAULT '1.0',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Ensure one metric per user/device/date
    UNIQUE KEY unique_metrics (user_id, device_id, date_analyzed),

    INDEX idx_user_date (user_id, date_analyzed),
    INDEX idx_device_date (device_id, date_analyzed),
    INDEX idx_quality_score (overall_quality_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 9. VIEWS FOR COMMON QUERIES
-- =====================================================

-- Anomaly Summary View
CREATE VIEW anomaly_summary AS
SELECT
    lr.user_id,
    lr.device_id,
    DATE(lr.server_time) as record_date,
    ad.anomaly_type,
    COUNT(*) as anomaly_count,
    AVG(ad.confidence_score) as avg_confidence,
    SUM(CASE WHEN ast.status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_count,
    SUM(CASE WHEN ast.marked_by_user = TRUE THEN 1 ELSE 0 END) as user_marked_count
FROM location_records lr
JOIN anomaly_detections ad ON ad.record_type = 'location' AND ad.record_id = lr.id
LEFT JOIN anomaly_status ast ON ast.record_type = 'location' AND ast.record_id = lr.id
GROUP BY lr.user_id, lr.device_id, DATE(lr.server_time), ad.anomaly_type;

-- Location Records with Anomaly Status View
CREATE VIEW location_records_with_anomalies AS
SELECT
    lr.*,
    CASE WHEN ast.id IS NOT NULL THEN TRUE ELSE FALSE END as has_anomaly_status,
    ast.status as anomaly_status,
    ast.marked_by_user,
    ast.marked_at,
    GROUP_CONCAT(ad.anomaly_type) as detected_anomaly_types,
    GROUP_CONCAT(ad.confidence_score) as anomaly_confidence_scores
FROM location_records lr
LEFT JOIN anomaly_status ast ON ast.record_type = 'location' AND ast.record_id = lr.id
LEFT JOIN anomaly_detections ad ON ad.record_type = 'location' AND ad.record_id = lr.id
GROUP BY lr.id;

-- =====================================================
-- 10. INITIAL DATA AND INDEXES
-- =====================================================

-- Additional indexes for performance
CREATE INDEX idx_location_anomaly_filter ON location_records (user_id, server_time, latitude, longitude);
CREATE INDEX idx_spatial_time ON location_records (server_time, latitude, longitude);
CREATE INDEX idx_batch_processing ON location_records (batch_sync_id, source_type, created_at);

-- Insert default admin user (optional)
INSERT INTO users (username, display_name, is_active)
VALUES ('admin', 'System Administrator', TRUE)
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

COMMIT;
