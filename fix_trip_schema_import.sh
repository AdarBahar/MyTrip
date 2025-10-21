#!/bin/bash

echo "🔧 Fixing TripSchema import error..."

# Upload corrected trip_complete.py
echo "📤 Uploading corrected trip_complete.py..."
scp -i ~/.ssh/hetzner-mytrips-api \
  backend/app/schemas/trip_complete.py \
  root@65.109.171.65:/opt/dayplanner/backend/app/schemas/

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

echo "✅ TripSchema import fix complete!"
