#!/usr/bin/env python3
"""
Export OpenAPI specification to JSON and YAML files.
This script generates comprehensive API documentation including all recent improvements.
"""

import json
import yaml
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
            "url": "https://api.mytrip.com",
            "description": "Production server"
        }
    ]
    
    # Add tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "auth",
            "description": "Authentication and user management"
        },
        {
            "name": "trips",
            "description": "Trip creation and management with enhanced validation"
        },
        {
            "name": "days",
            "description": "Day-by-day trip planning and organization"
        },
        {
            "name": "stops",
            "description": "Comprehensive stops management with 12 categories"
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
        }
    ]
    
    # Add examples for common operations
    openapi_schema["components"]["examples"] = {
        "TripCreateExample": {
            "summary": "Create a new trip",
            "value": {
                "title": "Israel Adventure",
                "destination": "Israel",
                "start_date": "2024-06-15",
                "timezone": "Asia/Jerusalem"
            }
        },
        "TripCreateResponse": {
            "summary": "Enhanced trip creation response",
            "value": {
                "trip": {
                    "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                    "title": "Israel Adventure",
                    "destination": "Israel",
                    "start_date": "2024-06-15",
                    "slug": "israel-adventure"
                },
                "next_steps": [
                    "Create your first day in Israel",
                    "Add start and end locations for your journey"
                ],
                "suggestions": {
                    "planning_timeline": "You have plenty of time to plan - consider researching seasonal activities"
                }
            }
        },
        "RoutingErrorExample": {
            "summary": "Enhanced routing error response",
            "value": {
                "detail": "Coordinates are outside the supported geographic region",
                "error_type": "OUT_OF_BOUNDS",
                "supported_regions": ["Israel", "Palestine"],
                "suggestions": [
                    "Try using nearby major cities or landmarks",
                    "Check if all locations are in the same general region",
                    "Consider splitting the trip into multiple days"
                ]
            }
        },
        "PlaceSearchExample": {
            "summary": "Place search with caching",
            "value": {
                "places": [
                    {
                        "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                        "name": "Western Wall",
                        "formatted_address": "Western Wall, Jerusalem, Israel",
                        "lat": 31.7767,
                        "lon": 35.2345,
                        "place_type": "attraction"
                    }
                ],
                "total": 1,
                "cached": True,
                "cache_age": 120
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
    print(f"   📖 Swagger UI: http://localhost:8000/docs")
    print(f"   📚 ReDoc: http://localhost:8000/redoc")

def generate_api_summary(schema):
    """Generate a human-readable API summary."""
    
    paths = schema.get("paths", {})
    total_endpoints = sum(len(methods) for methods in paths.values())
    
    summary = f"""# MyTrip API Documentation Summary

## 📊 API Overview

- **Total Endpoints**: {total_endpoints}
- **API Version**: {schema['info']['version']}
- **OpenAPI Version**: {schema['openapi']}

## 🚀 Recent Improvements

### Enhanced Trip Creation
- Input sanitization and validation
- Contextual next steps and suggestions
- Smart date range validation
- Auto-generated slugs

### Intelligent Routing System
- Hybrid GraphHopper integration (self-hosted + cloud)
- Exponential backoff for rate limiting
- Circuit breaker pattern for reliability
- Enhanced error messages with actionable steps

### Performance Optimizations
- Place search caching (5-minute TTL)
- Resource management improvements
- Smart bounds checking
- Matrix computation optimization

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

- [Swagger UI](http://localhost:8000/docs) - Interactive API documentation
- [ReDoc](http://localhost:8000/redoc) - Alternative documentation view
- [OpenAPI JSON](./openapi.json) - Machine-readable specification
- [OpenAPI YAML](./openapi.yaml) - Human-readable specification

## 🛡️ Authentication

All endpoints (except `/auth/login` and `/health`) require Bearer token authentication:

```bash
Authorization: Bearer <your_token>
```

Get your token by calling the `/auth/login` endpoint with your email address.

## 🚨 Error Handling

The API provides enhanced error responses with actionable recovery steps:

- **429 Rate Limiting**: Exponential backoff with retry guidance
- **400 Out of Bounds**: Geographic coverage limitations with alternatives
- **500 Service Errors**: Specific recovery steps and fallback options

## 📈 Performance Features

- **Caching**: Aggressive place search caching for improved response times
- **Circuit Breaker**: Automatic protection against cascading failures
- **Resource Management**: Optimized HTTP client usage and memory management
- **Smart Fallbacks**: Graceful degradation when services are unavailable

---

*Generated automatically from OpenAPI specification*
"""
    
    return summary

if __name__ == "__main__":
    export_openapi()
