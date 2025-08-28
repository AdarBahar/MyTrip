"use client";

import React, { useEffect, useRef } from 'react';
import * as maptilersdk from '@maptiler/sdk';
import '@maptiler/sdk/dist/maptiler-sdk.css';
import type { Place } from '@/lib/api/places';

interface MapPreviewProps {
  start?: Place | null;
  end?: Place | null;
  waypoints?: Place[]; // optional intermediate stops, drawn in order
  routeCoordinates?: [number, number][] | null; // use provided geometry when available (lon,lat)
  routes?: { id: string; coordinates: [number, number][], color?: string, width?: number, opacity?: number }[]; // multiple colored routes
  highlightRouteId?: string | null;
  height?: number; // px
  className?: string;
  interactive?: boolean; // allow pan/zoom
  extraMarkers?: { id: string; lat: number; lon: number; color?: string }[]; // search results markers
  overlayText?: string | null; // e.g., search query
}

export function MapPreview({ start, end, waypoints = [], routeCoordinates = null, routes, highlightRouteId = null, height = 240, className = '', interactive = true, extraMarkers = [], overlayText = null }: MapPreviewProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maptilersdk.Map | null>(null);
  const startMarkerRef = useRef<maptilersdk.Marker | null>(null);
  const endMarkerRef = useRef<maptilersdk.Marker | null>(null);
  const lineId = useRef<string>('preview-line');
  const routeLayerIdsRef = useRef<{layer: string, source: string}[]>([]);
  const extraMarkersRef = useRef<Map<string, maptilersdk.Marker>>(new Map());

  useEffect(() => {
    // Configure API key (Next inlines NEXT_PUBLIC_ envs at build time)
    const apiKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY as string | undefined;
    if (apiKey) maptilersdk.config.apiKey = apiKey;

    if (!mapContainer.current || mapRef.current) return;

    // Initialize the map (allow pan/zoom by default)
    mapRef.current = new maptilersdk.Map({
      container: mapContainer.current,
      style: maptilersdk.MapStyle.STREETS,
      center: [34.7818, 32.0853], // Tel Aviv fallback
      zoom: 10,
      interactive,
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Helper to add/update a marker
    const setMarker = (
      markerRef: React.MutableRefObject<maptilersdk.Marker | null>,
      place: Place | null | undefined,
      color: string
    ) => {
      if (!place) {
        if (markerRef.current) { markerRef.current.remove(); markerRef.current = null; }
        return;
      }
      const lngLat: [number, number] = [place.lon, place.lat];
      if (!markerRef.current) {
        markerRef.current = new maptilersdk.Marker({ color }).setLngLat(lngLat).addTo(map);
      } else {
        markerRef.current.setLngLat(lngLat);
      }
    };

    setMarker(startMarkerRef, start || null, '#16a34a'); // green
    setMarker(endMarkerRef, end || null, '#dc2626'); // red

    // Manage extra markers (e.g., search results)
    const existing = extraMarkersRef.current;
    const nextIds = new Set((extraMarkers || []).map(m => m.id));
    // Remove stale markers
    for (const [id, marker] of existing) {
      if (!nextIds.has(id)) { marker.remove(); existing.delete(id); }
    }
    // Add/update current markers
    for (const m of (extraMarkers || [])) {
      const key = m.id;
      const lngLat: [number, number] = [m.lon, m.lat];
      let mk = existing.get(key) || null;
      if (!mk) {
        mk = new maptilersdk.Marker({ color: m.color || '#f59e0b' }).setLngLat(lngLat).addTo(map);
        existing.set(key, mk);
      } else {
        mk.setLngLat(lngLat);
      }
    }

    const baseId = lineId.current;

    const removeAllRouteLayers = () => {
      // Remove any previously added route layers/sources
      for (const pair of routeLayerIdsRef.current) {
        if (map.getLayer(pair.layer)) map.removeLayer(pair.layer);
        if (map.getSource(pair.source)) map.removeSource(pair.source);
      }
      routeLayerIdsRef.current = [];
    };

    const applyLineAndFit = () => {
      removeAllRouteLayers();

      const allPoints: [number, number][] = [];

      // Multiple routes (colored)
      if (routes && routes.length) {
        routes.forEach((r, idx) => {
          if (!r.coordinates || !r.coordinates.length) return;
          const srcId = `${baseId}-src-${r.id || idx}`;
          const lyrId = `${baseId}-lyr-${r.id || idx}`;
          const geojson = { type: 'FeatureCollection', features: [
            { type: 'Feature', geometry: { type: 'LineString', coordinates: r.coordinates }, properties: {} },
          ] } as any;
          map.addSource(srcId, { type: 'geojson', data: geojson });
          map.addLayer({
            id: lyrId,
            type: 'line',
            source: srcId,
            paint: {
              'line-color': r.color || '#3b82f6',
              'line-width': typeof r.width === 'number' ? r.width : (r.id && r.id === highlightRouteId ? 5 : 3),
              'line-opacity': typeof r.opacity === 'number' ? r.opacity : 1,
            }
          });
          routeLayerIdsRef.current.push({ layer: lyrId, source: srcId });
          allPoints.push(...r.coordinates);
        });
      } else {
        // Single route or fallback straight line
        const coords: [number, number][] | null = routeCoordinates && routeCoordinates.length
          ? routeCoordinates
          : (start && (end || (waypoints && waypoints.length))
              ? [
                  [start.lon, start.lat],
                  ...(waypoints && waypoints.length ? waypoints.map(w => [w.lon, w.lat] as [number, number]) : []),
                  ...(end ? [[end.lon, end.lat] as [number, number]] : [])
                ]
              : null);

        if (coords) {
          const srcId = `${baseId}-src`;
          const lyrId = `${baseId}-lyr`;
          const geojson = { type: 'FeatureCollection', features: [
            { type: 'Feature', geometry: { type: 'LineString', coordinates: coords }, properties: {} },
          ] } as any;
          map.addSource(srcId, { type: 'geojson', data: geojson });
          map.addLayer({ id: lyrId, type: 'line', source: srcId, paint: { 'line-color': '#3b82f6', 'line-width': 3 } });
          routeLayerIdsRef.current.push({ layer: lyrId, source: srcId });
          allPoints.push(...coords);
        }
      }

      // Fit bounds
      if (allPoints.length > 0) {
        if (allPoints.length === 1) {
          map.easeTo({ center: allPoints[0], zoom: 12, duration: 300 });
        } else {
          const bounds = new maptilersdk.LngLatBounds();
          allPoints.forEach((p) => bounds.extend(p as any));
          map.fitBounds(bounds, { padding: 40, duration: 300 });
        }
      }
    };

    if (map.isStyleLoaded()) {
      applyLineAndFit();
    } else {
      const onLoad = () => applyLineAndFit();
      map.once('load', onLoad);
      return () => {
        map.off('load', onLoad);
      };
    }
  }, [start?.id, start?.lat, start?.lon, end?.id, end?.lat, end?.lon, waypoints?.length, routes?.length, routeCoordinates?.length, interactive, highlightRouteId, extraMarkers?.length]);

  return (
    <div className={className} style={{ position: 'relative', height }}>
      <div ref={mapContainer} style={{ position: 'absolute', inset: 0 }} />
      {overlayText && (
        <div className="absolute top-1 left-1 bg-white/80 text-gray-700 text-[10px] px-1.5 py-0.5 rounded shadow-sm pointer-events-none">
          {overlayText}
        </div>
      )}
    </div>
  );
}

