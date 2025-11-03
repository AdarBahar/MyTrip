# Location Database Deployment Configuration

## 🔒 Production Environment Variables

Add these to your production `.env.production` file:

```bash
# Location Database Configuration (Production)
LOCATION_DB_CLIENT=mysql
# Leave LOCATION_DB_HOST empty to use same host as main database
LOCATION_DB_HOST=
LOCATION_DB_PORT=3306
LOCATION_DB_NAME=baharc5_location
LOCATION_DB_USER=baharc5_location
LOCATION_DB_PASSWORD="IObUn{,mL%OU"
```

## 🚀 Deployment Steps

1. **Update Environment File**
   ```bash
   # On production server
   nano /opt/dayplanner/.env.production
   # Add the location database variables above
   ```

2. **Create Location Database Tables**
   ```bash
   cd /opt/dayplanner/backend
   source venv/bin/activate
   python3 create_location_tables.py
   ```

3. **Test Location Health Endpoint**
   ```bash
   # After deployment
   curl https://mytrips-api.bahar.co.il/location/health
   ```

4. **Restart Services**
   ```bash
   sudo systemctl restart dayplanner-backend
   sudo systemctl restart dayplanner-frontend
   ```

## ✅ Expected Health Response

```json
{
  "status": "ok",
  "module": "location",
  "database": {
    "connected": true,
    "database_name": "baharc5_location",
    "database_user": "baharc5_location",
    "test_query": 1,
    "expected_database": "baharc5_location",
    "expected_user": "baharc5_location"
  },
  "timestamp": "2024-11-03T15:30:00Z"
}
```

## 🔧 Troubleshooting

If health check fails:
1. Verify database credentials are correct
2. Check database user has proper permissions
3. Ensure database `baharc5_location` exists
4. Check network connectivity to database host

## 📋 Ready for PHP Migration

Once health check passes, the location module is ready for your PHP endpoint migration!
