# CORS Fix for Frontend Development

## Problem

Frontend development from localhost was failing with CORS error:
```
Access to fetch at 'https://mytrips-api.bahar.co.il/trips/' from origin 'http://localhost:3500' has been blocked by CORS policy: The 'Access-Control-Allow-Origin' header contains multiple values 'http://localhost:3500, *', but only one is allowed.
```

## Root Cause

Both nginx and FastAPI were adding CORS headers, causing duplicate headers which browsers reject.

## Solution

### Option 1: Let Nginx Handle CORS (Recommended)

**On the server, update nginx configuration:**

```bash
# Copy the fixed configuration
sudo cp /opt/dayplanner/deployment/nginx/mytrips-api-dev-friendly.conf /etc/nginx/sites-available/mytrips-api

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Restart backend to use production CORS settings
sudo systemctl restart dayplanner-backend
```

**The fixed nginx configuration:**
- Removes duplicate CORS headers from backend
- Handles preflight OPTIONS requests properly
- Allows localhost origins for development
- Supports both HTTP and HTTPS

### Option 2: Let FastAPI Handle CORS

**If you prefer FastAPI to handle CORS:**

1. **Update backend configuration:**
```python
# In backend/app/main.py, set:
nginx_handles_cors = False
```

2. **Update nginx configuration to NOT add CORS headers:**
```bash
# Remove all add_header directives from nginx config
# Keep only proxy settings
```

3. **Restart services:**
```bash
sudo systemctl restart dayplanner-backend
sudo systemctl reload nginx
```

## Testing the Fix

### 1. Test CORS Headers

```bash
# Test preflight request
curl -X OPTIONS "https://mytrips-api.bahar.co.il/trips/" \
  -H "Origin: http://localhost:3500" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  -v

# Should return:
# Access-Control-Allow-Origin: http://localhost:3500
# Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# Access-Control-Allow-Headers: Authorization, Content-Type, Accept, X-Requested-With
```

### 2. Test Actual Request

```bash
# Test actual API request
curl "https://mytrips-api.bahar.co.il/health" \
  -H "Origin: http://localhost:3500" \
  -v

# Should return health status with proper CORS headers
```

### 3. Test from Frontend

```javascript
// Test from browser console on http://localhost:3500
fetch('https://mytrips-api.bahar.co.il/health')
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
```

## Frontend Configuration

### Environment Variables

Make sure your frontend has the correct API base URL:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=https://mytrips-api.bahar.co.il
```

### API Client Configuration

```typescript
// In your API client
const apiClient = axios.create({
  baseURL: 'https://mytrips-api.bahar.co.il',
  withCredentials: false, // Set to true if you need cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## Verification Checklist

- [ ] Nginx configuration updated
- [ ] Backend CORS settings configured
- [ ] Services restarted
- [ ] Preflight requests work
- [ ] Actual API requests work
- [ ] Frontend can connect to API
- [ ] Authentication flow works
- [ ] No duplicate CORS headers in browser network tab

## Common Issues

### 1. Still Getting CORS Errors

**Check for duplicate headers:**
```bash
curl -X GET "https://mytrips-api.bahar.co.il/health" \
  -H "Origin: http://localhost:3500" \
  -v | grep -i "access-control"
```

**Should see only one of each header, not duplicates.**

### 2. 404 Errors

**Check nginx is proxying correctly:**
```bash
# Check nginx error logs
sudo tail -f /var/log/nginx/mytrips-api_error.log

# Check backend is running
sudo systemctl status dayplanner-backend
```

### 3. Authentication Issues

**Test login flow:**
```bash
# Test login
curl -X POST "https://mytrips-api.bahar.co.il/auth/login" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3500" \
  -d '{"email": "test@example.com", "password": "password123"}' \
  -v
```

## Production vs Development

### Development (localhost)
- CORS allows localhost origins
- More permissive headers
- Detailed error messages

### Production
- CORS restricted to production domains
- Minimal headers
- Generic error messages

## Files Changed

1. `deployment/nginx/mytrips-api-dev-friendly.conf` - Fixed nginx config
2. `backend/app/main.py` - Updated CORS middleware logic
3. `docs/CORS_FIX.md` - This documentation

## Next Steps

1. **Deploy the nginx configuration** to your server
2. **Restart services** on the server
3. **Test frontend connection** from localhost
4. **Verify authentication flow** works end-to-end
5. **Update frontend environment** variables if needed

The CORS issue should be resolved after applying these changes!
