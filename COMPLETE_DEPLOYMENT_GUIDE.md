# 🚀 Complete Deployment Guide - MyTrip API

**Comprehensive guide for deploying the MyTrip API with complete endpoints and short format features**

---

## 📋 **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [Manual Deployment](#manual-deployment)
4. [SSL Configuration](#ssl-configuration)
5. [Common Issues & Troubleshooting](#common-issues--troubleshooting)
6. [Production Configuration](#production-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Rollback Procedures](#rollback-procedures)

---

## 🔧 **Prerequisites**

### **Server Requirements**
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 20GB free space
- **Network**: Public IP with ports 80, 443, and 8000 accessible

### **Software Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
  python3.9 python3.9-venv python3-pip \
  nginx certbot python3-certbot-nginx \
  postgresql postgresql-contrib \
  git curl wget htop

# Install Node.js (for frontend if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### **Local Requirements**
- **SSH Key**: Access to server via SSH key
- **Git Access**: Repository access to `https://github.com/AdarBahar/MyTrip.git`
- **Domain**: Domain name pointing to server IP (for SSL)

---

## ⚡ **Quick Deployment**

### **Option 1: Automated Deployment (Recommended)**

```bash
# 1. Clone repository locally
git clone https://github.com/AdarBahar/MyTrip.git
cd MyTrip

# 2. Run automated deployment
./deploy_complete_endpoints.sh

# 3. Test deployment
./test_production_deployment.py \
  --token "YOUR_JWT_TOKEN" \
  --owner-id "YOUR_OWNER_ID"
```

### **Option 2: Existing Server Update**

If you already have the API running and just need to update:

```bash
# Quick update for existing deployment
scp -i ~/.ssh/hetzner-mytrips-api \
  backend/app/api/trips/router.py \
  backend/app/api/days/router.py \
  backend/app/schemas/trip_complete.py \
  backend/app/schemas/trip_short.py \
  backend/app/schemas/day.py \
  root@YOUR_SERVER_IP:/opt/dayplanner/backend/app/

ssh -i ~/.ssh/hetzner-mytrips-api root@YOUR_SERVER_IP
sudo systemctl restart dayplanner-backend
sudo systemctl status dayplanner-backend
```

---

## 🔨 **Manual Deployment**

### **Step 1: Server Setup**

```bash
# Connect to server
ssh -i ~/.ssh/your-key root@YOUR_SERVER_IP

# Create application directory
sudo mkdir -p /opt/dayplanner
sudo chown $USER:$USER /opt/dayplanner
cd /opt/dayplanner

# Clone repository
git clone https://github.com/AdarBahar/MyTrip.git .
```

### **Step 2: Backend Setup**

```bash
# Navigate to backend
cd /opt/dayplanner/backend

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
cp .env.example .env
nano .env  # Configure your environment variables
```

### **Step 3: Database Setup**

```bash
# Create PostgreSQL database
sudo -u postgres createdb dayplanner
sudo -u postgres createuser dayplanner_user
sudo -u postgres psql -c "ALTER USER dayplanner_user PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dayplanner TO dayplanner_user;"

# Run migrations
cd /opt/dayplanner/backend
source venv/bin/activate
alembic upgrade head
```

### **Step 4: Service Configuration**

```bash
# Copy systemd service file
sudo cp deployment/systemd/dayplanner-backend.service /etc/systemd/system/

# Edit service file if needed
sudo nano /etc/systemd/system/dayplanner-backend.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable dayplanner-backend
sudo systemctl start dayplanner-backend
sudo systemctl status dayplanner-backend
```

---

## 🔒 **SSL Configuration**

### **Option 1: Automatic SSL with Certbot (Recommended)**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Configure nginx
sudo cp deployment/nginx/mytrips-api.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/mytrips-api.conf /etc/nginx/sites-enabled/

# Edit nginx config
sudo nano /etc/nginx/sites-available/mytrips-api.conf
# Update server_name to your domain

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### **Option 2: Manual SSL Setup**

```bash
# Generate SSL certificate manually
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/mytrips-api.key \
  -out /etc/ssl/certs/mytrips-api.crt

# Use the HTTPS nginx config
sudo cp deployment/nginx/mytrips-api-https.conf /etc/nginx/sites-available/mytrips-api.conf
sudo systemctl reload nginx
```

### **SSL Nginx Configuration Example**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🚨 **Common Issues & Troubleshooting**

### **502 Bad Gateway**

**Symptoms**: Nginx returns 502 error
**Causes & Solutions**:

```bash
# 1. Check if backend service is running
sudo systemctl status dayplanner-backend

# 2. Check backend logs
sudo journalctl -u dayplanner-backend -f

# 3. Check if port 8000 is listening
sudo netstat -tlnp | grep :8000

# 4. Test backend directly
curl http://localhost:8000/health

# 5. Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# 6. Common fixes:
# - Restart backend service
sudo systemctl restart dayplanner-backend

# - Check environment variables
cd /opt/dayplanner/backend
source venv/bin/activate
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"

# - Check database connection
python -c "from app.database import engine; engine.connect()"
```

### **500 Internal Server Error**

**Symptoms**: API returns 500 errors
**Debugging**:

```bash
# 1. Check application logs
sudo journalctl -u dayplanner-backend -f

# 2. Check for import errors
cd /opt/dayplanner/backend
source venv/bin/activate
python -c "from app.main import app; print('Import successful')"

# 3. Check specific modules
python -c "from app.api.trips.router import router; print('Trips router OK')"
python -c "from app.schemas.trip_complete import TripCompleteResponse; print('Trip complete schema OK')"

# 4. Check database migrations
alembic current
alembic upgrade head

# 5. Common fixes for our recent changes:
# - Fix Stop.deleted_at error
sed -i 's/Stop\.deleted_at\.is_(None)/# Stop model has no deleted_at/' \
  /opt/dayplanner/backend/app/api/trips/router.py

# - Fix import errors
sed -i 's/from app.schemas.trip import TripSchema/from app.schemas.trip import Trip/' \
  /opt/dayplanner/backend/app/schemas/trip_complete.py
```

### **SSL Certificate Issues**

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check nginx SSL config
sudo nginx -t

# Common SSL fixes:
# - Update certificate paths in nginx
# - Check firewall rules for port 443
sudo ufw allow 443
```

### **Database Connection Issues**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
sudo -u postgres psql -c "\l"

# Test connection with app credentials
psql -h localhost -U dayplanner_user -d dayplanner -c "SELECT 1;"

# Check database URL in environment
cd /opt/dayplanner/backend
source venv/bin/activate
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### **Permission Issues**

```bash
# Fix file permissions
sudo chown -R www-data:www-data /opt/dayplanner
sudo chmod -R 755 /opt/dayplanner

# Fix service permissions
sudo chown root:root /etc/systemd/system/dayplanner-backend.service
sudo chmod 644 /etc/systemd/system/dayplanner-backend.service

# Fix nginx permissions
sudo chown root:root /etc/nginx/sites-available/mytrips-api.conf
sudo chmod 644 /etc/nginx/sites-available/mytrips-api.conf
```

---

## ⚙️ **Production Configuration**

### **Environment Variables (.env)**

```bash
# Database
DATABASE_URL=postgresql://dayplanner_user:password@localhost/dayplanner

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME="MyTrip API"
VERSION=1.0.0

# External Services
GRAPHHOPPER_API_KEY=your-graphhopper-key
GOOGLE_MAPS_API_KEY=your-google-maps-key

# Logging
LOG_LEVEL=INFO
```

### **Nginx Production Configuration**

```nginx
# /etc/nginx/sites-available/mytrips-api.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### **Systemd Service Configuration**

```ini
# /etc/systemd/system/dayplanner-backend.service
[Unit]
Description=DayPlanner Backend API Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/dayplanner/backend
Environment=PATH=/opt/dayplanner/backend/venv/bin
ExecStart=/opt/dayplanner/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/dayplanner/backend

[Install]
WantedBy=multi-user.target
```

---

## 📊 **Monitoring & Maintenance**

### **Health Monitoring**

```bash
# Create monitoring script
cat > /opt/dayplanner/monitor.sh << 'EOF'
#!/bin/bash
# Health monitoring script

API_URL="https://your-domain.com"
LOG_FILE="/var/log/dayplanner-monitor.log"

# Check API health
if curl -f -s "$API_URL/health" > /dev/null; then
    echo "$(date): API is healthy" >> $LOG_FILE
else
    echo "$(date): API is down - restarting service" >> $LOG_FILE
    systemctl restart dayplanner-backend
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}% - cleanup needed" >> $LOG_FILE
fi
EOF

chmod +x /opt/dayplanner/monitor.sh

# Add to crontab
echo "*/5 * * * * /opt/dayplanner/monitor.sh" | sudo crontab -
```

### **Log Rotation**

```bash
# Configure log rotation
sudo tee /etc/logrotate.d/dayplanner << 'EOF'
/var/log/dayplanner-monitor.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

### **Backup Script**

```bash
# Create backup script
cat > /opt/dayplanner/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/dayplanner"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump dayplanner > $BACKUP_DIR/db_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /opt/dayplanner/backend

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/dayplanner/backup.sh

# Schedule daily backups
echo "0 2 * * * /opt/dayplanner/backup.sh" | sudo crontab -
```

---

## 🔄 **Rollback Procedures**

### **Quick Rollback**

```bash
# Rollback to previous git commit
cd /opt/dayplanner
git log --oneline -5  # See recent commits
git checkout PREVIOUS_COMMIT_HASH

# Restart service
sudo systemctl restart dayplanner-backend
sudo systemctl status dayplanner-backend
```

### **Database Rollback**

```bash
# Rollback database migration
cd /opt/dayplanner/backend
source venv/bin/activate
alembic downgrade -1  # Go back one migration

# Or rollback to specific revision
alembic downgrade REVISION_ID
```

### **Emergency Rollback**

```bash
# Restore from backup
cd /opt/dayplanner
sudo systemctl stop dayplanner-backend

# Restore database
sudo -u postgres dropdb dayplanner
sudo -u postgres createdb dayplanner
sudo -u postgres psql dayplanner < /opt/backups/dayplanner/db_BACKUP_DATE.sql

# Restore application
tar -xzf /opt/backups/dayplanner/app_BACKUP_DATE.tar.gz -C /

sudo systemctl start dayplanner-backend
```

---

## ✅ **Deployment Verification Checklist**

```bash
# 1. Service Status
sudo systemctl status dayplanner-backend

# 2. Health Check
curl https://your-domain.com/health

# 3. API Endpoints
curl https://your-domain.com/trips?format=modern
curl https://your-domain.com/trips?format=short

# 4. SSL Certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# 5. Database Connection
cd /opt/dayplanner/backend && source venv/bin/activate
python -c "from app.database import engine; engine.connect(); print('DB OK')"

# 6. Logs Check
sudo journalctl -u dayplanner-backend --since "5 minutes ago"

# 7. Performance Test
./test_production_deployment.py --token "TOKEN" --owner-id "OWNER_ID"
```

---

## 🔧 **Advanced Configuration**

### **Load Balancing Setup**

```bash
# For high-traffic deployments, set up multiple backend instances
# /etc/nginx/sites-available/mytrips-api-lb.conf

upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Docker Deployment (Alternative)**

```dockerfile
# Dockerfile for containerized deployment
FROM python:3.9-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dayplanner
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: dayplanner
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### **Performance Optimization**

```bash
# Optimize PostgreSQL for production
sudo nano /etc/postgresql/13/main/postgresql.conf

# Add these optimizations:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### **Security Hardening**

```bash
# Firewall configuration
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # Block direct access to backend

# Fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create API rate limiting jail
sudo tee /etc/fail2ban/jail.local << 'EOF'
[nginx-req-limit]
enabled = true
filter = nginx-req-limit
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/error.log
findtime = 600
bantime = 7200
maxretry = 10
EOF
```

## 📊 **Monitoring & Alerting**

### **Prometheus + Grafana Setup**

```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-2.40.0.linux-amd64 /opt/prometheus

# Configure Prometheus
sudo tee /opt/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dayplanner-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
    scrape_interval: 5s
EOF

# Create systemd service for Prometheus
sudo tee /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/opt/prometheus/prometheus --config.file=/opt/prometheus/prometheus.yml --storage.tsdb.path=/opt/prometheus/data
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable prometheus
sudo systemctl start prometheus
```

### **Application Metrics**

```python
# Add to backend/app/main.py for metrics endpoint
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 📞 **Support & Resources**

### **Quick Reference Commands**

```bash
# Service Management
sudo systemctl status dayplanner-backend
sudo systemctl restart dayplanner-backend
sudo systemctl reload nginx

# Logs
sudo journalctl -u dayplanner-backend -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Database
sudo -u postgres psql dayplanner
cd /opt/dayplanner/backend && source venv/bin/activate && alembic current

# SSL
sudo certbot certificates
sudo certbot renew
sudo nginx -t

# Testing
curl https://your-domain.com/health
curl https://your-domain.com/docs
./test_production_deployment.py --token "TOKEN" --owner-id "OWNER_ID"
```

### **Emergency Contacts & Resources**

- **Repository**: https://github.com/AdarBahar/MyTrip.git
- **API Documentation**: https://your-domain.com/docs
- **Swagger UI**: https://your-domain.com/docs
- **Health Check**: https://your-domain.com/health
- **Logs Location**: `/var/log/nginx/` and `journalctl -u dayplanner-backend`
- **Configuration Files**: `/opt/dayplanner/backend/.env`
- **Backup Location**: `/opt/backups/dayplanner/`

### **Common File Locations**

```bash
# Application
/opt/dayplanner/backend/          # Main application
/opt/dayplanner/backend/.env      # Environment configuration
/opt/dayplanner/backend/venv/     # Python virtual environment

# System Services
/etc/systemd/system/dayplanner-backend.service  # Service definition
/etc/nginx/sites-available/mytrips-api.conf     # Nginx configuration
/etc/letsencrypt/live/your-domain.com/          # SSL certificates

# Logs
/var/log/nginx/access.log         # Nginx access logs
/var/log/nginx/error.log          # Nginx error logs
journalctl -u dayplanner-backend  # Application logs

# Database
/var/lib/postgresql/13/main/      # PostgreSQL data
/etc/postgresql/13/main/          # PostgreSQL configuration
```

**For issues, check the troubleshooting section above or review the service logs for specific error messages.**

---

*Last Updated: 2025-01-16 | Version: 2.0 | Commit: cc47969*
