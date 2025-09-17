# DayPlanner User-Space Deployment Guide

Deploy DayPlanner without root access using user-level tools and process managers.

## Prerequisites

- **User account** on hosting server (no root required)
- **SSH access** to the server
- **MySQL database** accessible from server
- **Internet access** for downloading dependencies
- **Ports 3500 and 8000** available for your user

## Quick Start

### 1. Clone Repository
```bash
# On your hosting server
git clone https://github.com/AdarBahar/MyTrip.git ~/dayplanner
cd ~/dayplanner
```

### 2. Configure Environment
```bash
# Copy and edit user-space environment
cp deployment/user-space/user-production.env .env.production
nano .env.production
```

**Required Environment Variables:**
- `DB_HOST` - Your MySQL server hostname
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `APP_SECRET` - Secure random string (32+ characters)
- `GRAPHHOPPER_API_KEY` - GraphHopper API key
- `MAPTILER_API_KEY` - MapTiler API key

### 3. Deploy Application
```bash
# Make scripts executable
chmod +x deployment/user-space/*.sh

# Run deployment
./deployment/user-space/deploy-user.sh
```

## What Gets Installed

The deployment script will:

1. **Install Node.js via NVM** - User-level Node.js installation
2. **Install PM2** - Process manager for auto-restart
3. **Setup Python venv** - Backend dependencies
4. **Build frontend** - Production Next.js build
5. **Configure PM2** - Process management
6. **Run migrations** - Database setup
7. **Start services** - Backend and frontend

## Access Your Application

After deployment:
- **Frontend:** `http://your-server-ip:3500`
- **Backend API:** `http://your-server-ip:8000`
- **API Docs:** `http://your-server-ip:8000/docs`

## Management Commands

### Service Management
```bash
# Start services
~/dayplanner/start.sh

# Stop services
~/dayplanner/stop.sh

# Restart services
~/dayplanner/restart.sh

# Check status
~/dayplanner/status.sh
```

### PM2 Commands
```bash
# Check service status
pm2 status

# View logs
pm2 logs

# Restart specific service
pm2 restart dayplanner-backend
pm2 restart dayplanner-frontend

# Stop all services
pm2 stop all

# Start all services
pm2 start all
```

### Database Operations
```bash
# Run migrations
./deployment/user-space/migrate-user.sh

# Check migration status
./deployment/user-space/migrate-user.sh --status

# Dry run migrations
./deployment/user-space/migrate-user.sh --dry-run
```

### Application Updates
```bash
# Update from Git
./deployment/user-space/update-user.sh

# Rollback to previous version
./deployment/user-space/update-user.sh --rollback
```

## File Structure

```
~/dayplanner/                 # Application directory
├── backend/                  # FastAPI backend
├── frontend/                 # Next.js frontend
├── logs/                     # Application logs
├── .env.production          # Environment configuration
├── ecosystem.config.js      # PM2 configuration
├── start.sh                 # Start services
├── stop.sh                  # Stop services
├── restart.sh               # Restart services
└── status.sh                # Check status

~/dayplanner-backups/        # Backup directory
├── deployment_YYYYMMDD_HHMMSS/  # Code backups
└── db_backup_YYYYMMDD_HHMMSS.sql.gz  # Database backups
```

## Troubleshooting

### Services Won't Start
```bash
# Check PM2 status
pm2 status

# View logs
pm2 logs

# Check specific service logs
pm2 logs dayplanner-backend
pm2 logs dayplanner-frontend
```

### Database Connection Issues
```bash
# Test database connection
cd ~/dayplanner/backend
source venv/bin/activate
python prestart.py
```

### Frontend Build Issues
```bash
# Rebuild frontend
cd ~/dayplanner/frontend
source ~/.nvm/nvm.sh
pnpm install
pnpm build
```

### Port Already in Use
```bash
# Check what's using the ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :3500

# Kill processes if needed
pkill -f "uvicorn"
pkill -f "node.*server.js"
```

### Permission Issues
```bash
# Fix file permissions
chmod +x ~/dayplanner/*.sh
chmod +x ~/dayplanner/deployment/user-space/*.sh
```

## Environment Configuration

### Development vs Production
```bash
# For development (local testing)
APP_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3500,http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# For production (replace with your domain/IP)
APP_BASE_URL=https://yourdomain.com:8000
CORS_ORIGINS=https://yourdomain.com:3500,https://yourdomain.com:8000
NEXT_PUBLIC_API_BASE_URL=https://yourdomain.com:8000
```

### Custom Ports
If ports 3500/8000 are not available:
```bash
# In .env.production
BACKEND_PORT=8080
FRONTEND_PORT=3000

# Update URLs accordingly
APP_BASE_URL=https://yourdomain.com:8080
NEXT_PUBLIC_API_BASE_URL=https://yourdomain.com:8080
```

## Security Considerations

1. **Firewall Rules:**
   - Ensure ports 3500 and 8000 are accessible
   - Consider using a reverse proxy if available

2. **Environment Variables:**
   - Keep `.env.production` secure
   - Use strong passwords and API keys

3. **Database Security:**
   - Use strong database passwords
   - Restrict database access to your server IP

## Performance Optimization

### PM2 Configuration
```bash
# Increase backend workers for better performance
# Edit ecosystem.config.js:
args: 'app.main:app --host 0.0.0.0 --port 8000 --workers 4'
```

### Memory Limits
```bash
# Adjust memory limits in ecosystem.config.js:
max_memory_restart: '2G'  # Backend
max_memory_restart: '1G'  # Frontend
```

## Backup and Recovery

### Automatic Backups
- Database backups are created before each migration
- Code backups are created before each update

### Manual Backup
```bash
# Backup database
./deployment/user-space/migrate-user.sh --dry-run

# Backup application
tar -czf ~/dayplanner-backup-$(date +%Y%m%d).tar.gz ~/dayplanner
```

### Recovery
```bash
# Restore from backup
./deployment/user-space/update-user.sh --rollback

# Or manual restore
tar -xzf ~/dayplanner-backup-*.tar.gz -C ~/
```

## Support

For issues:
1. Check the troubleshooting section above
2. Review PM2 logs: `pm2 logs`
3. Check application logs: `tail -f ~/dayplanner/logs/*.log`
4. Verify environment configuration
5. Test database connectivity

## Limitations

- **No system-wide services** - Services run under your user account
- **Manual startup** - Services need to be started after server reboot
- **Port restrictions** - Must use ports > 1024
- **No nginx** - Direct access to application ports
- **User-level only** - Cannot install system packages

## Next Steps

After successful deployment:
1. Test all application functionality
2. Set up monitoring (PM2 provides basic monitoring)
3. Configure domain name and SSL (if available)
4. Set up automated backups
5. Document any customizations
