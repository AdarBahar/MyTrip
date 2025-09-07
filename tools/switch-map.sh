#!/bin/bash

# GraphHopper Map Switcher
# Usage: ./switch-map.sh [israel|gcc|us]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data/graphhopper"

echo "GraphHopper Map Switcher"
echo "========================"

if [ $# -eq 0 ]; then
    echo "Usage: $0 [israel|gcc|us]"
    echo ""
    echo "Available maps:"
    echo "  israel  - Israel and Palestine (112 MB)"
    echo "  gcc     - GCC States / Middle East (229 MB)"
    echo "  us      - United States (10.6 GB)"
    echo ""
    echo "Current map:"
    if [ -f "$DATA_DIR/map.osm.pbf" ]; then
        SIZE=$(ls -lah "$DATA_DIR/map.osm.pbf" | awk '{print $5}')
        echo "  Size: $SIZE"
    else
        echo "  No map currently active"
    fi
    exit 1
fi

MAP_TYPE="$1"

# Stop GraphHopper container
echo "Stopping GraphHopper container..."
docker stop roadtrip-graphhopper 2>/dev/null || true

# Switch map based on type
case "$MAP_TYPE" in
    "israel")
        if [ ! -f "$DATA_DIR/map-israel-backup.osm.pbf" ]; then
            echo "Error: Israel map not found at $DATA_DIR/map-israel-backup.osm.pbf"
            exit 1
        fi
        echo "Switching to Israel map..."
        cp "$DATA_DIR/map-israel-backup.osm.pbf" "$DATA_DIR/map.osm.pbf"
        ;;
    "gcc")
        if [ ! -f "$DATA_DIR/gcc-states-latest.osm.pbf" ]; then
            echo "Error: GCC States map not found at $DATA_DIR/gcc-states-latest.osm.pbf"
            exit 1
        fi
        echo "Switching to GCC States map..."
        cp "$DATA_DIR/gcc-states-latest.osm.pbf" "$DATA_DIR/map.osm.pbf"
        ;;
    "us")
        if [ ! -f "$DATA_DIR/us-latest.osm.pbf" ]; then
            echo "Error: US map not found at $DATA_DIR/us-latest.osm.pbf"
            exit 1
        fi
        echo "Switching to US map..."
        cp "$DATA_DIR/us-latest.osm.pbf" "$DATA_DIR/map.osm.pbf"
        ;;
    *)
        echo "Error: Unknown map type '$MAP_TYPE'"
        echo "Available options: israel, gcc, us"
        exit 1
        ;;
esac

# Clear GraphHopper cache
echo "Clearing GraphHopper cache..."
rm -rf "$DATA_DIR/graph-cache"/*

# Start GraphHopper container
echo "Starting GraphHopper container..."
cd "$PROJECT_ROOT"
docker-compose --profile selfhost up -d graphhopper

echo ""
echo "Map switch complete!"
echo "GraphHopper is now processing the new map data."
echo "This may take 5-30 minutes depending on map size."
echo ""
echo "Monitor progress with:"
echo "  docker logs roadtrip-graphhopper -f"
echo ""
echo "Check when ready with:"
echo "  curl http://localhost:8989/health"
