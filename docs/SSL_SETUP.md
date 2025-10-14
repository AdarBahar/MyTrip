# SSL Certificate Setup for MyTrips API

This document explains how to set up SSL certificates for the MyTrips API to enable HTTPS.

## Overview

The MyTrips API supports both HTTP and HTTPS configurations. SSL certificates are automatically detected and configured during deployment, or can be set up manually using the provided scripts.

## Automatic SSL Setup

### During Deployment

The main deployment script automatically detects existing SSL certificates and configures HTTPS:

```bash
# Run the main deployment script
sudo /opt/dayplanner/deployment/scripts/deploy-with-auth-fixes.sh
```

**What it does:**
- Checks for existing SSL certificates in `/etc/letsencrypt/live/`
- If certificates exist, configures nginx for HTTPS with CORS support
- If no certificates exist, provides instructions for manual setup

### Manual SSL Setup

Use the dedicated SSL setup script:

```bash
# Set up SSL certificates and HTTPS configuration
sudo /opt/dayplanner/deployment/scripts/enable-ssl.sh
```

**What it does:**
- Installs certbot if not already installed
- Creates SSL certificates using Let's Encrypt
- Configures nginx for HTTPS with HTTP redirect
- Sets up automatic certificate renewal
- Tests the HTTPS configuration

## SSL Certificate Locations

### Standard Location
```
/etc/letsencrypt/live/mytrips-api.bahar.co.il/
├── fullchain.pem
├── privkey.pem
├── cert.pem
└── chain.pem
```

### Alternative Location (if domain conflicts exist)
```
/etc/letsencrypt/live/mytrips-api.bahar.co.il-0001/
├── fullchain.pem
├── privkey.pem
├── cert.pem
└── chain.pem
```

The deployment scripts automatically detect which location is used.

## Nginx Configurations

### HTTP Only (Initial Setup)
- File: `deployment/nginx/mytrips-api.conf`
- Used when no SSL certificates exist
- Supports CORS for development

### HTTPS Enabled
- File: `deployment/nginx/mytrips-api-https.conf`
- Used when SSL certificates are available
- Includes HTTP to HTTPS redirect
- Enhanced security headers

## Manual Certificate Creation

### Using Certbot with Nginx

```bash
# Install certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Create certificate and auto-configure nginx
sudo certbot --nginx -d mytrips-api.bahar.co.il
```

### Using Certbot Standalone

```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Create certificate
sudo certbot certonly --standalone -d mytrips-api.bahar.co.il

# Start nginx
sudo systemctl start nginx

# Apply HTTPS configuration
sudo /opt/dayplanner/deployment/scripts/enable-ssl.sh
```

## Certificate Management

### Automatic Renewal

Certificates are automatically renewed via cron job:

```bash
# Check if auto-renewal is configured
sudo crontab -l | grep certbot

# Test renewal (dry run)
sudo certbot renew --dry-run

# Force renewal if needed
sudo certbot renew --force-renewal
```

### Manual Renewal

```bash
# Renew certificates
sudo certbot renew

# Reload nginx after renewal
sudo systemctl reload nginx
```

## Troubleshooting

### Certificate Not Found

```bash
# Check certificate status
sudo certbot certificates

# List certificate directories
sudo ls -la /etc/letsencrypt/live/

# Check nginx configuration
sudo nginx -t
```

### HTTPS Not Working

```bash
# Check nginx is listening on port 443
sudo netstat -tlnp | grep :443

# Check nginx error logs
sudo tail -f /var/log/nginx/mytrips-api_error.log

# Test SSL configuration
curl -v https://mytrips-api.bahar.co.il/health
```

### Certificate Expired

```bash
# Check certificate expiry
sudo certbot certificates

# Renew expired certificates
sudo certbot renew --force-renewal

# Restart nginx
sudo systemctl restart nginx
```

## Security Configuration

### HTTPS-Only Mode

The HTTPS configuration includes security headers:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### CORS Configuration

HTTPS configuration maintains CORS support for development:

- Allows `localhost` origins for development
- Handles preflight OPTIONS requests
- Prevents duplicate CORS headers

## Environment Configuration

### Production Environment

Update `.env.production` for HTTPS:

```bash
APP_BASE_URL=https://mytrips-api.bahar.co.il
NEXT_PUBLIC_API_BASE_URL=https://mytrips-api.bahar.co.il
CORS_ORIGINS=https://mytrips.bahar.co.il,http://localhost:3500
```

### Frontend Configuration

Update frontend to use HTTPS:

```bash
# In frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=https://mytrips-api.bahar.co.il
```

## Testing SSL Setup

### Basic HTTPS Test

```bash
# Test HTTPS endpoint
curl https://mytrips-api.bahar.co.il/health

# Test HTTP redirect
curl -v http://mytrips-api.bahar.co.il/health
```

### SSL Certificate Test

```bash
# Check SSL certificate details
openssl s_client -connect mytrips-api.bahar.co.il:443 -servername mytrips-api.bahar.co.il

# Test SSL rating
curl -s "https://api.ssllabs.com/api/v3/analyze?host=mytrips-api.bahar.co.il"
```

### CORS Test with HTTPS

```bash
# Test preflight request
curl -X OPTIONS "https://mytrips-api.bahar.co.il/health" \
  -H "Origin: http://localhost:3500" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Test actual request
curl "https://mytrips-api.bahar.co.il/health" \
  -H "Origin: http://localhost:3500" \
  -v
```

## Deployment Checklist

- [ ] SSL certificates created and valid
- [ ] Nginx configured for HTTPS
- [ ] HTTP redirects to HTTPS
- [ ] CORS headers working correctly
- [ ] Automatic renewal configured
- [ ] Security headers enabled
- [ ] Frontend updated to use HTTPS
- [ ] Environment variables updated

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `deploy-with-auth-fixes.sh` | Main deployment with SSL detection |
| `enable-ssl.sh` | SSL certificate setup and HTTPS configuration |
| `fix-cors.sh` | CORS configuration fix |

## Support

For SSL-related issues:

1. Check certificate status: `sudo certbot certificates`
2. Test nginx configuration: `sudo nginx -t`
3. Check nginx logs: `sudo tail -f /var/log/nginx/mytrips-api_error.log`
4. Verify DNS resolution: `nslookup mytrips-api.bahar.co.il`
5. Test from external SSL checker: https://www.ssllabs.com/ssltest/

---

**Last Updated**: October 14, 2025
**Next Review**: January 14, 2026
