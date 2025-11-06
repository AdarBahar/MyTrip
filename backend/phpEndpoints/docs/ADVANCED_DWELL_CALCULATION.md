# Advanced Dwell Calculation

This document describes the advanced dwell calculation system implemented in the location tracking dashboard, which provides optimized, gap-aware dwell time calculation with spatial indexing and quality filtering.

## Overview

The advanced dwell calculation system improves upon the basic clustering approach by:

1. **Gap Awareness**: Pauses counting when there are gaps longer than 1 hour between data points
2. **Quality Filtering**: Ignores poor accuracy points and high-speed movement
3. **Spatial Optimization**: Uses spatial keys and indexing for efficient processing
4. **Incremental Processing**: Calculates dwell sessions incrementally rather than from scratch
5. **Database Storage**: Optionally stores pre-calculated sessions for faster display

## Key Features

### 1. Gap-Aware Dwell Calculation

Unlike simple time-based calculations, the advanced system:
- Only counts actual logged time periods
- Pauses counting during gaps > 1 hour (configurable)
- Assumes user left and returned for large gaps
- Provides more accurate representation of actual dwell time

### 2. Quality-Based Filtering

The system automatically filters out:
- Points with accuracy > 100 meters (configurable)
- Points where speed > 5 km/h (not dwelling)
- Outlier points that indicate GPS errors

### 3. Spatial Clustering

Uses grid-based spatial keys for consistent clustering:
- Generates spatial cluster IDs using coordinate grids
- Maintains consistent clustering across processing runs
- Supports adaptive radius based on accuracy

### 4. Session Merging

Intelligently merges adjacent sessions:
- Combines sessions if user left briefly (< 5 minutes) and returned
- Maintains spatial proximity requirements
- Recalculates centroids and statistics

## Database Schema

### Core Tables

#### `dwell_sessions`
Stores canonical dwell session data:
```sql
- id: Session identifier
- device_id: Device/user identifier  
- cluster_id: Spatial cluster identifier
- centroid_lat/lon: Session center point
- start_time/end_time: Session boundaries (milliseconds)
- duration_s: Actual dwell time in seconds
- points_count: Number of location points
- max_gap_ms: Largest gap within session
- accuracy_avg: Average GPS accuracy
- confidence_score: Quality score (0-100)
```

#### `dwell_daily`
Daily rollup summaries for quick access:
```sql
- device_id, day, cluster_id: Composite key
- total_dwell_s: Total time spent at location
- visits: Number of separate visits
- avg_confidence: Average quality score
```

#### `dwell_processing_state`
Tracks incremental processing state:
```sql
- device_id: Device identifier
- last_processed_time: Last processed timestamp
- current_session_id: Active session (if any)
```

### Spatial Optimization

The system adds spatial columns to `location_records`:
```sql
- geohash_7: Grid-based spatial key (~150m resolution)
- geom: PostGIS-compatible point geometry
```

With corresponding indexes:
- `ix_loc_geohash`: Fast spatial clustering
- `sidx_loc_geom`: Spatial range queries
- `ix_loc_device_time`: Temporal ordering

## Configuration

### Dashboard Settings

In `dashboard/index.php`:

```php
// Dwell calculation configuration
$useAdvancedDwell = true;        // Enable gap-aware calculation
$useDatabaseDwell = false;       // Use pre-calculated sessions
```

### Algorithm Parameters

```php
// In DwellSessionManager class
$maxGapMs = 3600000;            // 1 hour gap threshold
$minDwellSeconds = 60;          // Minimum 1 minute dwell
$maxAccuracyThreshold = 100;    // 100m accuracy limit
$maxSpeedKmh = 5;               // 5 km/h speed limit
$mergeGapMs = 300000;           // 5 minute merge threshold
```

## Setup Instructions

### 1. Database Migration

Run the spatial optimization migration:

```bash
php scripts/migrate-spatial-optimization.php
```

This adds:
- Spatial columns and indexes
- Dwell session tables
- Processing state tracking
- Stored procedures and views

### 2. Initial Data Processing

Process existing location data:

```bash
# Process all devices
php scripts/process-dwell-sessions.php --clear

# Process specific device
php scripts/process-dwell-sessions.php --device=user123

# Process date range
php scripts/process-dwell-sessions.php --from=2024-01-01 --to=2024-01-31
```

### 3. Enable Database Mode

Update dashboard configuration:

```php
$useDatabaseDwell = true;
```

## Usage Modes

### 1. Real-Time Advanced Calculation

- `$useAdvancedDwell = true`
- `$useDatabaseDwell = false`
- Calculates dwell sessions on-demand with gap awareness
- No database migration required
- Slower for large datasets

### 2. Database-Optimized Mode

- `$useAdvancedDwell = true`
- `$useDatabaseDwell = true`
- Uses pre-calculated sessions from database
- Requires migration and initial processing
- Fast display, suitable for production

### 3. Legacy Mode

- `$useAdvancedDwell = false`
- `$useDatabaseDwell = false`
- Simple time-based clustering
- Backward compatibility mode

## Quality Metrics

### Confidence Score

Each dwell session includes a confidence score (0-100) based on:

- **Accuracy**: Lower scores for poor GPS accuracy
- **Point Density**: Penalizes sessions with too few points
- **Gap Consistency**: Reduces score for large internal gaps
- **Duration Bonus**: Higher scores for longer, more reliable sessions

### Business Rules

1. **Adaptive Radius**: Cluster distance ≤ max(defined_radius, accuracy_avg)
2. **Minimum Dwell**: Only sessions ≥ 1 minute to reduce noise
3. **Merge Adjacent**: Combine sessions with brief departures (≤ 5 minutes)
4. **Outlier Filter**: Remove impossible speed jumps and poor accuracy
5. **Confidence Scoring**: Quality assessment for reliability

## Performance Considerations

### Incremental Processing

- Process new points only since last run
- Maintain rolling state per device
- O(1) per point instead of O(N) rescans

### Spatial Indexing

- Grid-based clustering for consistent results
- Spatial indexes for efficient range queries
- Geohash-based spatial keys

### Memory Management

- Process data in daily chunks
- Stream processing for large datasets
- Configurable batch sizes

## Monitoring and Maintenance

### Regular Processing

Set up cron job for incremental processing:

```bash
# Process new data every hour
0 * * * * php /path/to/scripts/process-dwell-sessions.php
```

### Quality Monitoring

Monitor confidence scores and session statistics:

```sql
-- Average confidence by device
SELECT device_id, AVG(confidence_score) as avg_confidence
FROM dwell_sessions 
WHERE start_time >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY)) * 1000
GROUP BY device_id;

-- Sessions with low confidence
SELECT * FROM recent_dwell_sessions 
WHERE confidence_score < 70
ORDER BY start_time DESC;
```

### Performance Tuning

- Monitor processing times and adjust chunk sizes
- Review spatial index usage with EXPLAIN
- Consider partitioning for very large datasets

## Troubleshooting

### Common Issues

1. **Migration Fails**: Check MySQL/MariaDB spatial function support
2. **No Sessions Created**: Verify quality filters aren't too restrictive
3. **Poor Performance**: Check spatial indexes are being used
4. **Low Confidence**: Review accuracy thresholds and point density

### Debug Mode

Enable detailed logging in DwellSessionManager:

```php
error_log("Processing device $deviceId: " . count($points) . " points");
```

### Data Validation

Verify session quality:

```sql
-- Check for unrealistic dwell times
SELECT * FROM dwell_sessions 
WHERE duration_s > 86400 OR duration_s < 60;

-- Verify spatial clustering
SELECT cluster_id, COUNT(*), AVG(confidence_score)
FROM dwell_sessions 
GROUP BY cluster_id 
HAVING COUNT(*) > 100;
```
