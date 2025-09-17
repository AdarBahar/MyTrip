# Production Deployment Checklist

Use this checklist to ensure a successful production deployment of DayPlanner without Docker.

## Pre-Deployment Preparation

### ✅ Server Requirements
- [ ] Ubuntu/Debian server (18.04+ recommended)
- [ ] Minimum 2GB RAM, 2 CPU cores
- [ ] 20GB+ available disk space
- [ ] Root/sudo access
- [ ] Domain name configured (optional)

### ✅ External Services
- [ ] MySQL database accessible from server
- [ ] Database credentials available
- [ ] GraphHopper API key (for cloud routing) OR plan for self-hosted
- [ ] MapTiler API key
- [ ] SSL certificate ready (if using HTTPS)

### ✅ DNS Configuration
- [ ] Domain A record pointing to server IP
- [ ] WWW subdomain configured (optional)
- [ ] SSL certificate installed (if using HTTPS)

## Deployment Steps

### 1. ✅ Initial Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clone repository
sudo git clone https://github.com/AdarBahar/MyTrip.git /opt/dayplanner
cd /opt/dayplanner
```

### 2. ✅ Environment Configuration
```bash
# Copy and edit production environment
sudo cp deployment/production.env .env.production
sudo nano .env.production
```

**Required Environment Variables:**
- [ ] `DB_HOST` - MySQL server hostname
- [ ] `DB_NAME` - Database name
- [ ] `DB_USER` - Database username  
- [ ] `DB_PASSWORD` - Database password
- [ ] `APP_SECRET` - Secure random string (32+ characters)
- [ ] `APP_BASE_URL` - Your domain URL
- [ ] `CORS_ORIGINS` - Allowed origins for CORS
- [ ] `GRAPHHOPPER_API_KEY` - GraphHopper API key
- [ ] `MAPTILER_API_KEY` - MapTiler API key
- [ ] `NEXT_PUBLIC_API_BASE_URL` - Frontend API URL
- [ ] `NEXT_PUBLIC_MAPTILER_API_KEY` - MapTiler key for frontend

### 3. ✅ Automated Deployment
```bash
# Make scripts executable
sudo chmod +x deployment/scripts/*.sh

# Run deployment script
sudo deployment/scripts/deploy.sh
```

### 4. ✅ Manual Verification Steps
- [ ] Backend service running: `sudo systemctl status dayplanner-backend`
- [ ] Frontend service running: `sudo systemctl status dayplanner-frontend`
- [ ] Nginx configuration valid: `sudo nginx -t`
- [ ] Database connectivity: `curl http://localhost:8000/health`
- [ ] Frontend accessibility: `curl http://localhost:3500`
- [ ] Full application: `curl http://localhost/health`

## Post-Deployment Configuration

### ✅ SSL/HTTPS Setup (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Update environment for HTTPS
sudo nano .env.production
# Change APP_BASE_URL to https://yourdomain.com
# Change CORS_ORIGINS to https://yourdomain.com
# Change NEXT_PUBLIC_API_BASE_URL to https://yourdomain.com/api

# Restart services
sudo systemctl restart dayplanner-backend
sudo systemctl restart dayplanner-frontend
```

### ✅ Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### ✅ Self-Hosted GraphHopper (Optional)
```bash
# Run GraphHopper setup script
sudo deployment/scripts/setup-graphhopper.sh

# Verify GraphHopper is running
curl http://localhost:8989/health
```

## Testing and Validation

### ✅ Functional Tests
- [ ] Can access homepage
- [ ] Can create user account
- [ ] Can log in
- [ ] Can create a trip
- [ ] Can add days to trip
- [ ] Can add stops to days
- [ ] Can compute routes
- [ ] Maps are loading correctly

### ✅ Performance Tests
- [ ] Page load times acceptable
- [ ] API response times under 2 seconds
- [ ] No memory leaks in services
- [ ] Database queries optimized

### ✅ Security Tests
- [ ] HTTPS working (if configured)
- [ ] Security headers present
- [ ] No sensitive data in logs
- [ ] Database access restricted
- [ ] Services running as non-root user

## Monitoring and Maintenance

### ✅ Log Monitoring
```bash
# Application logs
sudo tail -f /var/log/dayplanner/*.log

# Service logs
sudo journalctl -u dayplanner-backend -f
sudo journalctl -u dayplanner-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/dayplanner_*.log
```

### ✅ Health Monitoring
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health  
curl http://localhost:3500

# Full application health
curl http://yourdomain.com/health
```

### ✅ Backup Setup
- [ ] Database backup script configured
- [ ] Application backup script configured
- [ ] Backup retention policy defined
- [ ] Backup restoration tested

## Troubleshooting

### Common Issues and Solutions

**Backend won't start:**
```bash
sudo journalctl -u dayplanner-backend -n 50
cd /opt/dayplanner/backend && source venv/bin/activate && python prestart.py
```

**Frontend won't start:**
```bash
sudo journalctl -u dayplanner-frontend -n 50
cd /opt/dayplanner/frontend && sudo -u www-data pnpm build
```

**Database connection issues:**
```bash
mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME
```

**Permission issues:**
```bash
sudo chown -R www-data:www-data /opt/dayplanner
```

**Nginx issues:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Rollback Plan

If deployment fails:
```bash
# Stop services
sudo systemctl stop dayplanner-frontend
sudo systemctl stop dayplanner-backend

# Restore from backup (if available)
sudo deployment/scripts/update.sh --rollback

# Or manual rollback
sudo git checkout previous-working-commit
sudo deployment/scripts/deploy.sh
```

## Success Criteria

Deployment is successful when:
- [ ] All services are running and healthy
- [ ] Application is accessible via web browser
- [ ] All core functionality works
- [ ] No errors in logs
- [ ] Performance is acceptable
- [ ] Security measures are in place

## Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure automated backups
3. Set up log rotation
4. Plan for scaling if needed
5. Document any customizations
6. Train team on maintenance procedures

---

**Deployment Date:** ___________  
**Deployed By:** ___________  
**Version:** ___________  
**Notes:** ___________
