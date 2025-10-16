# 🔍 Deployment Troubleshooting Flowchart

**Step-by-step troubleshooting guide for common deployment issues**

---

## 🚨 **Issue: Cannot Access API (No Response)**

```
🌐 Can you access the domain?
├─ NO → Check DNS settings
│   ├─ Domain pointing to correct IP?
│   ├─ DNS propagation complete? (use dig your-domain.com)
│   └─ Firewall blocking ports 80/443?
│
└─ YES → Continue to next step
```

```
🔌 Is Nginx running?
├─ Check: sudo systemctl status nginx
├─ NO → Start Nginx: sudo systemctl start nginx
│   ├─ Fails to start?
│   │   ├─ Check config: sudo nginx -t
│   │   ├─ Check logs: sudo journalctl -u nginx
│   │   └─ Fix config errors
│   └─ Still failing? Check port conflicts: sudo netstat -tlnp | grep :80
│
└─ YES → Continue to next step
```

```
🔧 Is backend service running?
├─ Check: sudo systemctl status dayplanner-backend
├─ NO → Start service: sudo systemctl start dayplanner-backend
│   ├─ Fails to start?
│   │   ├─ Check logs: sudo journalctl -u dayplanner-backend -f
│   │   ├─ Import errors? → Go to "Import Error Section"
│   │   ├─ Database errors? → Go to "Database Error Section"
│   │   └─ Permission errors? → Go to "Permission Error Section"
│   └─ Port conflicts? sudo netstat -tlnp | grep :8000
│
└─ YES → Continue to next step
```

---

## 🚨 **Issue: 502 Bad Gateway**

```
🔍 502 Bad Gateway Troubleshooting
├─ Backend service running?
│   ├─ NO → sudo systemctl start dayplanner-backend
│   └─ YES → Check if responding
│       ├─ Test: curl http://localhost:8000/health
│       ├─ NO response → Check backend logs
│       │   └─ sudo journalctl -u dayplanner-backend -f
│       └─ Responds → Check Nginx proxy config
│
├─ Nginx proxy configuration correct?
│   ├─ Check: sudo nginx -t
│   ├─ Errors? → Fix config file
│   │   └─ /etc/nginx/sites-available/mytrips-api.conf
│   └─ OK → Check upstream connection
│       ├─ proxy_pass http://127.0.0.1:8000; correct?
│       └─ Backend listening on correct port?
│
└─ Network/Firewall issues?
    ├─ Check: sudo netstat -tlnp | grep :8000
    ├─ Backend not listening? → Check service config
    └─ Firewall blocking? → Check ufw status
```

**Quick Fix Commands:**
```bash
# Restart both services
sudo systemctl restart dayplanner-backend nginx

# Check both statuses
sudo systemctl status dayplanner-backend nginx

# Test backend directly
curl http://localhost:8000/health

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

---

## 🚨 **Issue: 500 Internal Server Error**

```
🐛 500 Internal Server Error Troubleshooting
├─ Check application logs first
│   └─ sudo journalctl -u dayplanner-backend -f
│
├─ Import/Module Errors?
│   ├─ Common patterns in logs:
│   │   ├─ "ImportError: cannot import name 'StopSchema'"
│   │   ├─ "ImportError: cannot import name 'TripSchema'"
│   │   └─ "AttributeError: type object 'Stop' has no attribute 'deleted_at'"
│   │
│   └─ Fix import errors:
│       ├─ cd /opt/dayplanner/backend
│       ├─ source venv/bin/activate
│       ├─ Test imports: python -c "from app.main import app"
│       └─ Apply fixes (see Import Error Section)
│
├─ Database Connection Errors?
│   ├─ Patterns: "connection refused", "authentication failed"
│   ├─ Check PostgreSQL: sudo systemctl status postgresql
│   ├─ Test connection: sudo -u postgres psql -c "\l"
│   └─ Check DATABASE_URL in .env file
│
├─ Configuration Errors?
│   ├─ Check .env file exists and has correct values
│   ├─ Check file permissions: ls -la /opt/dayplanner/backend/.env
│   └─ Validate config: python -c "from app.core.config import settings"
│
└─ Runtime Errors?
    ├─ Check for specific error in logs
    ├─ Memory issues? → Check: free -h
    ├─ Disk space? → Check: df -h
    └─ Database migration needed? → alembic upgrade head
```

**Quick Fix Commands:**
```bash
# Test imports manually
cd /opt/dayplanner/backend && source venv/bin/activate
python -c "from app.main import app; print('Import successful')"

# Fix common import issues
sed -i 's/from app.schemas.trip import TripSchema/from app.schemas.trip import Trip/' app/schemas/trip_complete.py
sed -i 's/Stop\.deleted_at\.is_(None)/# Stop model has no deleted_at/' app/api/trips/router.py

# Restart and check
sudo systemctl restart dayplanner-backend
sudo systemctl status dayplanner-backend
```

---

## 🚨 **Issue: SSL/HTTPS Problems**

```
🔒 SSL/HTTPS Troubleshooting
├─ Certificate exists?
│   ├─ Check: sudo certbot certificates
│   ├─ NO → Get certificate: sudo certbot --nginx -d your-domain.com
│   └─ YES → Check expiry date
│
├─ Nginx SSL configuration?
│   ├─ Check config: sudo nginx -t
│   ├─ SSL directives present?
│   │   ├─ ssl_certificate path correct?
│   │   └─ ssl_certificate_key path correct?
│   └─ Reload: sudo systemctl reload nginx
│
├─ Certificate validation?
│   ├─ Test: openssl s_client -connect your-domain.com:443
│   ├─ Certificate chain complete?
│   ├─ Certificate matches domain?
│   └─ Certificate not expired?
│
└─ Firewall/Network?
    ├─ Port 443 open? → sudo ufw status
    ├─ DNS pointing to correct IP?
    └─ CDN/Proxy interfering?
```

**Quick Fix Commands:**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL connection
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check Nginx SSL config
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🚨 **Issue: Database Connection Problems**

```
🗄️ Database Connection Troubleshooting
├─ PostgreSQL running?
│   ├─ Check: sudo systemctl status postgresql
│   ├─ NO → Start: sudo systemctl start postgresql
│   └─ YES → Check connectivity
│
├─ Database exists?
│   ├─ Check: sudo -u postgres psql -c "\l"
│   ├─ NO → Create: sudo -u postgres createdb dayplanner
│   └─ YES → Check user permissions
│
├─ User permissions correct?
│   ├─ Test: psql -h localhost -U dayplanner_user -d dayplanner -c "SELECT 1;"
│   ├─ Fails → Check user exists and has permissions
│   │   ├─ sudo -u postgres psql -c "\du"
│   │   └─ Grant permissions if needed
│   └─ Works → Check application config
│
├─ DATABASE_URL correct?
│   ├─ Check .env file: cat /opt/dayplanner/backend/.env | grep DATABASE_URL
│   ├─ Format: postgresql://user:pass@host:port/database
│   ├─ Test from app: python -c "from app.database import engine; engine.connect()"
│   └─ Update if incorrect
│
└─ Network/Firewall?
    ├─ PostgreSQL listening? → sudo netstat -tlnp | grep :5432
    ├─ Firewall blocking? → Check local connections
    └─ pg_hba.conf allows connections?
```

**Quick Fix Commands:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "\l"

# Test app database connection
cd /opt/dayplanner/backend && source venv/bin/activate
python -c "from app.database import engine; engine.connect(); print('DB connection OK')"

# Check DATABASE_URL
grep DATABASE_URL /opt/dayplanner/backend/.env
```

---

## 🚨 **Issue: Import/Module Errors**

```
📦 Import Error Troubleshooting
├─ Virtual environment activated?
│   ├─ Check: which python (should show venv path)
│   ├─ NO → source /opt/dayplanner/backend/venv/bin/activate
│   └─ YES → Check dependencies
│
├─ Dependencies installed?
│   ├─ Check: pip list | grep fastapi
│   ├─ Missing → pip install -r requirements.txt
│   └─ Present → Check specific imports
│
├─ Specific import errors?
│   ├─ "StopSchema not found"
│   │   └─ Fix: Use "Stop as StopSchema" in imports
│   ├─ "TripSchema not found"
│   │   └─ Fix: Use "Trip" instead of "TripSchema"
│   ├─ "Stop has no attribute deleted_at"
│   │   └─ Fix: Remove Stop.deleted_at filter
│   └─ Other module errors → Check file exists and syntax
│
└─ Python path issues?
    ├─ Check PYTHONPATH
    ├─ Check working directory
    └─ Check __init__.py files exist
```

**Common Import Fixes:**
```bash
cd /opt/dayplanner/backend
source venv/bin/activate

# Fix StopSchema import
sed -i 's/from app.schemas.stop import StopSchema/from app.schemas.stop import Stop as StopSchema/' app/api/trips/router.py
sed -i 's/from app.schemas.stop import StopSchema/from app.schemas.stop import Stop as StopSchema/' app/api/days/router.py

# Fix TripSchema import
sed -i 's/from app.schemas.trip import TripSchema/from app.schemas.trip import Trip/' app/schemas/trip_complete.py
sed -i 's/trip: TripSchema/trip: Trip/' app/schemas/trip_complete.py

# Fix Stop.deleted_at issue
sed -i 's/Stop\.deleted_at\.is_(None)/# Stop model has no deleted_at/' app/api/trips/router.py

# Test imports
python -c "from app.main import app; print('All imports successful')"
```

---

## 🚨 **Issue: Permission Errors**

```
🔐 Permission Error Troubleshooting
├─ File ownership correct?
│   ├─ Check: ls -la /opt/dayplanner/backend/
│   ├─ Wrong owner → sudo chown -R www-data:www-data /opt/dayplanner
│   └─ Correct → Check file permissions
│
├─ File permissions correct?
│   ├─ Check: ls -la /opt/dayplanner/backend/.env
│   ├─ Should be readable by service user
│   ├─ Fix: sudo chmod 644 /opt/dayplanner/backend/.env
│   └─ Directory permissions: sudo chmod 755 /opt/dayplanner/backend
│
├─ Service user correct?
│   ├─ Check service file: cat /etc/systemd/system/dayplanner-backend.service
│   ├─ User=www-data or appropriate user
│   ├─ User exists? → id www-data
│   └─ User can access files? → sudo -u www-data ls /opt/dayplanner/backend
│
└─ SELinux/AppArmor?
    ├─ Check if enabled: sestatus or aa-status
    ├─ Blocking access? → Check audit logs
    └─ Disable temporarily for testing
```

**Quick Permission Fixes:**
```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/dayplanner

# Fix permissions
sudo chmod -R 755 /opt/dayplanner/backend
sudo chmod 644 /opt/dayplanner/backend/.env

# Check service user can access
sudo -u www-data ls -la /opt/dayplanner/backend/

# Restart service
sudo systemctl restart dayplanner-backend
```

---

## ✅ **Final Verification Checklist**

After fixing any issues, run this verification:

```bash
# 1. Service status
sudo systemctl status dayplanner-backend nginx postgresql

# 2. Health check
curl https://your-domain.com/health

# 3. API endpoints
curl "https://your-domain.com/trips?format=modern&size=2"
curl "https://your-domain.com/trips?format=short&size=2"

# 4. SSL check
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# 5. Logs check (no errors)
sudo journalctl -u dayplanner-backend --since "5 minutes ago"

# 6. Full test suite
./test_production_deployment.py --token "TOKEN" --owner-id "OWNER_ID"
```

---

*Troubleshooting Guide | Version: 2.0 | Last Updated: 2025-01-16*
