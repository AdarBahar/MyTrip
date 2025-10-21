#!/bin/bash

echo "🔧 Fixing Stop.deleted_at error in short format..."

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

echo "✅ Stop.deleted_at fix complete!"
