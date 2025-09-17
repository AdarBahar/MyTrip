# DayPlanner Production Deployment Guide

This guide covers deploying the DayPlanner application to production without Docker.

## Prerequisites

- Ubuntu/Debian server (18.04+ recommended)
- Root access or sudo privileges
- MySQL database (external)
- Domain name (optional, can use IP address)

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AdarBahar/MyTrip.git /opt/dayplanner
   cd /opt/dayplanner
   ```

2. **Configure environment:**
   ```bash
   cp deployment/production.env .env.production
   # Edit .env.production with your settings
   nano .env.production
   ```

3. **Run deployment script:**
   ```bash
   sudo chmod +x deployment/scripts/*.sh
   sudo deployment/scripts/deploy.sh
   ```

## Manual Deployment Steps

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx curl git build-essential libpq-dev mysql-client

# Install pnpm
sudo npm install -g pnpm

# Create application directory
sudo mkdir -p /opt/dayplanner
sudo chown -R www-data:www-data /opt/dayplanner
```

### 2. Application Setup

```bash
# Clone repository
sudo git clone https://github.com/AdarBahar/MyTrip.git /opt/dayplanner
cd /opt/dayplanner

# Set ownership
sudo chown -R www-data:www-data /opt/dayplanner

# Configure environment
sudo cp deployment/production.env .env.production
sudo nano .env.production  # Edit with your settings
```

### 3. Backend Setup

```bash
cd /opt/dayplanner/backend

# Create virtual environment
sudo -u www-data python3 -m venv venv

# Install dependencies
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd /opt/dayplanner/frontend

# Install dependencies
sudo -u www-data pnpm install

# Build for production
sudo -u www-data pnpm build
```

### 5. Database Setup

```bash
# Run migrations
cd /opt/dayplanner/backend
source venv/bin/activate
export $(cat /opt/dayplanner/.env.production | grep -v '^#' | xargs)
alembic upgrade head
```

### 6. Service Configuration

```bash
# Copy systemd service files
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable dayplanner-backend.service
sudo systemctl enable dayplanner-frontend.service
```

### 7. Nginx Configuration

```bash
# Copy nginx configuration
sudo cp deployment/nginx/dayplanner.conf /etc/nginx/sites-available/

# Enable site
sudo ln -sf /etc/nginx/sites-available/dayplanner.conf /etc/nginx/sites-enabled/

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Start Services

```bash
# Start backend
sudo systemctl start dayplanner-backend.service

# Start frontend
sudo systemctl start dayplanner-frontend.service

# Check status
sudo systemctl status dayplanner-backend.service
sudo systemctl status dayplanner-frontend.service
```

## Configuration

### Environment Variables

Edit `/opt/dayplanner/.env.production`:

```bash
# Database Configuration
DB_HOST=your-mysql-host
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password

# Application Configuration
APP_ENV=production
APP_SECRET=your-super-secure-secret-key-min-32-chars
APP_BASE_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# API Keys
GRAPHHOPPER_API_KEY=your-graphhopper-api-key
MAPTILER_API_KEY=your-maptiler-api-key

# Frontend Configuration
NEXT_PUBLIC_API_BASE_URL=https://yourdomain.com/api
NEXT_PUBLIC_MAPTILER_API_KEY=your-maptiler-api-key
```

### Nginx Configuration

Update `/etc/nginx/sites-available/dayplanner.conf`:

- Replace `yourdomain.com` with your actual domain
- Configure SSL certificates if using HTTPS
- Adjust rate limiting as needed

## Management Commands

### Service Management

```bash
# Check service status
sudo systemctl status dayplanner-backend.service
sudo systemctl status dayplanner-frontend.service

# Restart services
sudo systemctl restart dayplanner-backend.service
sudo systemctl restart dayplanner-frontend.service

# View logs
sudo journalctl -u dayplanner-backend.service -f
sudo journalctl -u dayplanner-frontend.service -f
```

### Database Operations

```bash
# Run migrations
sudo /opt/dayplanner/deployment/scripts/migrate.sh

# Check migration status
sudo /opt/dayplanner/deployment/scripts/migrate.sh --status

# Dry run migrations
sudo /opt/dayplanner/deployment/scripts/migrate.sh --dry-run
```

### Application Updates

```bash
# Update from Git repository
sudo /opt/dayplanner/deployment/scripts/update.sh

# Rollback to previous version
sudo /opt/dayplanner/deployment/scripts/update.sh --rollback
```

## Monitoring and Logs

### Log Locations

- **Application Logs:** `/var/log/dayplanner/`
- **Nginx Logs:** `/var/log/nginx/dayplanner_*.log`
- **System Logs:** `journalctl -u dayplanner-*`

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3500

# Full application health
curl http://localhost/health
```

## Security Considerations

1. **Firewall Configuration:**
   ```bash
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **SSL/TLS Setup:**
   - Use Let's Encrypt for free SSL certificates
   - Configure HTTPS redirects in Nginx
   - Update CORS origins for HTTPS

3. **Database Security:**
   - Use strong passwords
   - Restrict database access to application server
   - Regular backups

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u dayplanner-backend.service -n 50
   sudo journalctl -u dayplanner-frontend.service -n 50
   ```

2. **Database connection issues:**
   ```bash
   cd /opt/dayplanner/backend
   source venv/bin/activate
   python prestart.py
   ```

3. **Frontend build issues:**
   ```bash
   cd /opt/dayplanner/frontend
   sudo -u www-data pnpm install
   sudo -u www-data pnpm build
   ```

4. **Permission issues:**
   ```bash
   sudo chown -R www-data:www-data /opt/dayplanner
   sudo chmod +x /opt/dayplanner/deployment/scripts/*.sh
   ```

### Performance Tuning

1. **Backend Workers:**
   - Adjust `--workers` in systemd service file
   - Monitor CPU and memory usage

2. **Nginx Optimization:**
   - Enable gzip compression
   - Configure caching headers
   - Adjust worker processes

3. **Database Optimization:**
   - Monitor query performance
   - Add indexes as needed
   - Regular maintenance

## Backup and Recovery

### Automated Backups

The migration script automatically creates database backups before applying changes.

### Manual Backup

```bash
# Database backup
mysqldump -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME > backup.sql

# Application backup
tar -czf dayplanner-backup-$(date +%Y%m%d).tar.gz /opt/dayplanner
```

### Recovery

```bash
# Restore database
mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME < backup.sql

# Restore application
sudo systemctl stop dayplanner-*
sudo tar -xzf dayplanner-backup-*.tar.gz -C /
sudo systemctl start dayplanner-*
```

## Support

For issues and questions:
- Check the troubleshooting section above
- Review application logs
- Check GitHub issues: https://github.com/AdarBahar/MyTrip/issues
