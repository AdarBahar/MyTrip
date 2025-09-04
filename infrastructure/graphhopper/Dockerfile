# GraphHopper self-hosted image (builds from official released JAR)
# Default GraphHopper version can be overridden at build time via --build-arg GH_VERSION=10.2

FROM eclipse-temurin:17-jre AS runtime
ARG GH_VERSION=10.2

WORKDIR /app

# Install curl to fetch the release JAR at build time
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Download GraphHopper web service JAR
RUN curl -fsSL -o /app/graphhopper-web.jar \
    https://repo1.maven.org/maven2/com/graphhopper/graphhopper-web/${GH_VERSION}/graphhopper-web-${GH_VERSION}.jar

# Copy config; will be bind-mounted too so this is just a sane default
COPY config.yml /data/config.yml

# Expose GraphHopper HTTP port
EXPOSE 8989

# Entry point: expects the map file at /data/map.osm.pbf (bind mount your PBF as data/graphhopper/map.osm.pbf)
ENTRYPOINT [ \
  "java", \
  "-Ddw.graphhopper.datareader.file=/data/map.osm.pbf", \
  "-jar", \
  "/app/graphhopper-web.jar", \
  "server", \
  "/data/config.yml" \
]

