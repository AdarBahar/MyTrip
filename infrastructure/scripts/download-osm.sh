#!/bin/bash

# Download OSM data for GraphHopper self-hosted routing
# Usage: ./download-osm.sh [region]
# Available regions: california, israel, europe, north-america

set -e

REGION=${1:-california}
DATA_DIR="./data/graphhopper"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

echo "Downloading OSM data for region: $REGION"

case $REGION in
  "california")
    URL="https://download.geofabrik.de/north-america/us/california-latest.osm.pbf"
    FILENAME="california-latest.osm.pbf"
    ;;
  "israel")
    URL="https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf"
    FILENAME="israel-and-palestine-latest.osm.pbf"
    ;;
  "europe")
    URL="https://download.geofabrik.de/europe-latest.osm.pbf"
    FILENAME="europe-latest.osm.pbf"
    ;;
  "north-america")
    URL="https://download.geofabrik.de/north-america-latest.osm.pbf"
    FILENAME="north-america-latest.osm.pbf"
    ;;
  *)
    echo "Unknown region: $REGION"
    echo "Available regions: california, israel, europe, north-america"
    exit 1
    ;;
esac

# Download the file
echo "Downloading from: $URL"
curl -L -o "$DATA_DIR/$FILENAME" "$URL"

# Create symlink to map.osm.pbf (expected by GraphHopper)
ln -sf "$FILENAME" "$DATA_DIR/map.osm.pbf"

echo "Download complete: $DATA_DIR/$FILENAME"
echo "Symlink created: $DATA_DIR/map.osm.pbf -> $FILENAME"
echo ""
echo "To use with GraphHopper self-hosted:"
echo "1. Set GRAPHHOPPER_MODE=selfhost in your .env file"
echo "2. Run: docker-compose --profile selfhost up"
echo ""
echo "Note: First startup will take time to build the routing graph."