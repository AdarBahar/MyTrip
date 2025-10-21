#!/bin/bash

# Fix import error on production server
# This script uploads the corrected router files and restarts the service

echo "🔧 Fixing import error on production server..."

# Upload corrected days router
echo "📤 Uploading corrected days router..."
scp -i ~/.ssh/hetzner-mytrips-api \
  backend/app/api/days/router.py \
  root@65.109.171.65:/opt/dayplanner/backend/app/api/days/

# Upload corrected trips router
echo "📤 Uploading corrected trips router..."
scp -i ~/.ssh/hetzner-mytrips-api \
  backend/app/api/trips/router.py \
  root@65.109.171.65:/opt/dayplanner/backend/app/api/trips/

# Restart the service
echo "🔄 Restarting dayplanner-backend service..."
ssh -i ~/.ssh/hetzner-mytrips-api root@65.109.171.65 \
  "systemctl restart dayplanner-backend"

# Check service status
echo "📊 Checking service status..."
ssh -i ~/.ssh/hetzner-mytrips-api root@65.109.171.65 \
  "systemctl status dayplanner-backend --no-pager"

# Test the API
echo "🧪 Testing API health..."
ssh -i ~/.ssh/hetzner-mytrips-api root@65.109.171.65 \
  "curl -s http://localhost:8000/health || echo 'Health check failed'"

echo "✅ Import error fix complete!"
