# Location Module Migration Guide

## 🎯 Overview

This guide provides comprehensive instructions for migrating PHP endpoints to the new `/location` module in the FastAPI application. The location module has been set up following the established project patterns and is ready for your PHP endpoint migration.

## 📁 Module Structure

The location module follows the established project architecture:

```
backend/app/
├── api/location/           # API endpoints
│   ├── __init__.py        # Module initialization
│   └── router.py          # FastAPI router with endpoints
├── models/
│   └── location.py        # SQLAlchemy database models
├── schemas/
│   └── location.py        # Pydantic request/response schemas
└── services/
    └── location.py        # Business logic service layer
```

## 🔗 Integration Status

✅ **Router Integration**: Location router is integrated with main FastAPI app
✅ **URL Prefix**: All endpoints accessible at `https://mytrips-api.bahar.co.il/location/*`
✅ **Authentication**: Uses existing JWT/auth system
✅ **Database**: Integrated with existing MySQL database
✅ **Models**: Location model registered with SQLAlchemy
✅ **User Relationships**: User model updated with location relationship

## 🚀 Quick Start

### 1. Test the Module

The location module is ready and includes a health check endpoint:

```bash
# Test the health endpoint
curl https://mytrips-api.bahar.co.il/location/health

# Expected response:
{
  "status": "ok",
  "module": "location"
}
```

### 2. View API Documentation

Once deployed, visit the automatic API documentation:
- **Swagger UI**: `https://mytrips-api.bahar.co.il/docs`
- **ReDoc**: `https://mytrips-api.bahar.co.il/redoc`

Look for the "location" tag to see all location endpoints.

## 📝 Migration Process

### Step 1: Provide Your PHP Code

When you're ready to migrate, provide:

1. **PHP Route Files**: Controllers, route definitions
2. **Database Schema**: Table structures, relationships
3. **Business Logic**: Validation rules, processing logic
4. **Authentication**: How endpoints are protected
5. **Request/Response Examples**: Expected data formats

### Step 2: Customization Areas

The following template files will be customized based on your PHP code:

#### **Router (`backend/app/api/location/router.py`)**
- Replace template endpoints with your actual PHP endpoints
- Customize URL paths, HTTP methods, and parameters
- Add proper request/response models
- Implement authentication requirements

#### **Models (`backend/app/models/location.py`)**
- Customize the Location model fields based on your database schema
- Add relationships to other models
- Create additional models if needed (e.g., LocationFavorite, LocationReview)
- Add proper indexes and constraints

#### **Schemas (`backend/app/schemas/location.py`)**
- Customize request/response schemas based on your API contracts
- Add validation rules matching your PHP validation
- Create specialized schemas for different endpoints
- Add proper field documentation

#### **Services (`backend/app/services/location.py`)**
- Implement your PHP business logic in Python
- Add custom validation and processing rules
- Integrate with external APIs if needed
- Add caching, logging, and error handling

### Step 3: Database Migration

After customizing the models, create and run database migrations:

```bash
# Generate migration
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add location tables"

# Review the generated migration file
# Edit if necessary

# Run migration
alembic upgrade head
```

## 🔧 Customization Examples

### Adding a New Endpoint

```python
# In backend/app/api/location/router.py

@router.get("/search/nearby")
async def search_nearby_locations(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, gt=0, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for locations near a coordinate"""
    service = LocationService(db)
    locations = service.get_nearby_locations(lat, lng, radius_km)
    return {"locations": locations}
```

### Adding Custom Validation

```python
# In backend/app/schemas/location.py

class LocationCreate(LocationBase):
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if 'forbidden_word' in v.lower():
            raise ValueError('Name contains forbidden content')
        return v
```

### Adding Business Logic

```python
# In backend/app/services/location.py

def validate_location_ownership(self, location_id: str, user_id: str) -> bool:
    """Custom business rule for location ownership"""
    location = self.get_location_by_id(location_id, user_id)
    if not location:
        return False

    # Custom logic here
    return location.created_by == user_id or user_id in location.collaborators
```

## 🔒 Security & Authentication

The location module uses the existing authentication system:

```python
# Protected endpoint (requires authentication)
@router.get("/my-locations")
async def get_my_locations(
    current_user: User = Depends(get_current_user),  # Required auth
    db: Session = Depends(get_db)
):
    # Only authenticated users can access
    pass

# Optional authentication
@router.get("/public-locations")
async def get_public_locations(
    current_user: Optional[User] = Depends(get_current_user_optional),  # Optional auth
    db: Session = Depends(get_db)
):
    # Works for both authenticated and anonymous users
    pass
```

## 📊 Database Patterns

### Following Existing Patterns

The location module follows established database patterns:

- **ULID Primary Keys**: Using `BaseModel` mixin
- **Timestamps**: Using `TimestampMixin` (created_at, updated_at in UTC)
- **Soft Delete**: Using `SoftDeleteMixin` (deleted_at field)
- **User Relationships**: Foreign key to users table
- **Indexes**: Proper indexing for performance

### Example Model Customization

```python
# Add custom fields based on your PHP schema
class Location(BaseModel, SoftDeleteMixin):
    __tablename__ = "locations"

    # Your custom fields
    name = Column(String(255), nullable=False)
    rating = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 5.00
    visit_count = Column(Integer, default=0)

    # Custom relationships
    reviews = relationship("LocationReview", back_populates="location")

    # Custom indexes
    __table_args__ = (
        Index('idx_location_rating', 'rating'),
        Index('idx_location_popular', 'visit_count', 'rating'),
    )
```

## 🚀 Deployment

The location module deploys automatically with the existing application:

1. **Same Docker Container**: No separate deployment needed
2. **Same Database**: Uses existing MySQL connection
3. **Same Environment**: Shares all configuration
4. **Same SSL/Domain**: Available at existing domain with `/location` prefix

### Deployment Commands

```bash
# Deploy using existing scripts
sudo ./deployment/scripts/deploy-app-login.sh

# Or manual deployment
cd /opt/dayplanner
sudo git pull origin main
sudo systemctl restart dayplanner-backend
```

## 📈 Monitoring & Logging

The location module integrates with existing monitoring:

- **Health Checks**: `/location/health` endpoint
- **Logging**: Uses existing logging configuration
- **Error Handling**: Uses existing exception handlers
- **Metrics**: Included in existing monitoring endpoints

## 🧪 Testing

Create tests following existing patterns:

```python
# backend/tests/api/test_location.py
import pytest
from fastapi.testclient import TestClient

def test_location_health(client: TestClient):
    response = client.get("/location/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "module": "location"}

def test_create_location(client: TestClient, auth_headers):
    location_data = {
        "name": "Test Location",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    response = client.post("/location/", json=location_data, headers=auth_headers)
    assert response.status_code == 201
```

## 📋 Next Steps

1. **Provide PHP Code**: Share your PHP endpoints for migration
2. **Review Templates**: Examine the template files created
3. **Customize Implementation**: Modify templates based on your requirements
4. **Create Database Migration**: Generate and run Alembic migration
5. **Test Endpoints**: Verify functionality matches PHP implementation
6. **Deploy**: Use existing deployment process

## 🆘 Support

If you need help during migration:

1. **Template Issues**: The templates can be modified to match your exact requirements
2. **Database Schema**: Complex schemas can be accommodated
3. **Business Logic**: Any PHP logic can be ported to Python
4. **Performance**: Optimization patterns are available
5. **Integration**: External API integrations can be added

**Ready to start migration!** Provide your PHP code and I'll customize the location module to match your exact requirements.
