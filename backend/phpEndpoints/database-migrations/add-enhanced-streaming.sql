-- =====================================================
-- ENHANCED STREAMING SUPPORT
-- Adds JWT session management and change detection logging
-- NO BREAKING CHANGES - All additions are optional
-- =====================================================

-- Table 1: Streaming Session Tokens (JWT-based sessions)
CREATE TABLE IF NOT EXISTS streaming_session_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Session identification
    session_id VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    device_ids JSON NULL COMMENT 'Array of device IDs to stream (null = all)',
    
    -- Token security
    token_hash VARCHAR(64) NOT NULL COMMENT 'SHA-256 hash of JWT token',
    
    -- Session lifecycle
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_session (session_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_user_active (user_id, revoked, expires_at),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='JWT-based session tokens for live streaming';

-- Table 2: Location Change Log (for debugging and analytics)
CREATE TABLE IF NOT EXISTS location_change_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Location reference
    device_id VARCHAR(100) NOT NULL,
    location_id BIGINT NULL COMMENT 'Reference to location_records.id',
    
    -- Change detection
    change_type ENUM('distance', 'time', 'speed', 'bearing', 'first', 'no_change') NOT NULL,
    should_emit BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Metrics
    distance_meters FLOAT NULL,
    time_diff_seconds INT NULL,
    speed_change_kmh FLOAT NULL,
    bearing_change_degrees FLOAT NULL,
    
    -- Tracking
    emitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_device_time (device_id, emitted_at),
    INDEX idx_change_type (change_type, should_emit),
    INDEX idx_location (location_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tracks location change detection for debugging and analytics';

-- Add index to device_last_position for streaming queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_device_server_time 
    ON device_last_position (device_id, server_time);

-- Add index to location_history_cache for cursor-based queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_server_time 
    ON location_history_cache (server_time);

-- Verify tables were created
SELECT 
    'streaming_session_tokens' as table_name,
    COUNT(*) as row_count
FROM streaming_session_tokens
UNION ALL
SELECT 
    'location_change_log' as table_name,
    COUNT(*) as row_count
FROM location_change_log;

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Next steps:
-- 1. Deploy shared/classes/JwtSessionManager.php
-- 2. Deploy shared/classes/ChangeDetector.php
-- 3. Deploy shared/classes/DuplicateDetector.php
-- 4. Deploy api/live/session.php (create/revoke sessions)
-- 5. Deploy api/live/stream-sse.php (SSE streaming endpoint)
-- 6. Update api/getloc.php with duplicate/change detection
-- =====================================================

