SELECT 
    lr.id, 
    lr.device_id,
    d.device_name,
    lr.user_id, 
    lr.server_time, 
    lr.created_at 
FROM location_records lr
LEFT JOIN devices d ON lr.device_id = d.id
WHERE lr.server_time >= '2025-10-12 12:30:00'  -- Includes 12:30:00 exactly
AND d.device_name = 'device_aa9e19da71fc702b'
-- AND lr.device_id = '5'
ORDER BY lr.server_time DESC;