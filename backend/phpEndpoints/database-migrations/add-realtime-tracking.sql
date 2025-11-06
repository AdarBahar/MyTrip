-- =====================================================
-- REAL-TIME TRACKING ENHANCEMENT
-- Adds support for live location streaming via polling
-- NO BREAKING CHANGES - All additions are optional
-- =====================================================

-- Table 1: Device Last Position (for quick map initialization)
CREATE TABLE IF NOT EXISTS device_last_position (
    device_id VARCHAR(100) PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Latest position
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy FLOAT NULL,
    altitude FLOAT NULL,
    
    -- Movement data
    speed FLOAT NULL,
    bearing FLOAT NULL,
    
    -- Timestamps
    recorded_at BIGINT NOT NULL,           -- Client timestamp (ms)
    server_time TIMESTAMP NOT NULL,        -- Server timestamp
    
    -- Metadata
    battery_level TINYINT NULL,
    network_type VARCHAR(20) NULL,
    provider VARCHAR(20) NULL,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes for fast queries
    INDEX idx_user_updated (user_id, updated_at),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 2: Location History Cache (for fast polling queries)
-- Stores recent points (last 24 hours) with optimized indexes
CREATE TABLE IF NOT EXISTS location_history_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Identification
    device_id VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    
    -- Position
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy FLOAT NULL,
    altitude FLOAT NULL,
    
    -- Movement
    speed FLOAT NULL,
    bearing FLOAT NULL,
    
    -- Timestamps
    recorded_at BIGINT NOT NULL,           -- Client timestamp (ms) - PRIMARY SORT KEY
    server_time TIMESTAMP NOT NULL,
    
    -- Metadata (minimal for cache)
    battery_level TINYINT NULL,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Critical indexes for polling queries
    INDEX idx_device_time (device_id, recorded_at),
    INDEX idx_user_time (user_id, recorded_at),
    INDEX idx_cleanup (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 3: Streaming Sessions (track active viewers)
CREATE TABLE IF NOT EXISTS streaming_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Session identification
    session_id VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    device_id VARCHAR(100) NULL,          -- NULL = all devices for user
    
    -- Session state
    last_cursor BIGINT NOT NULL,          -- Last timestamp received
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Client info
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_poll_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_session (session_id),
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes to existing location_records for history queries (non-breaking)
-- These will speed up fallback queries if cache is empty
CREATE INDEX IF NOT EXISTS idx_device_recorded_at 
    ON location_records (device_id, client_time);

CREATE INDEX IF NOT EXISTS idx_user_recorded_at 
    ON location_records (user_id, client_time);

-- Verify tables were created
SELECT 
    'device_last_position' as table_name,
    COUNT(*) as row_count
FROM device_last_position
UNION ALL
SELECT 
    'location_history_cache' as table_name,
    COUNT(*) as row_count
FROM location_history_cache
UNION ALL
SELECT 
    'streaming_sessions' as table_name,
    COUNT(*) as row_count
FROM streaming_sessions;

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Next steps:
-- 1. Deploy api/getloc-realtime-hook.php
-- 2. Deploy api/location-stream.php
-- 3. Update api/getloc.php to include the hook
-- 4. Update dashboard/map-test.php with live tracking UI
-- 5. Setup cron job for cleanup
-- =====================================================

