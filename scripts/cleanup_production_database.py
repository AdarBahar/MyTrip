#!/usr/bin/env python3
"""
Production Database Cleanup Script

This script safely removes all trip-related data from the PRODUCTION MySQL database
while preserving users and other important data.

⚠️  WARNING: This operates on the PRODUCTION database!
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Production Database configuration from .env
DB_CONFIG = {
    'host': 'srv1135.hstgr.io',
    'port': 3306,
    'database': 'u181637338_dayplanner',
    'user': 'u181637338_dayplanner',
    'password': 'xbZeSoREl%c63Ttq',
    'autocommit': False
}

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print(f"✅ Connected to PRODUCTION MySQL database: {DB_CONFIG['database']}")
            print(f"   Host: {DB_CONFIG['host']}")
            return connection
    except Error as e:
        print(f"❌ Error connecting to PRODUCTION MySQL: {e}")
        sys.exit(1)

def execute_query(cursor, query, params=None):
    """Execute a query safely with error handling"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.rowcount
    except Error as e:
        print(f"❌ Error executing query: {e}")
        print(f"Query: {query}")
        raise

def get_table_count(cursor, table_name):
    """Get count of records in a table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except Error:
        return 0

def backup_table_info(cursor):
    """Get information about tables before cleanup"""
    tables = [
        'trips', 'trip_members', 'days', 'stops', 'route_versions', 
        'route_legs', 'places', 'pins', 'users'
    ]
    
    info = {}
    for table in tables:
        count = get_table_count(cursor, table)
        info[table] = count
        print(f"📊 {table}: {count} records")
    
    return info

def cleanup_production_data():
    """Main cleanup function for PRODUCTION database"""
    print("🧹 Starting PRODUCTION Database Cleanup")
    print("=" * 60)
    print("⚠️  WARNING: This will delete ALL trip-related data from PRODUCTION!")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   Host: {DB_CONFIG['host']}")
    print("=" * 60)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get initial counts
        print("\n📊 Current PRODUCTION Database State:")
        initial_counts = backup_table_info(cursor)
        
        # Confirm cleanup
        print(f"\n⚠️  FINAL WARNING: This will delete ALL trip-related data from PRODUCTION!")
        print(f"Users will be preserved: {initial_counts.get('users', 0)} users")
        print(f"Database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
        
        confirm = input("\nType 'DELETE ALL PRODUCTION TRIPS' to confirm: ")
        if confirm != 'DELETE ALL PRODUCTION TRIPS':
            print("❌ Cleanup cancelled")
            return
        
        print("\n🗑️  Starting PRODUCTION cleanup process...")
        
        # Start transaction
        connection.start_transaction()
        
        # 1. Delete route_legs (depends on route_versions)
        print("\n1️⃣ Cleaning route_legs...")
        deleted = execute_query(cursor, "DELETE FROM route_legs")
        print(f"   Deleted {deleted} route legs")
        
        # 2. Delete route_versions (depends on days)
        print("\n2️⃣ Cleaning route_versions...")
        deleted = execute_query(cursor, "DELETE FROM route_versions")
        print(f"   Deleted {deleted} route versions")
        
        # 3. Delete stops (depends on days, trips, places)
        print("\n3️⃣ Cleaning stops...")
        deleted = execute_query(cursor, "DELETE FROM stops")
        print(f"   Deleted {deleted} stops")
        
        # 4. Delete pins (depends on trips, places)
        print("\n4️⃣ Cleaning pins...")
        deleted = execute_query(cursor, "DELETE FROM pins")
        print(f"   Deleted {deleted} pins")
        
        # 5. Delete days (depends on trips)
        print("\n5️⃣ Cleaning days...")
        deleted = execute_query(cursor, "DELETE FROM days")
        print(f"   Deleted {deleted} days")
        
        # 6. Delete trip_members (depends on trips, users)
        print("\n6️⃣ Cleaning trip_members...")
        deleted = execute_query(cursor, "DELETE FROM trip_members")
        print(f"   Deleted {deleted} trip members")
        
        # 7. Delete trip-owned places (preserve user and system places)
        print("\n7️⃣ Cleaning trip-owned places...")
        deleted = execute_query(cursor, "DELETE FROM places WHERE owner_type = 'trip'")
        print(f"   Deleted {deleted} trip-owned places")
        
        # 8. Delete trips (main table)
        print("\n8️⃣ Cleaning trips...")
        deleted = execute_query(cursor, "DELETE FROM trips")
        print(f"   Deleted {deleted} trips")
        
        # Commit transaction
        connection.commit()
        print("\n✅ PRODUCTION transaction committed successfully!")
        
        # Get final counts
        print("\n📊 Final PRODUCTION Database State:")
        final_counts = backup_table_info(cursor)
        
        # Show summary
        print("\n📈 PRODUCTION Cleanup Summary:")
        print("-" * 40)
        for table in ['trips', 'trip_members', 'days', 'stops', 'route_versions', 'route_legs', 'pins']:
            initial = initial_counts.get(table, 0)
            final = final_counts.get(table, 0)
            deleted = initial - final
            print(f"{table:15}: {initial:4} → {final:4} (deleted {deleted})")
        
        # Verify users are preserved
        users_preserved = final_counts.get('users', 0)
        print(f"\n👥 Users preserved: {users_preserved}")
        
        print("\n🎉 PRODUCTION database cleanup completed successfully!")
        print("✅ All trip-related data has been removed from PRODUCTION")
        print("✅ Users and user settings have been preserved")
        print("✅ System places have been preserved")
        
    except Exception as e:
        # Rollback on error
        connection.rollback()
        print(f"\n❌ Error during PRODUCTION cleanup: {e}")
        print("🔄 Transaction rolled back - no changes made to PRODUCTION")
        raise
        
    finally:
        cursor.close()
        connection.close()
        print("\n🔌 PRODUCTION database connection closed")

def verify_cleanup():
    """Verify the cleanup was successful"""
    print("\n🔍 Verifying PRODUCTION cleanup...")
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Check that trip tables are empty
        trip_tables = ['trips', 'trip_members', 'days', 'stops', 'route_versions', 'route_legs', 'pins']
        all_clean = True
        
        for table in trip_tables:
            count = get_table_count(cursor, table)
            if count > 0:
                print(f"⚠️  {table} still has {count} records")
                all_clean = False
            else:
                print(f"✅ {table} is clean (0 records)")
        
        # Check that users are preserved
        user_count = get_table_count(cursor, 'users')
        print(f"👥 Users preserved: {user_count}")
        
        # Check system places are preserved
        cursor.execute("SELECT COUNT(*) FROM places WHERE owner_type != 'trip'")
        system_places = cursor.fetchone()[0]
        print(f"📍 Non-trip places preserved: {system_places}")
        
        if all_clean:
            print("\n✅ PRODUCTION cleanup verification PASSED")
            print("🎯 PRODUCTION database ready for fresh trip creation!")
        else:
            print("\n❌ PRODUCTION cleanup verification FAILED")
            print("Some trip data may still exist in PRODUCTION")
            
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("🧹 PRODUCTION Database Cleanup Tool")
    print("=" * 50)
    print("⚠️  WARNING: This will remove ALL trip-related data from PRODUCTION")
    print("while preserving users and system data.")
    print()
    
    try:
        cleanup_production_data()
        verify_cleanup()
        
        print("\n🚀 Next Steps:")
        print("1. Restart your backend server")
        print("2. Clear browser cache")
        print("3. Try creating a new trip")
        print("4. The 409 conflict errors should be resolved")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  PRODUCTION cleanup cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
