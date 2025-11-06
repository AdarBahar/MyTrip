# 🔄 Batch Synchronization System

## 📋 Overview

The Batch Synchronization System enables mobile applications to upload offline-collected location and driving data in organized chunks, ensuring data integrity and proper ordering even after extended offline periods.

## 🏗️ System Architecture

### **Core Components**

1. **Batch Sync Endpoint** (`/batch-sync.php`)
   - Handles multi-part uploads with progress tracking
   - Validates data integrity and ordering
   - Provides atomic operations for data consistency

2. **Temporary Storage** (`/batch_temp/`)
   - Stores partial uploads until complete
   - Organizes data by sync session ID
   - Automatic cleanup after processing

3. **Data Processing Engine**
   - Merges and orders data from all parts
   - Writes to appropriate log files
   - Maintains chronological consistency

## 🚀 API Specification

### **Endpoint**
```
POST /batch-sync.php
```

### **Authentication**
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

### **Request Format**
```json
{
  "sync_id": "device123_1694123456789",
  "device_id": "device123",
  "user_name": "john_doe",
  "part_number": 1,
  "total_parts": 5,
  "records": [
    {
      "type": "location",
      "timestamp": 1694123456789,
      "latitude": 32.0853,
      "longitude": 34.7818,
      "accuracy": 15.0,
      "altitude": 125.5,
      "speed": 45.2,
      "bearing": 245.8,
      "battery_level": 85,
      "network_type": "WiFi",
      "provider": "gps"
    },
    {
      "type": "driving",
      "timestamp": 1694123466789,
      "event_type": "driving_start",
      "location": {
        "latitude": 32.0863,
        "longitude": 34.7828,
        "accuracy": 12.0
      },
      "speed": 0,
      "bearing": 180.0
    }
  ]
}
```

### **Response Format**

#### **Partial Upload Response**
```json
{
  "status": "success",
  "message": "Batch part received",
  "sync_id": "device123_1694123456789",
  "part_number": 1,
  "total_parts": 5,
  "records_count": 50,
  "request_id": "a1b2c3d4"
}
```

#### **Complete Sync Response**
```json
{
  "status": "success",
  "message": "Sync completed successfully",
  "sync_id": "device123_1694123456789",
  "part_number": 5,
  "total_parts": 5,
  "records_count": 25,
  "sync_complete": true,
  "processing_results": {
    "location": {
      "2024-09-08": 150,
      "2024-09-09": 200
    },
    "driving": {
      "2024-09-08": 25,
      "2024-09-09": 30
    }
  },
  "request_id": "a1b2c3d4"
}
```

## 📱 Mobile App Implementation

### **1. Data Collection Strategy**

```javascript
class OfflineDataManager {
  constructor() {
    this.pendingData = [];
    this.syncInProgress = false;
    this.maxBatchSize = 100;
    this.maxRetries = 3;
  }

  // Store data locally while offline
  storeLocationData(locationData) {
    const record = {
      type: 'location',
      timestamp: Date.now(),
      ...locationData,
      stored_at: Date.now(),
      synced: false
    };
    
    this.pendingData.push(record);
    this.saveToLocalStorage();
  }

  storeDrivingData(drivingData) {
    const record = {
      type: 'driving',
      timestamp: Date.now(),
      ...drivingData,
      stored_at: Date.now(),
      synced: false
    };
    
    this.pendingData.push(record);
    this.saveToLocalStorage();
  }

  // Check if sync is needed
  needsSync() {
    return this.pendingData.filter(r => !r.synced).length > 0;
  }
}
```

### **2. Batch Upload Implementation**

```javascript
class BatchSyncManager {
  constructor(apiEndpoint, apiToken) {
    this.apiEndpoint = apiEndpoint;
    this.apiToken = apiToken;
    this.maxBatchSize = 100;
  }

  async syncPendingData(dataManager) {
    if (dataManager.syncInProgress) return;
    
    const unsyncedData = dataManager.pendingData.filter(r => !r.synced);
    if (unsyncedData.length === 0) return;

    dataManager.syncInProgress = true;
    
    try {
      // Sort data by timestamp to maintain order
      unsyncedData.sort((a, b) => a.timestamp - b.timestamp);
      
      // Split into batches
      const batches = this.createBatches(unsyncedData);
      const syncId = this.generateSyncId();
      
      // Upload each batch
      for (let i = 0; i < batches.length; i++) {
        const success = await this.uploadBatch(
          syncId,
          i + 1,
          batches.length,
          batches[i],
          dataManager.deviceId,
          dataManager.userName
        );
        
        if (!success) {
          throw new Error(`Failed to upload batch ${i + 1}`);
        }
        
        // Update progress
        this.onProgress?.(i + 1, batches.length);
      }
      
      // Mark data as synced only after complete success
      unsyncedData.forEach(record => record.synced = true);
      dataManager.saveToLocalStorage();
      
      this.onSyncComplete?.(unsyncedData.length);
      
    } catch (error) {
      this.onSyncError?.(error);
    } finally {
      dataManager.syncInProgress = false;
    }
  }

  createBatches(data) {
    const batches = [];
    for (let i = 0; i < data.length; i += this.maxBatchSize) {
      batches.push(data.slice(i, i + this.maxBatchSize));
    }
    return batches;
  }

  async uploadBatch(syncId, partNumber, totalParts, records, deviceId, userName) {
    const payload = {
      sync_id: syncId,
      device_id: deviceId,
      user_name: userName,
      part_number: partNumber,
      total_parts: totalParts,
      records: records.map(r => ({
        type: r.type,
        timestamp: r.timestamp,
        ...this.extractRecordData(r)
      }))
    };

    const response = await fetch(this.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiToken}`
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    
    if (!response.ok) {
      throw new Error(`Batch upload failed: ${result.message}`);
    }

    // Check if sync is complete
    if (result.sync_complete) {
      this.onSyncComplete?.(result.processing_results);
    }

    return true;
  }

  generateSyncId() {
    return `${this.deviceId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  extractRecordData(record) {
    const { stored_at, synced, ...recordData } = record;
    return recordData;
  }
}
```

### **3. Safe Data Cleanup**

```javascript
class DataCleanupManager {
  constructor(dataManager) {
    this.dataManager = dataManager;
    this.retentionDays = 7; // Keep synced data for 7 days
  }

  // Only delete data after successful sync confirmation
  cleanupSyncedData() {
    const cutoffTime = Date.now() - (this.retentionDays * 24 * 60 * 60 * 1000);
    
    this.dataManager.pendingData = this.dataManager.pendingData.filter(record => {
      // Keep unsynced data
      if (!record.synced) return true;
      
      // Keep recent synced data (safety buffer)
      if (record.stored_at > cutoffTime) return true;
      
      // Remove old synced data
      return false;
    });
    
    this.dataManager.saveToLocalStorage();
  }

  // Emergency cleanup if storage is full
  emergencyCleanup() {
    // Keep only last 1000 records and all unsynced data
    const unsynced = this.dataManager.pendingData.filter(r => !r.synced);
    const synced = this.dataManager.pendingData
      .filter(r => r.synced)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 1000 - unsynced.length);
    
    this.dataManager.pendingData = [...unsynced, ...synced];
    this.dataManager.saveToLocalStorage();
  }
}
```

## 🔧 Server-Side Features

### **1. Data Integrity**
- **Atomic Operations**: All parts must be received before processing
- **Checksum Validation**: Each part includes data integrity checks
- **Duplicate Detection**: Prevents duplicate sync sessions
- **Order Preservation**: Maintains chronological order across all parts

### **2. Error Handling**
- **Partial Upload Recovery**: Resume from failed parts
- **Validation Errors**: Detailed field-level error reporting
- **Storage Failures**: Graceful handling of disk space issues
- **Timeout Management**: Automatic cleanup of stale sync sessions

### **3. Security**
- **Authentication**: Same token-based auth as other endpoints
- **Rate Limiting**: Configurable limits on batch size and frequency
- **Input Sanitization**: Comprehensive validation of all data
- **Audit Logging**: Complete tracking of sync operations

## 📊 Configuration Options

### **Server Configuration**
```php
$maxBatchSize = 100;        // Records per batch
$maxBatchParts = 50;        // Maximum parts per sync
$tempRetentionHours = 24;   // Cleanup incomplete syncs after 24h
$maxSyncSessions = 100;     // Concurrent sync sessions limit
```

### **Mobile App Configuration**
```javascript
const config = {
  maxBatchSize: 100,          // Records per batch
  maxRetries: 3,              // Retry failed uploads
  retryDelay: 5000,           // 5 seconds between retries
  syncInterval: 300000,       // Check for sync every 5 minutes
  retentionDays: 7,           // Keep synced data for 7 days
  emergencyThreshold: 10000   // Emergency cleanup at 10k records
};
```

## 🎯 Benefits

### **For Mobile Apps**
1. **Offline Resilience**: Continue collecting data without internet
2. **Efficient Uploads**: Chunked uploads prevent timeouts
3. **Progress Tracking**: Real-time sync progress feedback
4. **Safe Cleanup**: Only delete data after confirmed sync
5. **Automatic Recovery**: Resume interrupted syncs

### **For Server**
1. **Data Integrity**: Guaranteed chronological ordering
2. **Scalability**: Handle large offline data collections
3. **Resource Management**: Controlled memory and storage usage
4. **Monitoring**: Complete audit trail of sync operations
5. **Flexibility**: Support mixed location and driving data

## 🚨 Error Scenarios & Solutions

### **Network Interruption During Sync**
- **Problem**: Upload fails mid-sync
- **Solution**: Resume from last successful part
- **Implementation**: Track completed parts, retry only failed ones

### **Server Storage Full**
- **Problem**: Cannot store batch parts
- **Solution**: Return specific error, app retries later
- **Implementation**: Disk space checks before accepting uploads

### **Data Corruption**
- **Problem**: Invalid data in batch
- **Solution**: Detailed validation errors, reject entire batch
- **Implementation**: Field-level validation with specific error messages

### **Duplicate Sync Sessions**
- **Problem**: App sends same data multiple times
- **Solution**: Unique sync IDs prevent duplicates
- **Implementation**: Check existing sync sessions before processing

This comprehensive system ensures reliable offline data collection and synchronization while maintaining data integrity and providing excellent user experience.
