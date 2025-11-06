-- =====================================================
-- Stats Endpoint Performance Indexes
-- =====================================================
-- Purpose: Add optimized indexes for the new /api/stats endpoint
-- Impact: Minimal - these are covering indexes that will also improve existing queries
-- Recommended: Run during off-peak hours (2-4 AM Israel time)
-- Estimated time: 5-30 seconds depending on table size
-- =====================================================

-- Check current table sizes before running
-- SELECT 
--   TABLE_NAME, 
--   TABLE_ROWS, 
--   ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'Size (MB)'
-- FROM information_schema.TABLES 
-- WHERE TABLE_SCHEMA = 'location_tracking' 
-- AND TABLE_NAME IN ('location_records', 'driving_records', 'anomaly_detections');

-- =====================================================
-- 1. Location Records Stats Indexes
-- =====================================================

-- Index for stats queries by device_id and created_at
-- Covers: COUNT(*), MIN(created_at), MAX(created_at) queries
-- Used by: location_updates count, first_seen_at, last_update_at
ALTER TABLE location_records 
  ADD INDEX idx_stats_device_created (device_id, created_at, source_type)
  COMMENT 'Stats endpoint: device location counts and timestamps';

-- Index for stats queries by device_id and server_time
-- Covers: Queries filtering by server_time ranges
-- Used by: timeframe-based queries (today, last_7d, etc.)
ALTER TABLE location_records 
  ADD INDEX idx_stats_device_server (device_id, server_time, source_type)
  COMMENT 'Stats endpoint: server-time based filtering';

-- =====================================================
-- 2. Driving Records Stats Indexes
-- =====================================================

-- Index for driving session counts
-- Covers: COUNT(DISTINCT trip_id), driving session queries
-- Used by: driving_sessions count
ALTER TABLE driving_records 
  ADD INDEX idx_stats_device_trip (device_id, created_at, trip_id, event_type)
  COMMENT 'Stats endpoint: driving session counts';

-- =====================================================
-- 3. Anomaly Detection Stats Indexes
-- =====================================================

-- Index for anomaly counts by device and severity
-- Covers: Anomaly breakdown queries
-- Used by: anomaly counts by priority/severity
ALTER TABLE anomaly_detections 
  ADD INDEX idx_stats_anomaly_device (record_type, detected_at, anomaly_type, confidence_score)
  COMMENT 'Stats endpoint: anomaly statistics';

-- =====================================================
-- Verification Queries
-- =====================================================

-- Run these after creating indexes to verify they're being used:

-- EXPLAIN SELECT COUNT(*) FROM location_records 
-- WHERE device_id = 'test-device' AND created_at BETWEEN '2025-10-01' AND '2025-10-12';

-- EXPLAIN SELECT COUNT(DISTINCT trip_id) FROM driving_records 
-- WHERE device_id = 'test-device' AND created_at BETWEEN '2025-10-01' AND '2025-10-12';

-- EXPLAIN SELECT COUNT(*) FROM anomaly_detections 
-- WHERE record_type = 'location' AND detected_at BETWEEN '2025-10-01' AND '2025-10-12';

-- =====================================================
-- Rollback (if needed)
-- =====================================================

-- To remove these indexes if they cause issues:
-- ALTER TABLE location_records DROP INDEX idx_stats_device_created;
-- ALTER TABLE location_records DROP INDEX idx_stats_device_server;
-- ALTER TABLE driving_records DROP INDEX idx_stats_device_trip;
-- ALTER TABLE anomaly_detections DROP INDEX idx_stats_anomaly_device;

-- =====================================================
-- Performance Monitoring
-- =====================================================

-- Monitor slow queries after deployment:
-- SELECT * FROM mysql.slow_log WHERE sql_text LIKE '%stats%' ORDER BY query_time DESC LIMIT 10;

-- Check index usage:
-- SELECT * FROM information_schema.STATISTICS 
-- WHERE TABLE_SCHEMA = 'location_tracking' 
-- AND INDEX_NAME LIKE 'idx_stats%';

COMMIT;

