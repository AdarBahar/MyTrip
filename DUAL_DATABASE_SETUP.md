# Dual Database Configuration

## 🎯 Overview

The application now supports **dual database configuration** where:
- **Main Database**: Handles existing endpoints (trips, users, places, etc.)
- **Location Database**: Handles new `/location` endpoints with separate credentials

## 📊 Database Configuration

### **Main Database**
- **Host**: Uses `DB_HOST` environment variable
- **Database**: Uses `DB_NAME` environment variable
- **User**: Uses `DB_USER` environment variable
- **Password**: Uses `DB_PASSWORD` environment variable

### **Location Database**
- **Host**: Uses `LOCATION_DB_HOST` (defaults to `DB_HOST` if empty)
- **Database**: `baharc5_location`
- **User**: `baharc5_location`
- **Password**: `IObUn{,mL%OU`

## 🔧 Environment Variables

Add these to your `.env` file:

```bash
# Main Database (existing)
DB_CLIENT=mysql
DB_HOST=your-mysql-host
DB_PORT=3306
DB_NAME=your-main-database
DB_USER=your-main-user
DB_PASSWORD="your-main-password"

# Location Database (new)
LOCATION_DB_CLIENT=mysql
LOCATION_DB_HOST=  # Leave empty to use same host as main DB
LOCATION_DB_PORT=3306
LOCATION_DB_NAME=baharc5_location
LOCATION_DB_USER=baharc5_location
LOCATION_DB_PASSWORD="IObUn{,mL%OU"
```

## 🏗️ Architecture

### **Separate Database Engines**
- **Main Engine**: `app.core.database.engine`
- **Location Engine**: `app.core.location_database.location_engine`

### **Separate Base Classes**
- **Main Models**: Inherit from `BaseModel` (uses main database)
- **Location Models**: Inherit from `LocationBaseModel` (uses location database)

### **Separate Dependencies**
- **Main Endpoints**: Use `get_db()` dependency
- **Location Endpoints**: Use `get_location_db()` dependency

## 📁 File Structure

```
backend/app/
├── core/
│   ├── config.py                 # Updated with location DB settings
│   ├── database.py              # Main database engine
│   └── location_database.py     # Location database engine (NEW)
├── models/
│   ├── location_base.py         # Location database base models (NEW)
│   ├── location.py              # Location model (UPDATED)
│   └── user.py                  # User model (UPDATED - removed location relationship)
└── api/location/
    └── router.py                # Updated to use location database
```

## 🔄 Key Changes Made

### **1. Configuration (`app/core/config.py`)**
- Added location database settings
- Added `location_database_url` property
- Supports URL encoding for special characters in passwords

### **2. Location Database (`app/core/location_database.py`)**
- Separate SQLAlchemy engine for location database
- Separate session factory and dependency
- Separate base class for location models

### **3. Location Models (`app/models/location.py`)**
- Updated to use `LocationBaseModel` instead of `BaseModel`
- Removed foreign key relationship to users table
- Uses `created_by` as string reference to user ID

### **4. Main Models (`app/models/user.py`)**
- Removed `locations` relationship (different database)
- Added comment explaining separation

### **5. Location Router (`app/api/location/router.py`)**
- Updated to use `get_location_db()` dependency
- All endpoints now connect to location database

## 🚀 Deployment

### **1. Create Location Database Tables**

```bash
cd backend
python3 create_location_tables.py
```

### **2. Test Configuration**

```bash
cd backend
python3 test_dual_database.py
```

### **3. Environment Setup**

Update your production environment file with location database credentials.

## 🔒 Security

- **Separate Credentials**: Location database uses different user/password
- **Isolated Access**: Location endpoints cannot access main database tables
- **User References**: Location models reference users by ID string (no foreign key)

## 📋 API Endpoints

### **Main Database Endpoints**
- `/trips/*` - Trip management
- `/auth/*` - Authentication
- `/places/*` - Places search
- `/routing/*` - Route calculation
- All other existing endpoints

### **Location Database Endpoints**
- `/location/*` - All location-related endpoints
- Uses separate database with provided credentials

## 🧪 Testing

The dual database setup has been tested and verified:

✅ **Configuration**: Both database URLs generate correctly
✅ **Models**: Both database models import successfully
✅ **Dependencies**: Both database dependencies work
✅ **Router**: Location router uses correct database
✅ **Isolation**: Databases are properly separated

## 🔧 Development

### **Adding New Location Endpoints**

1. Create endpoints in `app/api/location/router.py`
2. Use `get_location_db()` dependency
3. Import location models from `app.models.location`
4. Models automatically use location database

### **Adding New Location Models**

1. Create model inheriting from `LocationBaseModel`
2. Import in location router or service
3. Run `create_location_tables.py` to create schema

## 📞 Support

The dual database configuration is ready for your PHP endpoint migration. When you provide your PHP code, I'll:

1. **Customize location models** based on your database schema
2. **Implement endpoints** matching your PHP functionality
3. **Create database migrations** for any additional tables
4. **Test integration** with both databases

**Ready for your PHP endpoints!** 🚀
