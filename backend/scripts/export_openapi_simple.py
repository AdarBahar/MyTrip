#!/usr/bin/env python3
"""
Simple OpenAPI export script that doesn't require database connection
"""
import json
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set minimal environment variables to avoid validation errors
os.environ.setdefault("DB_CLIENT", "sqlite")  # Use SQLite to avoid connection issues
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "test.db")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("SECRET_KEY", "test-key-for-openapi-generation")
os.environ.setdefault("MAPTILER_API_KEY", "test")
os.environ.setdefault("GRAPHHOPPER_API_KEY", "test")
os.environ.setdefault("ENFORCE_PROD_DB", "false")  # Disable production DB enforcement

try:
    from app.main import app

    # Get the OpenAPI schema
    openapi_schema = app.openapi()

    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "MyTrip API Support",
        "email": "support@mytrip.com",
        "url": "https://github.com/AdarBahar/MyTrip",
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    # Add server information
    openapi_schema["servers"] = [
        {"url": "https://mytrips-api.bahar.co.il", "description": "Production server"},
        {"url": "http://localhost:8000", "description": "Development server"},
    ]

    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)

    # Export to JSON
    json_file = output_dir / "openapi.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print("✅ OpenAPI specification exported:")
    print(f"   📄 JSON: {json_file}")
    print("\n🌐 View documentation at:")
    print("   📖 Swagger UI: https://mytrips-api.bahar.co.il/docs")
    print("   📚 ReDoc: https://mytrips-api.bahar.co.il/redoc")

except Exception as e:
    print(f"❌ Error generating OpenAPI schema: {e}")
    sys.exit(1)
