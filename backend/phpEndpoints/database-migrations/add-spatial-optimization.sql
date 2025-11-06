-- =====================================================
-- SPATIAL OPTIMIZATION MIGRATION
-- Adds spatial indexing and dwell session tables for optimized dwell calculation
-- =====================================================

-- Add spatial columns to location_records table
ALTER TABLE location_records
  ADD COLUMN geohash_7 VARCHAR(12) AS (
    CONCAT(
      'g_',
      FLOOR(latitude / 0.00135), '_',  -- ~150m grid
      FLOOR(longitude / (0.00135 / COS(RADIANS(latitude))))
    )
  ) STORED;

-- Add geometry column separately for MariaDB compatibility
ALTER TABLE location_records
  ADD COLUMN geom POINT;

-- Create indexes for spatial optimization
CREATE INDEX ix_loc_device_time ON location_records(device_id, client_time);
CREATE INDEX ix_loc_geohash ON location_records(geohash_7);
CREATE SPATIAL INDEX sidx_loc_geom ON location_records(geom);

-- =====================================================
-- DWELL SESSIONS TABLE (Canonical dwell data)
-- =====================================================
CREATE TABLE dwell_sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  device_id VARCHAR(100) NOT NULL,
  user_id INT NOT NULL,
  cluster_id VARCHAR(32) NOT NULL,     -- spatial cluster identifier
  centroid_lat DECIMAL(10,8) NOT NULL,
  centroid_lon DECIMAL(11,8) NOT NULL,
  start_time BIGINT NOT NULL,          -- milliseconds
  end_time BIGINT NOT NULL,            -- milliseconds
  duration_s INT NOT NULL,
  points_count INT NOT NULL,
  max_gap_ms INT NOT NULL DEFAULT 3600000,
  accuracy_avg FLOAT NULL,
  confidence_score TINYINT DEFAULT 100,
  
  -- Quality metrics
  min_accuracy FLOAT NULL,
  max_accuracy FLOAT NULL,
  accuracy_variance FLOAT NULL,
  
  -- Spatial data
  geom POINT,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  
  INDEX ix_ds_device_time (device_id, start_time),
  INDEX ix_ds_user_time (user_id, start_time),
  INDEX ix_ds_cluster (cluster_id),
  INDEX ix_ds_duration (duration_s),
  INDEX ix_ds_confidence (confidence_score),
  SPATIAL INDEX sidx_ds_geom (geom)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- DAILY DWELL ROLLUPS (For quick UI summaries)
-- =====================================================
CREATE TABLE dwell_daily (
  device_id VARCHAR(100) NOT NULL,
  user_id INT NOT NULL,
  day DATE NOT NULL,
  cluster_id VARCHAR(32) NOT NULL,
  centroid_lat DECIMAL(10,8) NOT NULL,
  centroid_lon DECIMAL(11,8) NOT NULL,
  total_dwell_s INT NOT NULL,
  visits INT NOT NULL,
  avg_confidence TINYINT DEFAULT 100,
  first_visit_time BIGINT NOT NULL,
  last_visit_time BIGINT NOT NULL,
  
  -- Spatial data
  geom POINT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (device_id, day, cluster_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  
  INDEX ix_dd_user_day (user_id, day),
  INDEX ix_dd_cluster (cluster_id),
  INDEX ix_dd_dwell (total_dwell_s),
  SPATIAL INDEX sidx_dd_geom (geom)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- DWELL PROCESSING STATE (For incremental processing)
-- =====================================================
CREATE TABLE dwell_processing_state (
  device_id VARCHAR(100) PRIMARY KEY,
  last_processed_time BIGINT NOT NULL,
  last_cluster_id VARCHAR(32) NULL,
  current_session_id BIGINT NULL,
  processing_version VARCHAR(10) DEFAULT '1.0',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX ix_dps_time (last_processed_time),
  FOREIGN KEY (current_session_id) REFERENCES dwell_sessions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- STORED PROCEDURES FOR DWELL PROCESSING
-- =====================================================

DELIMITER //

-- Process new location points for a device and update dwell sessions
CREATE PROCEDURE ProcessDwellSessions(
  IN p_device_id VARCHAR(100),
  IN p_from_time BIGINT,
  IN p_to_time BIGINT
)
BEGIN
  DECLARE done INT DEFAULT FALSE;
  DECLARE v_lat, v_lon DECIMAL(10,8);
  DECLARE v_time BIGINT;
  DECLARE v_accuracy FLOAT;
  DECLARE v_cluster_id VARCHAR(32);
  DECLARE v_last_cluster VARCHAR(32);
  DECLARE v_last_time BIGINT;
  DECLARE v_session_id BIGINT;
  
  -- Cursor for processing points in chronological order
  DECLARE point_cursor CURSOR FOR
    SELECT latitude, longitude, client_time, accuracy,
           CONCAT('g_', 
                  FLOOR(latitude / 0.00135), '_',
                  FLOOR(longitude / (0.00135 / COS(RADIANS(latitude)))))
           AS cluster_id
    FROM location_records 
    WHERE device_id = p_device_id 
      AND client_time BETWEEN p_from_time AND p_to_time
      AND (accuracy IS NULL OR accuracy <= 100)  -- Quality filter
    ORDER BY client_time;
  
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
  
  -- Get current processing state
  SELECT last_cluster_id, last_processed_time, current_session_id
  INTO v_last_cluster, v_last_time, v_session_id
  FROM dwell_processing_state 
  WHERE device_id = p_device_id;
  
  OPEN point_cursor;
  
  read_loop: LOOP
    FETCH point_cursor INTO v_lat, v_lon, v_time, v_accuracy, v_cluster_id;
    IF done THEN
      LEAVE read_loop;
    END IF;
    
    -- Process point logic would go here
    -- This is a simplified version - full implementation would handle
    -- session creation, extension, and closure based on gaps and clusters
    
  END LOOP;
  
  CLOSE point_cursor;
  
  -- Update processing state
  INSERT INTO dwell_processing_state (device_id, last_processed_time, last_cluster_id, current_session_id)
  VALUES (p_device_id, p_to_time, v_last_cluster, v_session_id)
  ON DUPLICATE KEY UPDATE
    last_processed_time = p_to_time,
    last_cluster_id = v_last_cluster,
    current_session_id = v_session_id;
    
END //

DELIMITER ;

-- =====================================================
-- VIEWS FOR EASY ACCESS
-- =====================================================

-- View for recent dwell sessions with human-readable durations
CREATE VIEW recent_dwell_sessions AS
SELECT 
  ds.*,
  u.username,
  CASE 
    WHEN ds.duration_s < 60 THEN CONCAT(ds.duration_s, 's')
    WHEN ds.duration_s < 3600 THEN CONCAT(FLOOR(ds.duration_s/60), 'm ', ds.duration_s%60, 's')
    ELSE CONCAT(FLOOR(ds.duration_s/3600), 'h ', FLOOR((ds.duration_s%3600)/60), 'm')
  END AS duration_human,
  FROM_UNIXTIME(ds.start_time/1000) AS start_datetime,
  FROM_UNIXTIME(ds.end_time/1000) AS end_datetime
FROM dwell_sessions ds
JOIN users u ON ds.user_id = u.id
WHERE ds.start_time >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY)) * 1000
ORDER BY ds.start_time DESC;

-- View for daily dwell summaries
CREATE VIEW daily_dwell_summary AS
SELECT 
  dd.*,
  u.username,
  CASE 
    WHEN dd.total_dwell_s < 60 THEN CONCAT(dd.total_dwell_s, 's')
    WHEN dd.total_dwell_s < 3600 THEN CONCAT(FLOOR(dd.total_dwell_s/60), 'm')
    ELSE CONCAT(FLOOR(dd.total_dwell_s/3600), 'h ', FLOOR((dd.total_dwell_s%3600)/60), 'm')
  END AS total_dwell_human
FROM dwell_daily dd
JOIN users u ON dd.user_id = u.id
ORDER BY dd.day DESC, dd.total_dwell_s DESC;
