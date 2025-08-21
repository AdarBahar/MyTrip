#!/bin/bash

# RoadTrip Planner Setup Script
# This script sets up the development environment for the RoadTrip Planner

set -e

echo "🚗 RoadTrip Planner Setup"
echo "========================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and configure:"
    echo "   - Database connection (DB_HOST, DB_USER, DB_PASSWORD, etc.)"
    echo "   - GRAPHHOPPER_API_KEY (for cloud routing)"
    echo "   - MAPTILER_API_KEY (for maps)"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Check for required tools
echo "🔍 Checking required tools..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    echo "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed"
    echo "   Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Check if we want to use self-hosted GraphHopper
echo ""
read -p "🗺️  Do you want to set up self-hosted GraphHopper? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Setting up self-hosted GraphHopper..."

    # Download OSM data
    echo "🌍 Available regions for OSM data:"
    echo "   1) California (recommended for demo)"
    echo "   2) Israel"
    echo "   3) Europe (large download)"
    echo "   4) North America (very large download)"
    echo ""
    read -p "Select region (1-4): " -n 1 -r
    echo

    case $REPLY in
        1) REGION="california" ;;
        2) REGION="israel" ;;
        3) REGION="europe" ;;
        4) REGION="north-america" ;;
        *) REGION="california" ;;
    esac

    echo "📥 Downloading OSM data for $REGION..."
    ./infrastructure/scripts/download-osm.sh $REGION

    # Update .env for self-hosted mode
    if grep -q "GRAPHHOPPER_MODE=cloud" .env; then
        sed -i.bak 's/GRAPHHOPPER_MODE=cloud/GRAPHHOPPER_MODE=selfhost/' .env
        echo "✅ Updated .env to use self-hosted GraphHopper"
    fi
else
    echo "☁️  Using GraphHopper Cloud API"
    echo "   Make sure to set GRAPHHOPPER_API_KEY in .env"
fi

# Check database connection
echo ""
echo "🗄️  Database Configuration"
echo "   Using external MySQL database"
echo "   Make sure your MySQL database is accessible and configured in .env"

# Install pre-commit hooks
echo ""
echo "🔧 Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  pre-commit not found. Install with: pip install pre-commit"
fi

# Build and start services
echo ""
echo "🐳 Building and starting services..."
make build
make up

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
make db.migrate

# Seed database
echo "🌱 Seeding database with demo data..."
make db.seed

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📚 Useful commands:"
echo "   make up      - Start all services"
echo "   make down    - Stop all services"
echo "   make logs    - View logs"
echo "   make test    - Run tests"
echo ""
echo "📖 Documentation: ./docs/README.md"
echo ""
echo "Happy road trip planning! 🚗💨"