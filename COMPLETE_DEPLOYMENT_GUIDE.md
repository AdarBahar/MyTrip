# 🚀 Complete Production Deployment Guide

This guide provides step-by-step instructions for deploying the MyTrips application to production with clean deployment and location database setup.

## 📋 Prerequisites

- Ubuntu/Debian server with root access
- MySQL database server
- Domain name configured (mytrips-api.bahar.co.il)
- SSH access to production server

## 🎯 Deployment Overview

### What This Guide Covers
1. **Clean Repository Deployment** - Only necessary files (70% smaller)
2. **Location Database Setup** - Separate database for location endpoints
3. **Service Configuration** - Systemd services for backend/frontend
4. **Nginx Configuration** - Reverse proxy and SSL
5. **Health Verification** - Ensure everything works

### Architecture
- **Main Database**: `baharc5_dayplanner` (existing trips, users, etc.)
- **Location Database**: `baharc5_location` (new location endpoints)
- **Backend**: FastAPI on port 8000
- **Frontend**: Next.js on port 3500
- **Nginx**: Reverse proxy on port 80/443

## 🚀 Step 1: Clean Repository Deployment

### Option A: Automated Deployment (Recommended)

```bash
# On production server
cd /opt/dayplanner
sudo git pull origin main
sudo ./deployment/scripts/deploy-app-login.sh
```

### Option B: Manual Clean Deployment

```bash
# Clone to temporary location
git clone https://github.com/AdarBahar/MyTrip.git /tmp/dayplanner-deploy
cd /tmp/dayplanner-deploy

# Create backup of current deployment
sudo cp -r /opt/dayplanner /opt/dayplanner-backups/backup-$(date +%Y%m%d_%H%M%S)

# Deploy only necessary files (70% smaller deployment)
sudo rsync -av --delete --exclude-from=.deployignore \
  /tmp/dayplanner-deploy/ /opt/dayplanner/

# Set ownership and cleanup
sudo chown -R www-data:www-data /opt/dayplanner
rm -rf /tmp/dayplanner-deploy
cd /opt/dayplanner
```

**What gets excluded:**
- Documentation files (`*.md`, `docs/`)
- Test files (`test_*.py`, `*_test.py`)
- Development scripts (`deploy_*.sh`, `fix_*.sh`)
- Development directories (`.git/`, `.vscode/`, `tools/`)
- Configuration files (`docker-compose.yml`, `Makefile`)

## 🗄️ Step 2: Database Configuration

### Main Database (Existing)
Your existing database configuration in `/opt/dayplanner/.env.production`:

```bash
# Main Database Configuration
DB_CLIENT=mysql
DB_HOST=srv1135.hstgr.io
DB_PORT=3306
DB_NAME=baharc5_dayplanner
DB_USER=baharc5_dayplanner
DB_PASSWORD=xbZeSoREl%c63Ttq
```

### Location Database (New)
Add location database configuration to `/opt/dayplanner/.env.production`:

```bash
# Location Database Configuration (Separate MySQL Database)
LOCATION_DB_CLIENT=mysql
# Leave LOCATION_DB_HOST empty to use same host as main database
LOCATION_DB_HOST=
LOCATION_DB_PORT=3306
LOCATION_DB_NAME=baharc5_location
LOCATION_DB_USER=baharc5_location
LOCATION_DB_PASSWORD="IObUn{,mL%OU"
```

### Edit Environment File

```bash
# Edit production environment file
sudo nano /opt/dayplanner/.env.production

# Add the location database variables above
# Save and exit (Ctrl+X, Y, Enter)
```

## 🔧 Step 3: Install Dependencies

### Backend Dependencies

```bash
cd /opt/dayplanner/backend

# Create/activate virtual environment
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### Frontend Dependencies

```bash
cd /opt/dayplanner/frontend

# Install Node.js dependencies
sudo -u www-data npm install
# OR if using pnpm:
sudo -u www-data pnpm install

# Build for production
sudo -u www-data npm run build
# OR if using pnpm:
sudo -u www-data pnpm build
```

## 🗃️ Step 4: Database Setup

### Create Location Database Tables

```bash
cd /opt/dayplanner/backend
source venv/bin/activate

# Load environment variables
export $(cat /opt/dayplanner/.env.production | grep -v '^#' | xargs)

# Create location database tables
python3 create_location_tables.py
```

### Run Main Database Migrations

```bash
# Run Alembic migrations for main database
alembic upgrade head
```

## ⚙️ Step 5: Service Configuration

### Copy Service Files

```bash
# Copy systemd service files
sudo cp /opt/dayplanner/deployment/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload
```

### Enable and Start Services

```bash
# Enable services to start on boot
sudo systemctl enable dayplanner-backend.service
sudo systemctl enable dayplanner-frontend.service

# Start backend service
sudo systemctl start dayplanner-backend.service

# Wait for backend to be ready, then start frontend
sleep 10
sudo systemctl start dayplanner-frontend.service
```

### Verify Services

```bash
# Check service status
sudo systemctl status dayplanner-backend.service
sudo systemctl status dayplanner-frontend.service

# Check logs if needed
sudo journalctl -u dayplanner-backend -f
sudo journalctl -u dayplanner-frontend -f
```

## 🌐 Step 6: Nginx Configuration

### Copy Nginx Configuration

```bash
# Copy nginx configuration
sudo cp /opt/dayplanner/deployment/nginx/mytrips-api.conf /etc/nginx/sites-available/

# Enable site
sudo ln -sf /etc/nginx/sites-available/mytrips-api.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## 🔍 Step 7: Health Verification

### Test Main Application

```bash
# Test main health endpoint
curl https://mytrips-api.bahar.co.il/health

# Expected response:
# {"status":"ok","timestamp":"2025-11-03T..."}
```

### Test Location Database

```bash
# Test location health endpoint
curl https://mytrips-api.bahar.co.il/location/health

# Expected response:
# {
#   "status": "ok",
#   "module": "location",
#   "database": {
#     "connected": true,
#     "database_name": "baharc5_location",
#     "database_user": "baharc5_location"
#   }
# }
```

### Test API Endpoints

```bash
# Test existing endpoints
curl https://mytrips-api.bahar.co.il/trips/
curl https://mytrips-api.bahar.co.il/users/me

# Test OpenAPI documentation
curl https://mytrips-api.bahar.co.il/docs
```

## 🧹 Step 8: Clean Up Existing Deployment (If Needed)

If you have an existing deployment with unnecessary files:

### Preview What Will Be Cleaned

```bash
# See what files will be removed (safe preview)
sudo /opt/dayplanner/deployment/scripts/preview-cleanup.sh
```

### Run Cleanup

```bash
# Clean up unnecessary files from existing deployment
sudo /opt/dayplanner/deployment/scripts/cleanup-production.sh
```

**What the cleanup does:**
- ✅ Creates backup before cleanup
- ✅ Stops services safely
- ✅ Removes unnecessary files (expect 70% size reduction)
- ✅ Restarts services
- ✅ Logs all operations

## 📊 Expected Results

### Before Clean Deployment
```
Deployment size: ~150MB
Files: ~2,500
Includes: docs/, *.md, test files, .git/, development scripts
```

### After Clean Deployment
```
Deployment size: ~45MB
Files: ~800
Includes: Only production-necessary files
Reduction: 70% smaller, 65% fewer files
```

### Database Configuration
- **Main Database**: Handles existing functionality (trips, users, places)
- **Location Database**: Handles new location endpoints (`/location/*`)
- **Dual Architecture**: Complete separation for security and scalability

## 🛠️ Troubleshooting

### Services Won't Start

```bash
# Check service logs
sudo journalctl -u dayplanner-backend -n 50
sudo journalctl -u dayplanner-frontend -n 50

# Check environment file
sudo cat /opt/dayplanner/.env.production | grep -E "(DB_|LOCATION_DB_)"

# Test database connectivity
cd /opt/dayplanner/backend
source venv/bin/activate
python3 -c "from app.core.config import settings; print(settings.database_url)"
python3 -c "from app.core.config import settings; print(settings.location_database_url)"
```

### Location Health Endpoint Fails

```bash
# Check location database configuration
sudo grep -A 10 "LOCATION_DB" /opt/dayplanner/.env.production

# Test location database connection manually
cd /opt/dayplanner/backend
source venv/bin/activate
python3 -c "
from app.core.location_database import location_engine
try:
    conn = location_engine.connect()
    result = conn.execute('SELECT 1, DATABASE(), USER()').fetchone()
    print(f'Connected to: {result[1]} as {result[2]}')
    conn.close()
except Exception as e:
    print(f'Connection failed: {e}')
"
```

### Rollback Deployment

```bash
# List available backups
ls -la /opt/dayplanner-backups/

# Restore from backup
sudo systemctl stop dayplanner-backend dayplanner-frontend
sudo rsync -av /opt/dayplanner-backups/backup-YYYYMMDD_HHMMSS/ /opt/dayplanner/
sudo chown -R www-data:www-data /opt/dayplanner
sudo systemctl start dayplanner-backend dayplanner-frontend
```

## 🎯 Maintenance Commands

### Service Management

```bash
# Restart services
sudo systemctl restart dayplanner-backend
sudo systemctl restart dayplanner-frontend

# View logs
sudo journalctl -u dayplanner-backend -f
sudo journalctl -u dayplanner-frontend -f

# Check status
sudo systemctl status dayplanner-backend
sudo systemctl status dayplanner-frontend
```

### Update Deployment

```bash
# Pull latest changes and deploy
cd /opt/dayplanner
sudo git pull origin main
sudo ./deployment/scripts/deploy-app-login.sh
```

### Database Maintenance

```bash
# Run new migrations
cd /opt/dayplanner/backend
source venv/bin/activate
export $(cat /opt/dayplanner/.env.production | grep -v '^#' | xargs)
alembic upgrade head
```

## ✅ Deployment Checklist

- [ ] Clean repository deployed (70% smaller)
- [ ] Environment file configured with both databases
- [ ] Backend dependencies installed
- [ ] Frontend built for production
- [ ] Location database tables created
- [ ] Main database migrations run
- [ ] Systemd services configured and running
- [ ] Nginx configured and running
- [ ] Main health endpoint working
- [ ] Location health endpoint working
- [ ] SSL certificate configured (if applicable)
- [ ] Cleanup script run (if needed)

**🎉 Your production deployment is complete and optimized!**

## 🔄 Quick Commands Reference

### Deployment Commands
```bash
# Full clean deployment
sudo ./deployment/scripts/deploy-app-login.sh

# Preview cleanup (safe)
sudo ./deployment/scripts/preview-cleanup.sh

# Run cleanup
sudo ./deployment/scripts/cleanup-production.sh

# Manual clean deployment
sudo rsync -av --delete --exclude-from=.deployignore /tmp/repo/ /opt/dayplanner/
```

### Service Commands
```bash
# Restart all services
sudo systemctl restart dayplanner-backend dayplanner-frontend nginx

# Check all service status
sudo systemctl status dayplanner-backend dayplanner-frontend nginx

# View logs
sudo journalctl -u dayplanner-backend -f
```

### Health Check Commands
```bash
# Test main application
curl https://mytrips-api.bahar.co.il/health

# Test location database
curl https://mytrips-api.bahar.co.il/location/health

# Test API endpoints
curl https://mytrips-api.bahar.co.il/trips/
curl https://mytrips-api.bahar.co.il/docs
```

### Database Commands
```bash
# Load environment and run migrations
cd /opt/dayplanner/backend
source venv/bin/activate
export $(cat /opt/dayplanner/.env.production | grep -v '^#' | xargs)
alembic upgrade head

# Test database connections
python3 -c "from app.core.config import settings; print('Main DB:', settings.database_url)"
python3 -c "from app.core.config import settings; print('Location DB:', settings.location_database_url)"
```

---

**📞 Support**: If you encounter issues, check the troubleshooting section or review service logs for detailed error information.
