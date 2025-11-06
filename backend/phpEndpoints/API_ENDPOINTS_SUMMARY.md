# Location Tracking API - Endpoints Summary

## ✅ Migrated to FastAPI (Python)

The following endpoints have been migrated to the Python FastAPI backend with legacy-compatible paths under the `/location` prefix. Authentication via `X-API-Token` is supported, and data is stored in the separate `baharc5_location` database.

- `GET /location/health`
- `POST /location/api/getloc`
- `POST /location/api/driving`
- `POST /location/api/batch-sync`
- `GET /location/api/locations`
- `GET /location/api/driving-records`
- `GET /location/api/users`  (new)
- `GET /location/api/live/history`  (new)
- `GET /location/api/live/latest`  (new)
- `POST /location/api/live/session`  (new)
- `DELETE /location/api/live/session/{session_id}`  (new)
- `GET /location/api/live/stream`  (new)
- `GET /location/api/stats`  (new; segments=true supported: hourly for last_24h, daily for last_7d)
- `POST /location/api/stats`  (new; body supports segments=true)





## 🔗 **Core API Endpoints** (Recommended)

### **System Information**
- **`GET /api/`** - API Information
  - Returns comprehensive API documentation, available endpoints, and system status
  - No authentication required
  - **Use case**: API discovery and system status

- **`GET /api/health.php`** - Health Check
  - Simple health status, database connectivity, and system information
  - No authentication required
  - **Use case**: System monitoring and health checks

### **Location Data**
- **`POST /api/getloc.php`** - Submit location data
  - **Authentication**: Required (Bearer token or X-API-Token)
  - **Purpose**: Submit real-time location points
  - **Use case**: Real-time location tracking for mobile apps

### **Driving Events**
- **`POST /api/driving.php`** - Submit driving events
  - **Authentication**: Required (Bearer token or X-API-Token)
  - **Purpose**: Handle driving start/data/stop events with trip analytics
  - **Event Types**: `driving_start`, `driving_data`, `driving_stop`
  - **Use case**: Advanced driving behavior analysis and trip tracking

### **Batch Synchronization**
- **`POST /api/batch-sync.php`** - Batch data synchronization
  - **Authentication**: Required (Bearer token or X-API-Token)
  - **Purpose**: Offline data collection with multi-part uploads
  - **Features**: Progress tracking, atomic operations, conflict resolution
  - **Use case**: Offline data collection and bulk synchronization

### **Real-time Tracking**
- **`GET /api/location-stream.php`** - Location streaming endpoint
  - **Authentication**: Required (Bearer token or X-API-Token)
  - **Purpose**: Real-time location updates via efficient polling
  - **Features**: Cursor-based pagination, multi-device support, rate limiting
  - **Use case**: Live location tracking and map viewers

### **Location Management**
- **`POST /api/update-location.php`** - Update location coordinates
  - **Authentication**: Required (Bearer token or X-API-Token)
  - **Purpose**: Manually adjust location coordinates for specific records
  - **Use case**: Data quality management and anomaly correction

## 🔗 **Legacy Endpoints** (Backward Compatibility)

### **Root Level APIs**
- **`POST /getloc.php`** - Legacy location submission (⚠️ Deprecated)
- **`POST /driving.php`** - Legacy driving events (⚠️ Deprecated)
- **`POST /batch-sync.php`** - Legacy batch sync (⚠️ Deprecated)

*Note: Legacy endpoints redirect to their `/api/` counterparts. Use `/api/` endpoints for new implementations.*

## 🔗 **Dashboard Endpoints**

### **File Management**
- **`GET /dashboard/download.php`** - Download APK files
  - **Parameters**: `?file=filename.apk`
  - **Use case**: Mobile app distribution

- **`POST /dashboard/upload-apk.php`** - Upload APK files
  - **Authentication**: Dashboard admin password
  - **Features**: CSRF protection, file validation, upload logging
  - **Use case**: Mobile app deployment

## 📋 **Authentication Methods**

1. **Bearer Token**: `Authorization: Bearer YOUR_TOKEN`
2. **API Key Header**: `X-API-Token: YOUR_TOKEN`

## 📋 **Key Features**

- **Real-time tracking** with streaming endpoints
- **Offline data collection** with batch synchronization
- **Anomaly detection** and quality control
- **Driving behavior tracking** with trip management
- **Spatial optimization** with dwell time calculations
- **Multi-device support** with user management
- **Comprehensive logging** and diagnostics
- **Automatic failover** between database and file storage

## 📋 **Storage Modes**

1. **Database Mode**: MySQL/MariaDB with full features
2. **File Mode**: JSON file storage as fallback

The system automatically detects and falls back to file storage if the database is unavailable.

## 📋 **Documentation Access**

- **Swagger UI**: https://www.bahar.co.il/location/api/docs/
- **OpenAPI Spec**: https://www.bahar.co.il/location/swagger.json
- **Dynamic Spec**: https://www.bahar.co.il/location/swagger-json.php

## 📋 **Response Format**

All endpoints return JSON responses with:
- Proper HTTP status codes
- Consistent error handling
- Request tracking IDs for debugging
- Comprehensive validation messages

## 📋 **Rate Limiting**

- **Location**: 1000 requests/hour per IP
- **Driving**: 500 requests/hour per IP
- **Batch Sync**: 100 requests/hour per IP
- **Streaming**: 1 request/second per session

---

**Last Updated**: 2025-11-06
**API Version**: 2.1.0
**Documentation**: https://www.bahar.co.il/location/api/docs/
