#!/usr/bin/env python3
"""
Create location database tables
Run this script to create the location database schema
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def main():
    """Create location database tables"""
    print("🗄️  Creating location database tables...")

    try:
        from app.core.config import settings
        from app.core.location_database import LocationBase, location_engine

        print(f"   Location DB: {settings.LOCATION_DB_NAME}")
        print(f"   Location DB Host: {settings.LOCATION_DB_HOST or settings.DB_HOST}")
        print(f"   Location DB User: {settings.LOCATION_DB_USER}")

        # Create all tables
        LocationBase.metadata.create_all(bind=location_engine)

        print("   ✅ Location database tables created successfully!")

        # List created tables
        inspector = location_engine.dialect.get_table_names(location_engine.connect())
        print(f"   📋 Created tables: {inspector}")

        return 0

    except Exception as e:
        print(f"   ❌ Error creating location database tables: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
