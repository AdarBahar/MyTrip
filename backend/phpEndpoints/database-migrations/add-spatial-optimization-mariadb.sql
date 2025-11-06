-- =====================================================
-- SPATIAL OPTIMIZATION MIGRATION - MariaDB Compatible
-- Adds spatial indexing and dwell session tables for optimized dwell calculation
-- =====================================================

-- Add spatial columns to location_records table
ALTER TABLE location_records
  ADD COLUMN geohash_7 VARCHAR(32) AS (
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
  
  -- Spatial data (simplified for MariaDB)
  geom POINT,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  
  INDEX ix_ds_device_time (device_id, start_time),
  INDEX ix_ds_user_time (user_id, start_time),
  INDEX ix_ds_cluster (cluster_id),
  INDEX ix_ds_duration (duration_s),
  INDEX ix_ds_confidence (confidence_score)
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
  
  -- Spatial data (simplified for MariaDB)
  geom POINT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (device_id, day, cluster_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  
  INDEX ix_dd_user_day (user_id, day),
  INDEX ix_dd_cluster (cluster_id),
  INDEX ix_dd_dwell (total_dwell_s)
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
-- VIEWS FOR EASY ACCESS (MariaDB Compatible)
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

-- =====================================================
-- TRIGGERS TO POPULATE GEOMETRY COLUMNS
-- =====================================================

-- Trigger for location_records geometry
DELIMITER //
CREATE TRIGGER tr_location_records_geom_insert
  BEFORE INSERT ON location_records
  FOR EACH ROW
BEGIN
  SET NEW.geom = POINT(NEW.longitude, NEW.latitude);
END //

CREATE TRIGGER tr_location_records_geom_update
  BEFORE UPDATE ON location_records
  FOR EACH ROW
BEGIN
  IF NEW.latitude != OLD.latitude OR NEW.longitude != OLD.longitude THEN
    SET NEW.geom = POINT(NEW.longitude, NEW.latitude);
  END IF;
END //

-- Trigger for dwell_sessions geometry
CREATE TRIGGER tr_dwell_sessions_geom_insert
  BEFORE INSERT ON dwell_sessions
  FOR EACH ROW
BEGIN
  SET NEW.geom = POINT(NEW.centroid_lon, NEW.centroid_lat);
END //

CREATE TRIGGER tr_dwell_sessions_geom_update
  BEFORE UPDATE ON dwell_sessions
  FOR EACH ROW
BEGIN
  IF NEW.centroid_lat != OLD.centroid_lat OR NEW.centroid_lon != OLD.centroid_lon THEN
    SET NEW.geom = POINT(NEW.centroid_lon, NEW.centroid_lat);
  END IF;
END //

-- Trigger for dwell_daily geometry
CREATE TRIGGER tr_dwell_daily_geom_insert
  BEFORE INSERT ON dwell_daily
  FOR EACH ROW
BEGIN
  SET NEW.geom = POINT(NEW.centroid_lon, NEW.centroid_lat);
END //

CREATE TRIGGER tr_dwell_daily_geom_update
  BEFORE UPDATE ON dwell_daily
  FOR EACH ROW
BEGIN
  IF NEW.centroid_lat != OLD.centroid_lat OR NEW.centroid_lon != OLD.centroid_lon THEN
    SET NEW.geom = POINT(NEW.centroid_lon, NEW.centroid_lat);
  END IF;
END //

DELIMITER ;

-- =====================================================
-- POPULATE EXISTING GEOMETRY DATA
-- =====================================================

-- Update existing location_records with geometry data
UPDATE location_records 
SET geom = POINT(longitude, latitude) 
WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;
