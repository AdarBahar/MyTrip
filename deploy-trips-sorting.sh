#!/bin/bash

# Wrapper script for trips sorting deployment
# This script loads configuration and calls the main deployment script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_SCRIPT="$SCRIPT_DIR/deployment/scripts/deploy-trips-sorting.sh"
CONFIG_FILE="$SCRIPT_DIR/deployment/scripts/deploy-config.local.env"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 MyTrip - Trips Sorting Feature Deployment${NC}"
echo "=================================================="

# Check if deployment script exists
if [[ ! -f "$DEPLOYMENT_SCRIPT" ]]; then
    echo -e "${RED}❌ Deployment script not found: $DEPLOYMENT_SCRIPT${NC}"
    exit 1
fi

# Load configuration if it exists
if [[ -f "$CONFIG_FILE" ]]; then
    echo -e "${GREEN}📋 Loading configuration from: $CONFIG_FILE${NC}"
    source "$CONFIG_FILE"
else
    echo -e "${YELLOW}⚠️  Configuration file not found: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}   Using default configuration or command line arguments${NC}"
fi

# Show current configuration
echo ""
echo "Configuration:"
echo "  Server: ${PROD_SERVER:-'not set'}"
echo "  User: ${PROD_USER:-'not set'}"
echo "  App Dir: ${PROD_APP_DIR:-'not set'}"
echo "  Service: ${PROD_SERVICE_NAME:-'not set'}"
echo ""

# Confirm deployment
if [[ "$1" != "--rollback" && "$1" != "--dry-run" ]]; then
    echo -e "${YELLOW}⚠️  This will deploy to production server: ${PROD_SERVER}${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
fi

# Export configuration for the deployment script
export PROD_SERVER
export PROD_USER
export PROD_APP_DIR
export PROD_VENV_DIR
export PROD_SERVICE_NAME

# Execute the deployment script with all arguments
echo -e "${GREEN}🔄 Executing deployment script...${NC}"
exec "$DEPLOYMENT_SCRIPT" "$@"
