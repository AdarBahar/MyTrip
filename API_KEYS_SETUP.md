# 🔑 API Keys Setup Guide

MyTrip requires API keys for maps and routing functionality. This guide will help you get free API keys and configure them properly.

## 🗺️ **MapTiler API Key (Required for Maps)**

### **Why do I need this?**
MapTiler provides the map tiles, styles, and geocoding services for the interactive maps in MyTrip.

### **Getting a Free API Key:**

1. **Sign up at MapTiler**:
   - Visit: https://www.maptiler.com/
   - Click "Sign Up" (free account)
   - Verify your email

2. **Get your API key**:
   - Go to your dashboard
   - Click "API Keys" in the sidebar
   - Copy your default API key

3. **Free tier includes**:
   - 100,000 map loads per month
   - Geocoding and search
   - Multiple map styles
   - No credit card required

### **Configuration:**

Add your API key to the environment files:

#### **For Docker Development:**
```bash
# Edit .env.docker
NEXT_PUBLIC_MAPTILER_API_KEY=your_actual_api_key_here
```

#### **For Production Hosting:**
```bash
# Edit .env.production  
NEXT_PUBLIC_MAPTILER_API_KEY=your_actual_api_key_here
```

#### **For Local Development:**
```bash
# Edit .env
NEXT_PUBLIC_MAPTILER_API_KEY=your_actual_api_key_here
```

## 🛣️ **GraphHopper API Key (Optional for Cloud Routing)**

### **Why do I need this?**
GraphHopper provides routing and navigation services. You can use either:
- **Self-hosted GraphHopper** (included in Docker setup) - No API key needed
- **GraphHopper Cloud** (for production) - Requires API key

### **Getting a Free API Key:**

1. **Sign up at GraphHopper**:
   - Visit: https://www.graphhopper.com/
   - Click "Sign Up" (free account)
   - Verify your email

2. **Get your API key**:
   - Go to your dashboard
   - Click "API Keys"
   - Create a new API key

3. **Free tier includes**:
   - 1,000 requests per day
   - Multiple routing profiles (car, bike, foot)
   - Route optimization
   - No credit card required

### **Configuration:**

#### **For Cloud Routing (Production):**
```bash
# Edit .env.production
GRAPHHOPPER_MODE=cloud
GRAPHHOPPER_API_KEY=your_actual_api_key_here
GRAPHHOPPER_BASE_URL=https://graphhopper.com/api/1
```

#### **For Self-hosted Routing (Docker):**
```bash
# Edit .env.docker (default setup)
GRAPHHOPPER_MODE=selfhost
GRAPHHOPPER_BASE_URL=http://graphhopper:8989
# No API key needed for self-hosted
```

## 🚀 **Quick Setup Commands**

### **Docker Development:**
```bash
# 1. Get your MapTiler API key from https://www.maptiler.com/
# 2. Edit the Docker environment file
nano .env.docker

# 3. Replace the placeholder:
# NEXT_PUBLIC_MAPTILER_API_KEY=get-free-key-from-maptiler-com
# With your actual key:
# NEXT_PUBLIC_MAPTILER_API_KEY=your_actual_key_here

# 4. Restart Docker containers
./scripts/docker-dev.sh
```

### **Production Hosting:**
```bash
# 1. Get API keys from:
#    - MapTiler: https://www.maptiler.com/
#    - GraphHopper: https://www.graphhopper.com/ (optional)

# 2. Edit the production environment file
nano .env.production

# 3. Replace the placeholders with your actual keys
# 4. Build and deploy
./scripts/build-for-hosting.sh
```

## ✅ **Verification**

### **Check if API keys are working:**

1. **MapTiler (Maps)**:
   - Visit any trip page (e.g., http://localhost:3500/trips/test1)
   - Maps should load and center on the trip destination
   - No yellow "API Key Required" message
   - Small overlay shows destination name and helpful message

2. **GraphHopper (Routing)**:
   - Create a trip with multiple stops
   - Routes should calculate between stops
   - No routing errors in console

### **Common Issues:**

#### **Maps not loading:**
- ❌ API key contains placeholder text
- ❌ API key is invalid or expired
- ❌ Domain not authorized (for production)
- ✅ Check browser console for 403 errors

#### **Routing not working:**
- ❌ GraphHopper API key invalid
- ❌ Self-hosted GraphHopper container not running
- ❌ Wrong GRAPHHOPPER_BASE_URL
- ✅ Check backend logs for routing errors

#### **Place creation errors (422 Unprocessable Entity):**
- ❌ Missing coordinates (lat/lon) in place data
- ❌ Invalid coordinate values (NaN, null, undefined)
- ❌ Coordinates out of valid range (lat: -90 to 90, lon: -180 to 180)
- ✅ Check browser console for validation errors
- ✅ Ensure selected places have valid coordinates
- ✅ **Fixed**: Coordinate extraction from PlacesSearch results

## 🆓 **Cost Information**

### **MapTiler Free Tier:**
- **100,000 map loads/month** - Very generous for most applications
- **Unlimited geocoding** within fair use
- **No credit card required**
- **Upgrade available** if you exceed limits

### **GraphHopper Free Tier:**
- **1,000 requests/day** - Good for development and small applications
- **Multiple routing profiles**
- **No credit card required**
- **Self-hosted option** available for unlimited use

### **Self-hosted Alternative:**
- **GraphHopper** - Included in Docker setup, completely free
- **OpenStreetMap data** - Free and open source
- **No API limits** - Run on your own infrastructure

## 🔒 **Security Notes**

- **Never commit API keys** to version control
- **Use environment variables** for all API keys
- **Restrict API key domains** in production
- **Monitor API usage** to avoid unexpected charges
- **Rotate keys regularly** for security

## 📞 **Support**

If you have issues with API keys:

1. **Check the browser console** for error messages
2. **Verify API key format** (no extra spaces or characters)
3. **Test API keys directly** using the provider's documentation
4. **Check rate limits** if requests are failing
5. **Contact API providers** for account-specific issues

Your MyTrip application will work perfectly once the API keys are configured! 🎉
