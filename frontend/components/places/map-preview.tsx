"use client";

import React, { useEffect, useMemo, useRef } from 'react';
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
  extraMarkers?: { id: string; lat: number; lon: number; color?: string; label?: string }[]; // search results markers
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
  const lastMarkersSigRef = useRef<string>('');

  useEffect(() => {
    // Configure API key (Next inlines NEXT_PUBLIC_ envs at build time)
    const apiKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY as string | undefined;
    if (apiKey) maptilersdk.config.apiKey = apiKey;

    const el = mapContainer.current;
    if (!el || mapRef.current) return;

    const initMap = () => {
      if (mapRef.current || !mapContainer.current) return;
      mapRef.current = new maptilersdk.Map({
        container: mapContainer.current,
        style: maptilersdk.MapStyle.STREETS,
        center: [34.7818, 32.0853], // Tel Aviv fallback
        zoom: 10,
        interactive,
      });
    };

    // Wait for container to have layout size to avoid maplibre internal errors
    if (el.offsetWidth === 0 || el.offsetHeight === 0) {
      const ro = new ResizeObserver(() => {
        if (!mapContainer.current) return;
        if (mapContainer.current.offsetWidth > 0 && mapContainer.current.offsetHeight > 0) {
          try { ro.disconnect(); } catch {}
          initMap();
        }
      });
      ro.observe(el);
      return () => {
        try { ro.disconnect(); } catch {}
        if (mapRef.current) {
          mapRef.current.remove();
          mapRef.current = null;
        }
      };
    } else {
      initMap();
      return () => {
        if (mapRef.current) {
          mapRef.current.remove();
          mapRef.current = null;
        }
      };
    }
  }, []);

  const extraMarkersSig = useMemo(() => JSON.stringify((extraMarkers || []).map(m => ({ id: m.id, lat: +m.lat.toFixed(5), lon: +m.lon.toFixed(5), color: m.color || '' }))), [extraMarkers])

  useEffect(() => {
    const map = mapRef.current as any;
    if (!map || map._removed) return;

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
        if (m.label) {
          const popup = new maptilersdk.Popup({ offset: 12 }).setText(m.label);
          mk.setPopup(popup);
        }
        existing.set(key, mk);
      } else {
        mk.setLngLat(lngLat);
        if (m.label) {
          const popup = mk.getPopup() || new maptilersdk.Popup({ offset: 12 });
          popup.setText(m.label);
          mk.setPopup(popup);
        }
      }
    }
    // Track signature to force rerender when markers move/change
    lastMarkersSigRef.current = extraMarkersSig

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
      if (!map || (map as any)._removed) return;
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
          if (!map.getSource(srcId)) map.addSource(srcId, { type: 'geojson', data: geojson });
          if (!map.getLayer(lyrId)) map.addLayer({
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

      // Also include simple markers for start/end/waypoints with labels
      const labelFor = (p?: Place | null) => {
        if (!p) return ''
        const parts = [p.name, p.address].filter(Boolean)
        return parts.join(' — ')
      }
      const basicMarkers: { id: string; lat: number; lon: number; color?: string; label?: string }[] = []
      if (start) basicMarkers.push({ id: `start-${start.id}`, lat: start.lat, lon: start.lon, color: '#16a34a', label: labelFor(start) })
      for (const w of waypoints || []) basicMarkers.push({ id: `wp-${w.id}`, lat: w.lat, lon: w.lon, color: '#f59e0b', label: labelFor(w) })
      if (end) basicMarkers.push({ id: `end-${end.id}`, lat: end.lat, lon: end.lon, color: '#dc2626', label: labelFor(end) })
      const merged = [...(extraMarkers || []), ...basicMarkers]
      // Re-run markers pass with merged list
      const existing2 = extraMarkersRef.current
      const nextIds2 = new Set(merged.map(m => m.id))
      for (const [id, marker] of existing2) { if (!nextIds2.has(id)) { marker.remove(); existing2.delete(id) } }
      for (const m of merged) {
        const key = m.id
        const lngLat: [number, number] = [m.lon, m.lat]
        let mk = existing2.get(key) || null
        if (!mk) {
          mk = new maptilersdk.Marker({ color: m.color || '#2563eb' }).setLngLat(lngLat).addTo(map)
          if (m.label) mk.setPopup(new maptilersdk.Popup({ offset: 12 }).setText(m.label))
          existing2.set(key, mk)
        } else {
          mk.setLngLat(lngLat)
          if (m.label) {
            const popup = mk.getPopup() || new maptilersdk.Popup({ offset: 12 })
            popup.setText(m.label)
            mk.setPopup(popup)
          }
        }
      }

          const srcId = `${baseId}-src`;
          const lyrId = `${baseId}-lyr`;
          const geojson = { type: 'FeatureCollection', features: [
            { type: 'Feature', geometry: { type: 'LineString', coordinates: coords }, properties: {} },
          ] } as any;
          if (!map.getSource(srcId)) map.addSource(srcId, { type: 'geojson', data: geojson });
          if (!map.getLayer(lyrId)) map.addLayer({ id: lyrId, type: 'line', source: srcId, paint: { 'line-color': '#3b82f6', 'line-width': 3 } });
          routeLayerIdsRef.current.push({ layer: lyrId, source: srcId });
          allPoints.push(...coords);
        }
      }

      // Fit bounds
      if (allPoints.length > 0) {
        try {
          if (allPoints.length === 1) {
            map.easeTo({ center: allPoints[0], zoom: 12, duration: 300 });
          } else {
            const bounds = new maptilersdk.LngLatBounds();
            allPoints.forEach((p) => bounds.extend(p as any));
            map.fitBounds(bounds, { padding: 40, duration: 300 });
          }
        } catch {}
      }
    };

    if (map.isStyleLoaded()) {
      applyLineAndFit();
    } else {
      const onLoad = () => applyLineAndFit();
      map.once('load', onLoad);
      return () => {
        try { map.off('load', onLoad); } catch {}
      };
    }
  }, [start?.id, start?.lat, start?.lon, end?.id, end?.lat, end?.lon, waypoints?.length, routes?.length, routeCoordinates?.length, interactive, highlightRouteId, extraMarkersSig]);

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

