-- Rename Tables to Match Backend Schema
-- This script renames the MyTrips_ prefixed tables to match what the backend expects
--
-- BEFORE: MyTrips_Trips, MyTrips_Users, etc.
-- AFTER:  trips, users, etc.
--
-- This will resolve the 409 conflicts by making the database schema match the backend models

-- Start transaction for safety
START TRANSACTION;

-- Show current tables
SELECT 'BEFORE RENAME - Current Tables:' as status;
SHOW TABLES;

-- Check if the target tables already exist (they shouldn't)
SELECT 'Checking for existing target tables...' as status;

SELECT 
    CASE 
        WHEN COUNT(*) > 0 
        THEN 'WARNING: Some target tables already exist!'
        ELSE 'OK: No target tables exist, safe to rename'
    END as check_result
FROM information_schema.tables 
WHERE table_schema = 'dayplanner' 
AND table_name IN ('trips', 'users', 'days', 'stops', 'routes', 'legs', 'pins', 'trip_members');

-- Rename tables to match backend expectations
-- Order matters due to foreign key constraints

SELECT 'Renaming tables...' as status;

-- 1. Rename users table (no dependencies)
RENAME TABLE MyTrips_Users TO users;
SELECT 'Renamed MyTrips_Users -> users' as status;

-- 2. Rename trips table (depends on users)
RENAME TABLE MyTrips_Trips TO trips;
SELECT 'Renamed MyTrips_Trips -> trips' as status;

-- 3. Rename trip_members table (depends on trips and users)
RENAME TABLE MyTrips_TripMembers TO trip_members;
SELECT 'Renamed MyTrips_TripMembers -> trip_members' as status;

-- 4. Rename days table (depends on trips)
RENAME TABLE MyTrips_Days TO days;
SELECT 'Renamed MyTrips_Days -> days' as status;

-- 5. Rename stops table (depends on days and trips)
RENAME TABLE MyTrips_Stops TO stops;
SELECT 'Renamed MyTrips_Stops -> stops' as status;

-- 6. Rename routes table (depends on days)
RENAME TABLE MyTrips_Routes TO route_versions;
SELECT 'Renamed MyTrips_Routes -> route_versions' as status;

-- 7. Rename legs table (depends on routes)
RENAME TABLE MyTrips_Legs TO route_legs;
SELECT 'Renamed MyTrips_Legs -> route_legs' as status;

-- 8. Rename pins table (depends on trips)
RENAME TABLE MyTrips_Pins TO pins;
SELECT 'Renamed MyTrips_Pins -> pins' as status;

-- Show final tables
SELECT 'AFTER RENAME - Final Tables:' as status;
SHOW TABLES;

-- Verify the key tables exist
SELECT 'Verification - Key tables should exist:' as status;

SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('trips', 'users', 'days', 'stops', 'route_versions', 'route_legs', 'pins', 'trip_members')
        THEN '✅ REQUIRED TABLE'
        ELSE '📋 OTHER TABLE'
    END as table_status
FROM information_schema.tables 
WHERE table_schema = 'dayplanner'
ORDER BY 
    CASE 
        WHEN table_name IN ('trips', 'users', 'days', 'stops', 'route_versions', 'route_legs', 'pins', 'trip_members')
        THEN 1 
        ELSE 2 
    END,
    table_name;

-- Check record counts in renamed tables
SELECT 'Record counts in renamed tables:' as status;

SELECT 'trips' as table_name, COUNT(*) as record_count FROM trips
UNION ALL
SELECT 'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'trip_members' as table_name, COUNT(*) as record_count FROM trip_members
UNION ALL
SELECT 'days' as table_name, COUNT(*) as record_count FROM days
UNION ALL
SELECT 'stops' as table_name, COUNT(*) as record_count FROM stops
UNION ALL
SELECT 'route_versions' as table_name, COUNT(*) as record_count FROM route_versions
UNION ALL
SELECT 'route_legs' as table_name, COUNT(*) as record_count FROM route_legs
UNION ALL
SELECT 'pins' as table_name, COUNT(*) as record_count FROM pins;

-- Final verification
SELECT 'VERIFICATION COMPLETE' as status;
SELECT 
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'dayplanner' 
            AND table_name IN ('trips', 'users', 'days', 'stops', 'route_versions', 'route_legs', 'pins', 'trip_members')
        ) = 8
        THEN '✅ SUCCESS: All required tables renamed correctly'
        ELSE '❌ ERROR: Some tables missing after rename'
    END as rename_result;

-- Commit the changes
-- IMPORTANT: Review the results above before committing!
-- If everything looks correct, uncomment the next line:
-- COMMIT;

-- If you want to rollback instead (undo all changes), uncomment this line:
-- ROLLBACK;

SELECT 'TRANSACTION READY TO COMMIT' as status;
SELECT 'Review the results above, then run COMMIT; or ROLLBACK;' as instruction;
