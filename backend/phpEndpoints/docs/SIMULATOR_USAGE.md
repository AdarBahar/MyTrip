# Real-Time Location Simulator

## Overview

The `simulate-realtime-drive.php` script simulates real-time location updates by sending data from the 3 test drive datasets to your location tracking API.

## Features

- ✅ Sends location updates in real-time with proper timing delays
- ✅ Supports all 3 test datasets (basic, detours, pauses)
- ✅ Configurable speed multiplier (run 10x faster, etc.)
- ✅ Works with both local and production environments
- ✅ Customizable username and device ID
- ✅ Colorful terminal output with progress tracking
- ✅ Success/error statistics

## Available Datasets

| Dataset | File | Points | Description |
|---------|------|--------|-------------|
| **basic** | `test_drive_log.jsonl` | 568 | Basic test drive route |
| **detours** | `test_drive_log_with_detours.jsonl` | 1,598 | Drive with detours and variations |
| **pauses** | `test_drive_log_with_pauses.jsonl` | 662 | Drive with pauses/stops |

## Usage

### Basic Usage

Run all datasets in sequence:
```bash
php simulate-realtime-drive.php
```

### Run Specific Dataset

```bash
# Run only the basic dataset
php simulate-realtime-drive.php --dataset=basic

# Run only the detours dataset
php simulate-realtime-drive.php --dataset=detours

# Run only the pauses dataset
php simulate-realtime-drive.php --dataset=pauses
```

### Speed Control

```bash
# Run at 10x speed (10 times faster)
php simulate-realtime-drive.php --speed=10

# Run at 0.5x speed (half speed, slower)
php simulate-realtime-drive.php --speed=0.5

# Run at 100x speed (very fast, for quick testing)
php simulate-realtime-drive.php --speed=100
```

### Environment Selection

```bash
# Run on local MAMP server (default)
php simulate-realtime-drive.php --env=local

# Run on production server
php simulate-realtime-drive.php --env=production
```

### Custom User and Device

```bash
# Use custom username and device ID
php simulate-realtime-drive.php --user=MyTestUser --device=device_test_123

# Combine with other options
php simulate-realtime-drive.php --dataset=detours --speed=10 --user=FastDriver --device=device_fast_001
```

### Combined Examples

```bash
# Quick test: Run basic dataset at 50x speed on local
php simulate-realtime-drive.php --dataset=basic --speed=50 --env=local

# Production test: Run all datasets at 10x speed
php simulate-realtime-drive.php --speed=10 --env=production

# Slow detailed test: Run pauses dataset at half speed
php simulate-realtime-drive.php --dataset=pauses --speed=0.5
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dataset=<name>` | Dataset to run: `basic`, `detours`, `pauses`, or `all` | `all` |
| `--speed=<factor>` | Speed multiplier (e.g., 10 = 10x faster) | `1.0` |
| `--env=<env>` | Environment: `local` or `production` | `local` |
| `--user=<name>` | Username to use for location updates | `TestUser` |
| `--device=<id>` | Device ID to use | `device_simulator_001` |
| `--help` | Show help message | - |

## Output Example

```
🚀 Real-Time Location Simulator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📂 Loading dataset: basic (dashboard/testLogs/test_drive_log.jsonl)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚗 Starting simulation: basic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Total points: 568
👤 Username: TestUser
📱 Device ID: device_simulator_001
🌐 API URL: http://localhost:8888/location/api/getloc.php
⚡ Speed: 10x
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ [1/568] 32.187830, 34.935401 | 🔋 99%
✓ [2/568] 32.187745, 34.935687 | 28.5 km/h | 🔋 99%
✓ [3/568] 32.186990, 34.935750 | 21.0 km/h | 🔋 99%
...

📊 Progress: 8.8% | Elapsed: 2.5s | Success: 50 | Errors: 0

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Simulation Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total points: 568
✓ Successful: 568
✗ Errors: 0
⏱️  Total time: 56.82s
⚡ Avg rate: 10.0 points/sec
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Viewing Results

### Option 1: Live Tracking Dashboard

1. Open the map viewer:
   ```
   http://localhost:8888/location/dashboard/map-test.php
   ```

2. Click "📡 Start Live Tracking"

3. Enter device ID: `device_simulator_001` (or your custom device ID)

4. Run the simulator in another terminal

5. Watch the location updates appear in real-time on the map!

### Option 2: API Endpoints

Check the latest location:
```bash
curl 'http://localhost:8888/location/api/live/latest.php?user=TestUser' \
  -H 'Authorization: Bearer 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='
```

Check history (last 24 hours):
```bash
curl 'http://localhost:8888/location/api/live/history.php?device=device_simulator_001&duration=86400&limit=1000' \
  -H 'Authorization: Bearer 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI='
```

### Option 3: Database Query

```sql
SELECT COUNT(*) 
FROM location_history_cache 
WHERE device_id = 'device_simulator_001';

SELECT * 
FROM device_last_position 
WHERE device_id = 'device_simulator_001';
```

## Troubleshooting

### Script Not Found

Make sure you're in the project root directory:
```bash
cd /Users/adar.bahar/Code/location-web
php simulate-realtime-drive.php
```

### Permission Denied

Make the script executable:
```bash
chmod +x simulate-realtime-drive.php
```

### Connection Errors

**Local environment:**
- Make sure MAMP is running
- Verify the URL: `http://localhost:8888/location/api/getloc.php`

**Production environment:**
- Check your internet connection
- Verify the API is accessible: `https://www.bahar.co.il/location/api/getloc.php`

### API Authentication Errors

The script uses the hardcoded API token. If you get 401 errors, verify the token in your `.env` file matches:
```
LOC_API_TOKEN=4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI=
```

## Use Cases

### 1. Testing Live Tracking UI

Run the simulator while viewing the live tracking dashboard to test real-time updates:

```bash
# Terminal 1: Start simulator at 10x speed
php simulate-realtime-drive.php --speed=10

# Browser: Open live tracking
# http://localhost:8888/location/dashboard/map-test.php
```

### 2. Populating Test Data

Quickly populate the database with test data:

```bash
# Run all datasets at 100x speed
php simulate-realtime-drive.php --speed=100
```

### 3. Testing Cache Cleanup

Test the 24-hour cache cleanup by running old data:

```bash
# Run simulation
php simulate-realtime-drive.php

# Wait or manually run cleanup
curl http://localhost:8888/location/cleanup-old-cache.php

# Verify cache is cleaned
curl http://localhost:8888/location/test-cache-diagnosis.php
```

### 4. Load Testing

Test API performance with rapid requests:

```bash
# Send 1,598 points as fast as possible
php simulate-realtime-drive.php --dataset=detours --speed=1000
```

### 5. Multi-Device Testing

Simulate multiple devices by running multiple instances:

```bash
# Terminal 1
php simulate-realtime-drive.php --device=device_car_001 --user=Driver1 --dataset=basic

# Terminal 2
php simulate-realtime-drive.php --device=device_car_002 --user=Driver2 --dataset=detours

# Terminal 3
php simulate-realtime-drive.php --device=device_car_003 --user=Driver3 --dataset=pauses
```

## Technical Details

### Timing Simulation

The simulator calculates delays between points based on the `client_time` field in the dataset:

```php
$timeDiff = ($point['client_time'] - $lastClientTime) / 1000; // ms to seconds
$delay = $timeDiff / $speedFactor;
usleep((int)($delay * 1000000)); // Sleep for calculated delay
```

### Data Sent to API

Each location update includes:
- `id` - Device ID
- `name` - Username
- `latitude` - GPS latitude
- `longitude` - GPS longitude
- `accuracy` - GPS accuracy in meters
- `altitude` - Altitude in meters (optional)
- `speed` - Speed in m/s (optional)
- `bearing` - Direction in degrees (optional)
- `battery_level` - Battery percentage (optional)
- `client_time` - Client timestamp in milliseconds

### API Endpoint

The script sends POST requests to:
- **Local:** `http://localhost:8888/location/api/getloc.php`
- **Production:** `https://www.bahar.co.il/location/api/getloc.php`

With headers:
```
Content-Type: application/json
Authorization: Bearer <token>
X-API-Token: <token>
```

## Next Steps

After running the simulator:

1. ✅ Check the live tracking dashboard to see the route
2. ✅ Query the history API to verify data was stored
3. ✅ Run the cache diagnosis to check data integrity
4. ✅ Test the cleanup script to verify old data removal
5. ✅ Update the UI to query history with different time ranges

## Related Files

- `simulate-realtime-drive.php` - Main simulator script
- `dashboard/testLogs/*.jsonl` - Test drive datasets
- `dashboard/map-test.php` - Live tracking viewer
- `api/getloc.php` - Location submission endpoint
- `api/live/history.php` - History query endpoint
- `cleanup-old-cache.php` - Cache cleanup script
- `test-cache-diagnosis.php` - Cache diagnostic tool

