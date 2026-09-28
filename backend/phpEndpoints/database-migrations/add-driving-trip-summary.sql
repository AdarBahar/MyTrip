-- =====================================================
-- Driving Trip Summary Columns
-- =====================================================
-- Purpose: Persist the trip_summary sent with driving events (normally only on
--          driving_stop) by POST /location/api/driving and POST /location/api/batch-sync.
--          Maps TripSummary {duration_seconds, distance_meters, avg_speed, max_speed}
--          onto flat, nullable columns on driving_records.
-- Impact:  Additive only - four nullable FLOAT columns, no defaults, no backfill.
--          Existing rows are left with NULLs.
-- Target:  The location database (e.g. mytrips_location), NOT the main DB.
-- Order:   Apply BEFORE deploying the backend code that maps these columns
--          (the ORM selects them on every driving_records query).
--
-- Note: legacy PHP setup-database.sql created an unused `trip_summary JSON`
--       column. It is intentionally left untouched; the backend uses the
--       typed columns below instead.
-- =====================================================

ALTER TABLE driving_records
  ADD COLUMN trip_duration_seconds FLOAT NULL
    COMMENT 'Trip summary: duration in seconds' AFTER trip_id,
  ADD COLUMN trip_distance_meters FLOAT NULL
    COMMENT 'Trip summary: distance in meters' AFTER trip_duration_seconds,
  ADD COLUMN trip_avg_speed FLOAT NULL
    COMMENT 'Trip summary: average speed in km/h' AFTER trip_distance_meters,
  ADD COLUMN trip_max_speed FLOAT NULL
    COMMENT 'Trip summary: max speed in km/h' AFTER trip_avg_speed;

-- =====================================================
-- Verification Queries
-- =====================================================

-- SHOW COLUMNS FROM driving_records LIKE trip_%;

-- SELECT id, event_type, trip_id, trip_duration_seconds, trip_distance_meters,
--        trip_avg_speed, trip_max_speed
-- FROM driving_records
-- WHERE trip_duration_seconds IS NOT NULL
-- ORDER BY id DESC LIMIT 10;

-- =====================================================
-- Rollback (if needed)
-- =====================================================

-- Deploy the previous backend code first, then:
-- ALTER TABLE driving_records
--   DROP COLUMN trip_duration_seconds,
--   DROP COLUMN trip_distance_meters,
--   DROP COLUMN trip_avg_speed,
--   DROP COLUMN trip_max_speed;
