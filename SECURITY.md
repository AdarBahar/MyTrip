# Security Policy

## Overview

This document outlines the security practices and policies for the MyTrips project. We take security seriously and have implemented measures to protect sensitive information and prevent security vulnerabilities.

## Security Incident Response

**⚠️ SECURITY INCIDENT RESOLVED ⚠️**

**Date**: October 14, 2025  
**Status**: RESOLVED  
**Severity**: HIGH  

### Incident Summary

Multiple sensitive credentials were accidentally committed to the repository:

1. **Database Password**: MySQL production credentials
2. **FTP Credentials**: FTP server access credentials  
3. **GitHub Personal Access Token**: API access token
4. **High Entropy Secrets**: Various configuration secrets

### Actions Taken

✅ **Immediate Response**:
- All sensitive files removed from repository
- Git history cleaned (see below)
- Credentials invalidated/rotated
- Enhanced .gitignore patterns added
- Security documentation created

✅ **Files Removed**:
- `apply_auth_with_password.sh` (contained MySQL credentials)
- `deployment/production/ftp_credentials.json` (contained FTP credentials)
- `scripts/cleanup_production_database.py` (contained database credentials)
- `scripts/run_production_cleanup.sh` (contained database credentials)
- `SECURITY_INCIDENT_RESPONSE.md` (contained exposed credentials)
- `todo.txt` (GitHub token redacted)

✅ **Security Measures Implemented**:
- Comprehensive .gitignore patterns for sensitive files
- Pre-commit hooks for credential detection
- Security documentation and policies
- Environment variable templates without real credentials

## Security Best Practices

### 1. Credential Management

**DO:**
- Use environment variables for all sensitive configuration
- Store credentials in secure credential management systems
- Use `.env.example` files with placeholder values
- Rotate credentials regularly

**DON'T:**
- Commit credentials to version control
- Share credentials in plain text
- Use default or weak passwords
- Store credentials in configuration files

### 2. Environment Variables

All sensitive configuration should be stored in environment variables:

```bash
# Database Configuration
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-secure-password

# API Keys
GRAPHHOPPER_API_KEY=your-api-key
MAPTILER_API_KEY=your-api-key

# Application Secrets
APP_SECRET=your-super-secure-secret-key-min-32-chars
```

### 3. File Patterns to Never Commit

The following patterns are blocked by .gitignore:

- `*credentials*`
- `*secrets*`
- `*password*`
- `*.key`, `*.pem`, `*.p12`, `*.pfx`
- `ftp_credentials.json`
- `database_credentials.json`
- `api_keys.json`
- `*_with_password.sh`
- `*_with_credentials.sh`
- `ghp_*` (GitHub tokens)
- `.env.production`
- `deployment/production/credentials/`

### 4. Pre-Commit Security Checks

Install pre-commit hooks to prevent credential commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### 5. Production Deployment Security

**Environment Setup:**
1. Create `.env.production` on the server (never commit)
2. Set proper file permissions: `chmod 600 .env.production`
3. Use secure credential storage (AWS Secrets Manager, etc.)
4. Enable SSL/TLS for all communications
5. Use strong, unique passwords for all services

**Database Security:**
- Use dedicated database users with minimal privileges
- Enable SSL connections to database
- Regular security updates and patches
- Monitor for suspicious activity

**API Security:**
- JWT tokens with proper expiration
- Rate limiting on API endpoints
- Input validation and sanitization
- CORS configuration for production domains only

## Git History Cleaning

**⚠️ IMPORTANT**: The git history has been cleaned to remove sensitive data.

### What Was Done

1. **Identified Sensitive Commits**: Found commits containing credentials
2. **Removed Sensitive Files**: Deleted files with embedded credentials
3. **Updated .gitignore**: Added comprehensive security patterns
4. **Force Push**: Updated main branch with clean history

### For Collaborators

If you have local clones of this repository:

```bash
# Backup your local changes
git stash

# Fetch the cleaned history
git fetch origin
git reset --hard origin/main

# Restore your changes
git stash pop
```

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Email security concerns to: [REDACTED - Use secure communication]
3. Include detailed information about the vulnerability
4. Allow reasonable time for response before public disclosure

## Security Checklist for Developers

Before committing code:

- [ ] No hardcoded credentials or API keys
- [ ] No sensitive configuration in code
- [ ] Environment variables used for all secrets
- [ ] .env files not committed
- [ ] Pre-commit hooks passing
- [ ] Security review completed

Before deploying:

- [ ] Production environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database credentials rotated
- [ ] API keys validated
- [ ] Security headers configured
- [ ] Rate limiting enabled

## Credential Rotation Schedule

- **Database passwords**: Every 90 days
- **API keys**: Every 180 days  
- **JWT secrets**: Every 365 days
- **SSL certificates**: Before expiration
- **GitHub tokens**: Every 365 days or when compromised

## Security Tools and Monitoring

### Recommended Tools

- **git-secrets**: Prevent committing secrets
- **truffleHog**: Scan for secrets in git history
- **pre-commit**: Automated security checks
- **SAST tools**: Static application security testing

### Monitoring

- Monitor for unusual database access patterns
- Log and alert on failed authentication attempts
- Track API usage and rate limiting
- Monitor SSL certificate expiration

## Compliance and Standards

This project follows:

- OWASP Top 10 security practices
- Industry standard credential management
- Secure coding practices
- Regular security assessments

## Contact

For security-related questions or concerns:
- Review this security policy
- Check existing security documentation
- Use secure communication channels for sensitive topics

---

**Last Updated**: October 14, 2025  
**Next Review**: January 14, 2026
