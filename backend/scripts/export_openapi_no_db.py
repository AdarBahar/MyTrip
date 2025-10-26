#!/usr/bin/env python3
"""
Export OpenAPI specification to JSON and YAML files without database connection.
This script generates comprehensive API documentation including the new app-login endpoint.
"""

import json
import yaml
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the database connection to avoid connection errors
import unittest.mock

def mock_create_all(*args, **kwargs):
    """Mock database table creation"""
    pass

def mock_get_db():
    """Mock database session"""
    pass

# Apply mocks before importing the app
with unittest.mock.patch('app.core.database.Base.metadata.create_all', mock_create_all):
    with unittest.mock.patch('app.core.database.get_db', mock_get_db):
        from app.main import app

def export_openapi():
    """Export OpenAPI specification to multiple formats."""
    
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "MyTrip API Support",
        "email": "support@mytrip.com",
        "url": "https://github.com/AdarBahar/MyTrip"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://mytrips-api.bahar.co.il",
            "description": "Production server"
        }
    ]
    
    # Add tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "auth",
            "description": "Authentication and user management (including new app-login endpoint)"
        },
        {
            "name": "trips",
            "description": "Trip creation and management with enhanced validation"
        },
        {
            "name": "days",
            "description": "Day-by-day trip planning and organization with soft delete support"
        },
        {
            "name": "stops",
            "description": "Comprehensive stops management with 12 categories and soft delete"
        },
        {
            "name": "places",
            "description": "Place search and geocoding with aggressive caching"
        },
        {
            "name": "routing",
            "description": "Intelligent routing with hybrid GraphHopper integration"
        },
        {
            "name": "settings",
            "description": "User settings and preferences"
        },
        {
            "name": "ai",
            "description": "AI-powered route optimization and suggestions"
        }
    ]
    
    # Add examples for common operations including app-login
    openapi_schema["components"]["examples"] = {
        "AppLoginExample": {
            "summary": "Simple app login request",
            "value": {
                "email": "user@example.com",
                "password": "user_password"
            }
        },
        "AppLoginSuccessResponse": {
            "summary": "Successful app login response",
            "value": {
                "authenticated": True,
                "user_id": "01K5P68329YFSCTV777EB4GM9P",
                "message": "Authentication successful"
            }
        },
        "AppLoginFailureResponse": {
            "summary": "Failed app login response",
            "value": {
                "authenticated": False,
                "user_id": None,
                "message": "Invalid email or password"
            }
        },
        "TripCreateExample": {
            "summary": "Create a new trip",
            "value": {
                "title": "Israel Adventure",
                "destination": "Israel",
                "start_date": "2024-06-15",
                "timezone": "Asia/Jerusalem"
            }
        },
        "DayDeleteExample": {
            "summary": "Soft delete a day with cascade",
            "value": {
                "status": "DELETED"
            }
        }
    }
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)
    
    # Export to JSON
    json_file = output_dir / "openapi.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    # Export to YAML
    yaml_file = output_dir / "openapi.yaml"
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # Create a human-readable summary
    summary_file = output_dir / "API_SUMMARY.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(generate_api_summary(openapi_schema))
    
    print(f"✅ OpenAPI specification exported:")
    print(f"   📄 JSON: {json_file}")
    print(f"   📄 YAML: {yaml_file}")
    print(f"   📋 Summary: {summary_file}")
    print(f"\n🌐 View documentation at:")
    print(f"   📖 Swagger UI: https://mytrips-api.bahar.co.il/docs")
    print(f"   📚 ReDoc: https://mytrips-api.bahar.co.il/redoc")
    
    # Check for app-login endpoint
    paths = openapi_schema.get("paths", {})
    if "/auth/app-login" in paths:
        print(f"\n✅ App Login Endpoint Found:")
        print(f"   🔐 POST /auth/app-login - Simple authentication without token management")
    else:
        print(f"\n❌ App Login Endpoint NOT found in OpenAPI spec")

def generate_api_summary(schema):
    """Generate a human-readable API summary."""
    
    paths = schema.get("paths", {})
    total_endpoints = sum(len(methods) for methods in paths.values())
    
    # Check for new endpoints
    has_app_login = "/auth/app-login" in paths
    
    summary = f"""# MyTrip API Documentation Summary

## 📊 API Overview

- **Total Endpoints**: {total_endpoints}
- **API Version**: {schema['info']['version']}
- **OpenAPI Version**: {schema['openapi']}

## 🆕 Latest Updates

### New App Login Endpoint
{'✅' if has_app_login else '❌'} **POST /auth/app-login** - Simple authentication without token management
- Returns boolean authentication result
- No JWT token generation required
- Perfect for mobile apps and legacy systems
- Validates against hashed passwords in database

### Enhanced Day Management
- Soft delete functionality with cascade to stops
- Day status enum: ACTIVE, INACTIVE, DELETED
- Bulk operations with proper filtering

### Improved Error Handling
- Generic error messages to prevent user enumeration
- Graceful degradation for authentication failures
- Enhanced validation and security

## 📋 Endpoint Categories

"""
    
    # Group endpoints by tags
    tag_counts = {}
    for path, methods in paths.items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and 'tags' in operation:
                for tag in operation['tags']:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    for tag, count in sorted(tag_counts.items()):
        summary += f"- **{tag.title()}**: {count} endpoints\n"
    
    summary += f"""

## 🔗 Quick Links

- [Swagger UI](https://mytrips-api.bahar.co.il/docs) - Interactive API documentation
- [ReDoc](https://mytrips-api.bahar.co.il/redoc) - Alternative documentation view
- [OpenAPI JSON](./openapi.json) - Machine-readable specification
- [OpenAPI YAML](./openapi.yaml) - Human-readable specification

## 🛡️ Authentication Options

### JWT Token Authentication (Existing)
```bash
Authorization: Bearer <your_token>
```
Get your token by calling the `/auth/login` endpoint.

### Simple App Authentication (New)
```bash
POST /auth/app-login
{{
  "email": "user@example.com",
  "password": "user_password"
}}
```
Returns simple boolean authentication result without token management.

## 🚨 Error Handling

The API provides enhanced error responses with actionable recovery steps:

- **Authentication Errors**: Generic messages to prevent user enumeration
- **Validation Errors**: Detailed field-level validation feedback
- **Rate Limiting**: Exponential backoff with retry guidance
- **Service Errors**: Specific recovery steps and fallback options

## 📈 Performance Features

- **Caching**: Aggressive place search caching for improved response times
- **Soft Delete**: Data preservation with proper filtering
- **Circuit Breaker**: Automatic protection against cascading failures
- **Resource Management**: Optimized HTTP client usage and memory management

---

*Generated automatically from OpenAPI specification*
"""
    
    return summary

if __name__ == "__main__":
    export_openapi()
