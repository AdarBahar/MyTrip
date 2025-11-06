# History API Troubleshooting Guide

## Issue: `/live/history.php` Returns Only 1 Record Despite 1002 in Database

### Problem Description

When querying the history endpoint:
```bash
curl 'https://www.bahar.co.il/location/api/live/history.php?device=device_aa9e19da71fc702b&duration=86400&limit=1000' \
  -H 'Authorization: Bearer TOKEN'
```

**Expected:** 1002 location records  
**Actual:** Only 1 record returned

Database query confirms 1002 records exist:
```sql
SELECT COUNT(*) FROM location_history_cache WHERE device_id = 'device_aa9e19da71fc702b'
-- Returns: 1002
```

---

## Root Cause Analysis

### Investigation Results

Using the diagnostic script `test-cache-diagnosis.php`, we discovered:

1. **Total records in cache:** 1002
2. **Records within last 24 hours:** Only 1
3. **Server time range:** 
   - Oldest: `2025-10-23 14:13:18` (5 days ago)
   - Newest: `2025-10-28 12:58:20` (3 hours ago)
   - Span: 118 hours (~5 days)

### The Problem

The `location_history_cache` table is designed to store **only the last 24 hours** of data for fast queries. However, it contained 1001 old records from 4-5 days ago.

The API query filters by:
```sql
WHERE lhc.server_time >= DATE_SUB(NOW(), INTERVAL :duration SECOND)
```

With `duration=86400` (24 hours), only records with `server_time` in the last 24 hours are returned.

### Why Old Records Existed

1. **Cleanup cron job not running** - The `api/cron/cleanup-location-cache.php` script should run hourly to remove old records
2. **Historical data migration** - Old records were inserted without proper `server_time` values
3. **Recent fix** - The `LocationDataManager` was recently fixed to properly populate `server_time` using `NOW()`

---

## Solution

### Immediate Fix: Clean Up Old Cache Records

Created `cleanup-old-cache.php` script to remove records older than 24 hours:

```php
DELETE FROM location_history_cache 
WHERE server_time < DATE_SUB(NOW(), INTERVAL 24 HOUR)
```

**Results:**
- Deleted 1013 old records
- Cache now contains only 2 recent records (last 24 hours)
- API now correctly returns all available recent records

### Long-term Fix: Automated Cleanup

The existing cron job at `api/cron/cleanup-location-cache.php` should be scheduled to run hourly:

```bash
# Add to crontab
0 * * * * /usr/bin/php /path/to/location/api/cron/cleanup-location-cache.php
```

Or via cPanel:
- **Command:** `php /home/baharc5/public_html/location/api/cron/cleanup-location-cache.php`
- **Schedule:** Every hour (`0 * * * *`)

---

## Deployment Steps

### 1. Deploy Cleanup Script to Production

Add to `deploy_prod.sh`:
```bash
"$LOCAL_BASE/cleanup-old-cache.php:$FTP_REMOTE_BASE/cleanup-old-cache.php"
```

### 2. Run Cleanup on Production

```bash
curl https://www.bahar.co.il/location/cleanup-old-cache.php
```

### 3. Verify Results

```bash
curl https://www.bahar.co.il/location/test-cache-diagnosis.php
```

Check that:
- "Records within last 24 hours" matches "Total records"
- No records older than 24 hours exist

### 4. Test History API

```bash
curl 'https://www.bahar.co.il/location/api/live/history.php?device=device_aa9e19da71fc702b&duration=86400&limit=1000' \
  -H 'Authorization: Bearer TOKEN'
```

Should now return all records in the cache.

---

## Additional Issue: `/locations.php` Authentication Failure

### Problem

```bash
curl 'https://www.bahar.co.il/location/api/locations.php?user=Adar&limit=10' \
  -H 'Authorization: Bearer TOKEN'
```

Returns:
```json
{
  "status": "error",
  "message": "Valid API token required",
  "error_code": 401
}
```

### Possible Causes

1. **Different `.env` configuration** - Production might have a different `LOC_API_TOKEN`
2. **ModSecurity blocking** - Server firewall might block `Authorization` header
3. **Environment variable loading** - `.env` file might not be loaded properly

### Workaround: Use X-API-Token Header

The authentication middleware supports multiple header formats:

```bash
# Method 1: X-API-Token header (recommended for production)
curl 'https://www.bahar.co.il/location/api/locations.php?user=Adar&limit=1000' \
  -H 'X-API-Token: 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='

# Method 2: Authorization Bearer (standard)
curl 'https://www.bahar.co.il/location/api/locations.php?user=Adar&limit=1000' \
  -H 'Authorization: Bearer 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='

# Method 3: Query parameter (testing only)
curl 'https://www.bahar.co.il/location/api/locations.php?user=Adar&limit=1000&api_token=4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='
```

### Investigation Steps

1. **Check production `.env` file:**
   ```bash
   # Via FTP or cPanel File Manager
   cat /home/baharc5/public_html/location/.env | grep LOC_API_TOKEN
   ```

2. **Test with X-API-Token header:**
   ```bash
   curl 'https://www.bahar.co.il/location/api/locations.php?user=Adar&limit=10' \
     -H 'X-API-Token: YOUR_TOKEN'
   ```

3. **Check security logs:**
   ```bash
   curl 'https://www.bahar.co.il/location/api/logs.html'
   ```
   Look for authentication failures with details.

---

## Correct CURL Commands for Testing

### Last 24 Hours History (Cache Endpoint)

```bash
curl -X GET \
  'https://www.bahar.co.il/location/api/live/history.php?device=device_aa9e19da71fc702b&duration=86400&limit=1000' \
  -H 'Authorization: Bearer 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='
```

### Full History (Database Endpoint)

```bash
# Last 7 days
curl -X GET \
  'https://www.bahar.co.il/location/api/locations.php?user=Adar&date_from=2025-10-21&date_to=2025-10-28&limit=1000' \
  -H 'X-API-Token: 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='

# All time
curl -X GET \
  'https://www.bahar.co.il/location/api/locations.php?user=Adar&limit=1000' \
  -H 'X-API-Token: 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='
```

---

## Summary

### ✅ Fixed Issues

1. **Cache cleanup** - Created script to remove old records
2. **Diagnostic tools** - Created `test-cache-diagnosis.php` for troubleshooting
3. **Documentation** - Documented the issue and solution

### 🔧 Action Required

1. **Deploy cleanup script** to production
2. **Run cleanup** on production to remove old cache records
3. **Set up cron job** for automated hourly cleanup
4. **Test authentication** on `/locations.php` endpoint
5. **Update UI guide** with correct authentication headers

### 📊 Expected Results After Fix

- `/live/history.php` returns all records within the specified duration
- Cache table contains only records from the last 24 hours
- Automated cleanup prevents old data accumulation
- Both endpoints work with proper authentication

