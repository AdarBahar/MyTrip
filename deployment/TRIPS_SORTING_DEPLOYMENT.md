# Trips Sorting Feature - Production Deployment Guide

## Overview

This guide covers the deployment of the trips sorting feature to production with rollback capabilities.

## Files Included

### Core Changes
- `backend/app/api/trips/router.py` - Updated with sorting functionality
- `docs/TRIPS_SORTING_FEATURE.md` - Feature documentation

### Deployment Scripts
- `deployment/scripts/deploy-trips-sorting.sh` - Main deployment script with rollback
- `deployment/scripts/production-test.py` - Comprehensive test suite
- `deployment/scripts/deploy-config.env` - Configuration template

### Test Scripts
- `test_trips_sorting.py` - Local/production testing script

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] SSH key authentication configured for production server
- [ ] Production server details configured in `deploy-config.local.env`
- [ ] Test user credentials available for production testing
- [ ] Backup strategy confirmed

### 2. Code Review
- [ ] Changes reviewed and tested locally
- [ ] No syntax errors in modified files
- [ ] All tests pass locally
- [ ] Documentation updated

### 3. Production Readiness
- [ ] Production server accessible via SSH
- [ ] Backend service running and healthy
- [ ] Database accessible
- [ ] Sufficient disk space for backups

## Deployment Process

### Step 1: Configuration

Copy and customize the configuration file:

```bash
cd deployment/scripts
cp deploy-config.env deploy-config.local.env
# Edit deploy-config.local.env with your production details
```

### Step 2: Dry Run

Test the deployment process without making changes:

```bash
./deploy-trips-sorting.sh --dry-run --server your-server.com --user deploy
```

### Step 3: Deploy

Execute the deployment:

```bash
./deploy-trips-sorting.sh --server your-server.com --user deploy --verbose
```

### Step 4: Verify

The script automatically runs tests, but you can also run them manually:

```bash
# On production server
python3 test_trips_sorting.py --api-base http://localhost:8000
```

## Rollback Process

If issues are detected, rollback immediately:

```bash
./deploy-trips-sorting.sh --rollback --server your-server.com --user deploy
```

## Deployment Script Features

### Automatic Backup
- Creates timestamped backup before deployment
- Backs up modified files and service status
- Stores backup manifest for tracking

### Health Checks
- Verifies SSH connectivity
- Checks service status before and after deployment
- Runs comprehensive test suite

### Rollback Capability
- Automatic rollback on test failure
- Manual rollback command available
- Restores from most recent backup

### Safety Features
- Dry run mode for testing
- Verbose logging
- Error handling and cleanup
- Service status verification

## Testing

### Automated Tests
The deployment includes comprehensive tests:

1. **Health Check** - Basic server connectivity
2. **Authentication** - Login functionality
3. **Basic Endpoint** - Trips endpoint accessibility
4. **Default Sorting** - Newest first behavior
5. **Explicit Sorting** - All sorting parameters
6. **Invalid Parameters** - Graceful error handling
7. **Pagination** - Sorting with pagination
8. **Performance** - Response time validation

### Manual Testing
After deployment, verify:

```bash
# Test newest first (default)
curl -H "Authorization: Bearer $TOKEN" "https://your-api.com/trips"

# Test 10 most recent
curl -H "Authorization: Bearer $TOKEN" "https://your-api.com/trips?size=10&sort_by=created_at:desc"

# Test alphabetical
curl -H "Authorization: Bearer $TOKEN" "https://your-api.com/trips?sort_by=title:asc"
```

## Monitoring

### Post-Deployment Monitoring
- [ ] Check application logs for errors
- [ ] Monitor API response times
- [ ] Verify database performance
- [ ] Check user feedback

### Key Metrics
- API response time for `/trips` endpoint
- Database query performance
- Error rates
- User adoption of sorting features

## Troubleshooting

### Common Issues

#### Deployment Fails
1. Check SSH connectivity
2. Verify file permissions
3. Check disk space
4. Review service logs

#### Tests Fail
1. Check service status: `systemctl status mytrips-backend`
2. Review application logs: `journalctl -u mytrips-backend -f`
3. Test database connectivity
4. Verify environment variables

#### Performance Issues
1. Check database indexes
2. Monitor query execution time
3. Review server resources
4. Consider caching strategies

### Rollback Scenarios

#### When to Rollback
- Test suite fails
- API response time > 5 seconds
- Error rate increases significantly
- User reports of broken functionality

#### Rollback Process
1. Execute rollback script
2. Verify service restoration
3. Run health checks
4. Notify stakeholders
5. Investigate root cause

## Success Criteria

### Deployment Success
- [ ] All automated tests pass
- [ ] Service starts successfully
- [ ] API responds within acceptable time
- [ ] No increase in error rates

### Feature Success
- [ ] Default sorting works (newest first)
- [ ] All sorting parameters functional
- [ ] Pagination preserves sorting
- [ ] Invalid parameters handled gracefully
- [ ] Documentation accessible

## Post-Deployment Tasks

### Immediate (0-2 hours)
- [ ] Monitor application logs
- [ ] Check key metrics
- [ ] Verify user functionality
- [ ] Update deployment log

### Short-term (2-24 hours)
- [ ] Monitor performance trends
- [ ] Collect user feedback
- [ ] Review error logs
- [ ] Update monitoring dashboards

### Long-term (1-7 days)
- [ ] Analyze usage patterns
- [ ] Performance optimization
- [ ] User adoption metrics
- [ ] Plan next improvements

## Contact Information

### Deployment Team
- **Primary**: [Your Name] - [email]
- **Backup**: [Backup Contact] - [email]

### Escalation
- **Technical Issues**: [Tech Lead] - [email]
- **Business Issues**: [Product Owner] - [email]
- **Emergency**: [On-call rotation] - [phone]

## Appendix

### Configuration Files
- Production environment variables
- Service configuration
- Database connection settings
- Monitoring configuration

### Useful Commands
```bash
# Check service status
systemctl status mytrips-backend

# View logs
journalctl -u mytrips-backend -f

# Test API health
curl http://localhost:8000/health

# Check disk space
df -h

# View recent backups
ls -la /tmp/mytrips-backup-*
```
