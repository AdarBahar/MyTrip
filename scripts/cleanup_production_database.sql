-- PRODUCTION Database Cleanup Script
-- ⚠️  WARNING: This operates on the PRODUCTION database!
-- 
-- Safely removes all trip-related data while preserving users
-- Database: u181637338_dayplanner on srv1135.hstgr.io
--
-- Tables cleaned (in dependency order):
-- 1. route_legs → route_versions → days
-- 2. stops → days, trips, places  
-- 3. pins → trips, places
-- 4. days → trips
-- 5. trip_members → trips, users
-- 6. places (trip-owned only)
-- 7. trips (main table)
--
-- Preserved:
-- - users (all user data)
-- - user_settings  
-- - places (user-owned and system-owned)

-- Start transaction for safety
START TRANSACTION;

-- Show current state before cleanup
SELECT 'BEFORE CLEANUP - Current PRODUCTION Database State' as status;

SELECT 
    'trips' as table_name, 
    COUNT(*) as record_count 
FROM trips
UNION ALL
SELECT 
    'trip_members' as table_name, 
    COUNT(*) as record_count 
FROM trip_members
UNION ALL
SELECT 
    'days' as table_name, 
    COUNT(*) as record_count 
FROM days
UNION ALL
SELECT 
    'stops' as table_name, 
    COUNT(*) as record_count 
FROM stops
UNION ALL
SELECT 
    'route_versions' as table_name, 
    COUNT(*) as record_count 
FROM route_versions
UNION ALL
SELECT 
    'route_legs' as table_name, 
    COUNT(*) as record_count 
FROM route_legs
UNION ALL
SELECT 
    'pins' as table_name, 
    COUNT(*) as record_count 
FROM pins
UNION ALL
SELECT 
    'places' as table_name, 
    COUNT(*) as record_count 
FROM places
UNION ALL
SELECT 
    'users' as table_name, 
    COUNT(*) as record_count 
FROM users;

-- Show specific trips that will be deleted
SELECT 'Trips to be deleted:' as status;
SELECT id, slug, title, created_at FROM trips ORDER BY created_at DESC LIMIT 10;

-- Disable foreign key checks temporarily for easier cleanup
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Clean route_legs (depends on route_versions)
SELECT 'Cleaning route_legs...' as status;
DELETE FROM route_legs;
SELECT ROW_COUNT() as deleted_route_legs;

-- 2. Clean route_versions (depends on days)  
SELECT 'Cleaning route_versions...' as status;
DELETE FROM route_versions;
SELECT ROW_COUNT() as deleted_route_versions;

-- 3. Clean stops (depends on days, trips, places)
SELECT 'Cleaning stops...' as status;
DELETE FROM stops;
SELECT ROW_COUNT() as deleted_stops;

-- 4. Clean pins (depends on trips, places)
SELECT 'Cleaning pins...' as status;
DELETE FROM pins;
SELECT ROW_COUNT() as deleted_pins;

-- 5. Clean days (depends on trips)
SELECT 'Cleaning days...' as status;
DELETE FROM days;
SELECT ROW_COUNT() as deleted_days;

-- 6. Clean trip_members (depends on trips, users)
SELECT 'Cleaning trip_members...' as status;
DELETE FROM trip_members;
SELECT ROW_COUNT() as deleted_trip_members;

-- 7. Clean trip-owned places only (preserve user and system places)
SELECT 'Cleaning trip-owned places...' as status;
DELETE FROM places WHERE owner_type = 'trip';
SELECT ROW_COUNT() as deleted_trip_places;

-- 8. Clean trips (main table)
SELECT 'Cleaning trips...' as status;
DELETE FROM trips;
SELECT ROW_COUNT() as deleted_trips;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Show final state after cleanup
SELECT 'AFTER CLEANUP - Final PRODUCTION Database State' as status;

SELECT 
    'trips' as table_name, 
    COUNT(*) as record_count 
FROM trips
UNION ALL
SELECT 
    'trip_members' as table_name, 
    COUNT(*) as record_count 
FROM trip_members
UNION ALL
SELECT 
    'days' as table_name, 
    COUNT(*) as record_count 
FROM days
UNION ALL
SELECT 
    'stops' as table_name, 
    COUNT(*) as record_count 
FROM stops
UNION ALL
SELECT 
    'route_versions' as table_name, 
    COUNT(*) as record_count 
FROM route_versions
UNION ALL
SELECT 
    'route_legs' as table_name, 
    COUNT(*) as record_count 
FROM route_legs
UNION ALL
SELECT 
    'pins' as table_name, 
    COUNT(*) as record_count 
FROM pins
UNION ALL
SELECT 
    'places (total)' as table_name, 
    COUNT(*) as record_count 
FROM places
UNION ALL
SELECT 
    'places (user-owned)' as table_name, 
    COUNT(*) as record_count 
FROM places WHERE owner_type = 'user'
UNION ALL
SELECT 
    'places (system-owned)' as table_name, 
    COUNT(*) as record_count 
FROM places WHERE owner_type = 'system'
UNION ALL
SELECT 
    'users (preserved)' as table_name, 
    COUNT(*) as record_count 
FROM users;

-- Verification queries
SELECT 'VERIFICATION - All trip tables should be empty' as status;

SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM trips) = 0 
         AND (SELECT COUNT(*) FROM trip_members) = 0
         AND (SELECT COUNT(*) FROM days) = 0
         AND (SELECT COUNT(*) FROM stops) = 0
         AND (SELECT COUNT(*) FROM route_versions) = 0
         AND (SELECT COUNT(*) FROM route_legs) = 0
         AND (SELECT COUNT(*) FROM pins) = 0
        THEN '✅ CLEANUP SUCCESSFUL - All trip tables are empty'
        ELSE '❌ CLEANUP INCOMPLETE - Some trip data remains'
    END as cleanup_status;

-- Show preserved data
SELECT 
    CONCAT('👥 Users preserved: ', COUNT(*)) as preserved_users
FROM users;

SELECT 
    CONCAT('📍 Non-trip places preserved: ', COUNT(*)) as preserved_places
FROM places 
WHERE owner_type != 'trip';

-- Final warning before commit
SELECT 'PRODUCTION DATABASE CLEANUP READY TO COMMIT' as status;
SELECT '⚠️  WARNING: This will permanently delete ALL trip data from PRODUCTION!' as warning;
SELECT 'Review the results above, then run COMMIT; or ROLLBACK;' as instruction;

-- Commit the transaction
-- IMPORTANT: Review the results above before committing!
-- If everything looks correct, uncomment the next line:
-- COMMIT;

-- If you want to rollback instead (undo all changes), uncomment this line:
-- ROLLBACK;
