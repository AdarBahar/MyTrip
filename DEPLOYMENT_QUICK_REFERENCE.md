# 🚀 Deployment Quick Reference Card

**Fast reference for common deployment scenarios and troubleshooting**

---

## ⚡ **Quick Deployment Commands**

### **New Server Setup (Fresh Install)**
```bash
# 1. Server preparation
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.9 python3.9-venv nginx postgresql git

# 2. Clone and deploy
git clone https://github.com/AdarBahar/MyTrip.git
cd MyTrip
./deploy_complete_endpoints.sh

# 3. Configure SSL
sudo certbot --nginx -d your-domain.com
```

### **Existing Server Update**
```bash
# Quick update for existing deployment
git pull origin main
./deploy_complete_endpoints.sh

# Or manual update
scp -i ~/.ssh/hetzner-mytrips-api backend/app/api/trips/router.py root@SERVER:/opt/dayplanner/backend/app/api/trips/
ssh -i ~/.ssh/hetzner-mytrips-api root@SERVER "systemctl restart dayplanner-backend"
```

### **Emergency Rollback**
```bash
# Rollback to previous commit
cd /opt/dayplanner
git checkout HEAD~1
sudo systemctl restart dayplanner-backend
```

---

## 🚨 **Common Issues & Quick Fixes**

### **502 Bad Gateway**
```bash
# Check service status
sudo systemctl status dayplanner-backend

# Restart service
sudo systemctl restart dayplanner-backend

# Check logs
sudo journalctl -u dayplanner-backend -f

# Test backend directly
curl http://localhost:8000/health
```

### **500 Internal Server Error**
```bash
# Check for import errors
cd /opt/dayplanner/backend && source venv/bin/activate
python -c "from app.main import app; print('Import OK')"

# Fix common import issues
sed -i 's/Stop\.deleted_at\.is_(None)/# Stop has no deleted_at/' app/api/trips/router.py
sed -i 's/TripSchema/Trip/' app/schemas/trip_complete.py

# Restart service
sudo systemctl restart dayplanner-backend
```

### **SSL Certificate Issues**
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL
openssl s_client -connect your-domain.com:443
```

### **Database Connection Issues**
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql -c "\l"

# Check app database connection
cd /opt/dayplanner/backend && source venv/bin/activate
python -c "from app.database import engine; engine.connect(); print('DB OK')"
```

---

## 🔧 **Configuration Templates**

### **Environment Variables (.env)**
```bash
DATABASE_URL=postgresql://dayplanner_user:password@localhost/dayplanner
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ALLOWED_ORIGINS=["https://your-domain.com"]
LOG_LEVEL=INFO
```

### **Nginx Configuration**
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
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Systemd Service**
```ini
[Unit]
Description=DayPlanner Backend API Service
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/dayplanner/backend
Environment=PATH=/opt/dayplanner/backend/venv/bin
ExecStart=/opt/dayplanner/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📊 **Health Check Commands**

### **Service Status**
```bash
# Backend service
sudo systemctl status dayplanner-backend

# Nginx
sudo systemctl status nginx

# PostgreSQL
sudo systemctl status postgresql

# All services
sudo systemctl status dayplanner-backend nginx postgresql
```

### **API Testing**
```bash
# Health endpoint
curl https://your-domain.com/health

# API endpoints
curl "https://your-domain.com/trips?format=modern&size=2"
curl "https://your-domain.com/trips?format=short&size=2"

# Swagger docs
curl https://your-domain.com/docs

# With authentication
curl -H "Authorization: Bearer TOKEN" "https://your-domain.com/trips?format=short"
```

### **Log Monitoring**
```bash
# Real-time application logs
sudo journalctl -u dayplanner-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# All logs combined
sudo journalctl -u dayplanner-backend -f & sudo tail -f /var/log/nginx/error.log
```

---

## 🔄 **Maintenance Commands**

### **Updates**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update application
cd /opt/dayplanner
git pull origin main
sudo systemctl restart dayplanner-backend

# Update SSL certificates
sudo certbot renew
```

### **Backups**
```bash
# Database backup
sudo -u postgres pg_dump dayplanner > backup_$(date +%Y%m%d).sql

# Application backup
tar -czf app_backup_$(date +%Y%m%d).tar.gz /opt/dayplanner/backend

# Restore database
sudo -u postgres psql dayplanner < backup_YYYYMMDD.sql
```

### **Performance Monitoring**
```bash
# System resources
htop
df -h
free -h

# Network connections
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :443

# Database connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 🎯 **Deployment Scenarios**

### **Scenario 1: Fresh Ubuntu Server**
```bash
# Complete setup from scratch
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.9 python3.9-venv nginx postgresql git certbot python3-certbot-nginx

git clone https://github.com/AdarBahar/MyTrip.git
cd MyTrip
./deploy_complete_endpoints.sh

sudo certbot --nginx -d your-domain.com
```

### **Scenario 2: Update Existing Deployment**
```bash
# Update with new features
cd /opt/dayplanner
git pull origin main
./deploy_complete_endpoints.sh

# Test deployment
./test_production_deployment.py --token "TOKEN" --owner-id "OWNER_ID"
```

### **Scenario 3: Fix Broken Deployment**
```bash
# Emergency fix
cd /opt/dayplanner/backend
source venv/bin/activate

# Fix import errors
python -c "from app.main import app; print('Testing imports...')"

# Common fixes
sed -i 's/Stop\.deleted_at\.is_(None)/# Fixed: Stop has no deleted_at/' app/api/trips/router.py
sed -i 's/from app.schemas.trip import TripSchema/from app.schemas.trip import Trip/' app/schemas/trip_complete.py

sudo systemctl restart dayplanner-backend
sudo systemctl status dayplanner-backend
```

### **Scenario 4: SSL Setup**
```bash
# Automatic SSL with Let's Encrypt
sudo certbot --nginx -d your-domain.com

# Manual SSL certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/mytrips.key \
  -out /etc/ssl/certs/mytrips.crt

# Update nginx config for SSL
sudo nano /etc/nginx/sites-available/mytrips-api.conf
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📞 **Emergency Contacts**

### **Critical Commands**
```bash
# Stop everything
sudo systemctl stop dayplanner-backend nginx

# Start everything
sudo systemctl start postgresql nginx dayplanner-backend

# Check everything
sudo systemctl status postgresql nginx dayplanner-backend
```

### **File Locations**
- **App**: `/opt/dayplanner/backend/`
- **Config**: `/opt/dayplanner/backend/.env`
- **Nginx**: `/etc/nginx/sites-available/mytrips-api.conf`
- **Service**: `/etc/systemd/system/dayplanner-backend.service`
- **SSL**: `/etc/letsencrypt/live/your-domain.com/`
- **Logs**: `journalctl -u dayplanner-backend` & `/var/log/nginx/`

### **Test Commands**
```bash
# Quick health check
curl https://your-domain.com/health

# Full test suite
./test_production_deployment.py --token "TOKEN" --owner-id "OWNER_ID"

# Manual API test
curl -H "Authorization: Bearer TOKEN" "https://your-domain.com/trips?format=short&size=2"
```

---

*Quick Reference | Version: 2.0 | Last Updated: 2025-01-16*
