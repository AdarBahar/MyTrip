'use client'

/**
 * Enhanced Trip Route Map Component
 * 
 * Interactive map showing trip routes with proper markers (S, 1, 2, E) and colors
 * for each leg on each day, similar to the route-breakdown page.
 */

import React, { useState, useEffect, useRef } from 'react'
import * as maptilersdk from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'

interface TripRoutePoint {
  lat: number
  lon: number
  name: string
}

interface TripRouteData {
  id: string
  coordinates: [number, number][]
  color?: string
  stops?: TripRoutePoint[]
}

interface TripRouteMapProps {
  routes: TripRouteData[]
  extraMarkers?: Array<{
    id: string
    lat: number
    lon: number
    color: string
    label: string
  }>
  highlightRouteId?: string | null
  height?: number
  className?: string
  interactive?: boolean
  visibleRoutes?: Record<string, boolean>
}

export default function TripRouteMap({
  routes,
  extraMarkers = [],
  highlightRouteId,
  height = 280,
  className = '',
  interactive = true,
  visibleRoutes = {}
}: TripRouteMapProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maptilersdk.Map | null>(null)
  const routeLayerIdsRef = useRef<{layer: string, source: string}[]>([])
  const markersRef = useRef<maptilersdk.Marker[]>([])

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current) return

    // Set MapTiler API key
    maptilersdk.config.apiKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY || ''

    const map = new maptilersdk.Map({
      container: mapContainer.current,
      style: maptilersdk.MapStyle.STREETS,
      center: [34.8516, 32.0853], // Default to Israel center
      zoom: 8
    })

    mapRef.current = map

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [])

  // Update routes and markers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const addRouteData = () => {
      // Clear existing route layers and markers
      routeLayerIdsRef.current.forEach(({ layer, source }) => {
        if (map.getLayer(layer)) map.removeLayer(layer)
        if (map.getSource(source)) map.removeSource(source)
      })
      routeLayerIdsRef.current = []

      markersRef.current.forEach(marker => marker.remove())
      markersRef.current = []

      // Filter visible routes
      const visibleRoutesData = routes.filter(route => 
        visibleRoutes[route.id] !== false && route.coordinates.length > 0
      )

      if (visibleRoutesData.length === 0) {
        return
      }

      // Add route lines
      visibleRoutesData.forEach((route, routeIndex) => {
        const sourceId = `route-source-${route.id}`
        const layerId = `route-layer-${route.id}`

        // Add route source
        map.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates: route.coordinates
            }
          }
        })

        // Add route layer
        map.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': route.color || '#3b82f6',
            'line-width': highlightRouteId === route.id ? 6 : 4,
            'line-opacity': highlightRouteId === route.id ? 1 : 0.8
          }
        })

        routeLayerIdsRef.current.push({ layer: layerId, source: sourceId })
      })

      // Create markers for route points
      const allMarkers: Array<{
        lat: number
        lon: number
        name: string
        type: 'start' | 'stop' | 'end'
        label: string
        color: string
        routeId: string
      }> = []

      visibleRoutesData.forEach((route, routeIndex) => {
        if (!route.stops || route.stops.length === 0) return

        // Add markers for each stop in the route
        route.stops.forEach((stop, stopIndex) => {
          let type: 'start' | 'stop' | 'end'
          let label: string
          let color: string

          if (stopIndex === 0) {
            type = 'start'
            label = 'S'
            color = '#10b981' // Green for start
          } else if (stopIndex === route.stops!.length - 1) {
            type = 'end'
            label = 'E'
            color = '#ef4444' // Red for end
          } else {
            type = 'stop'
            label = (stopIndex).toString()
            color = '#3b82f6' // Blue for intermediate stops
          }

          allMarkers.push({
            lat: stop.lat,
            lon: stop.lon,
            name: stop.name,
            type,
            label,
            color,
            routeId: route.id
          })
        })
      })

      // Add extra markers (if any)
      extraMarkers.forEach(marker => {
        allMarkers.push({
          lat: marker.lat,
          lon: marker.lon,
          name: marker.label,
          type: 'stop',
          label: marker.label,
          color: marker.color,
          routeId: 'extra'
        })
      })

      // Create map markers
      allMarkers.forEach((markerData) => {
        // Create marker element
        const el = document.createElement('div')
        el.className = 'custom-trip-marker'
        el.style.cssText = `
          background-color: ${markerData.color};
          width: 30px;
          height: 30px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 12px;
          font-family: system-ui, -apple-system, sans-serif;
          cursor: pointer;
          z-index: 10;
        `
        el.textContent = markerData.label

        // Create marker with popup
        const marker = new maptilersdk.Marker({ element: el })
          .setLngLat([markerData.lon, markerData.lat])
          .setPopup(
            new maptilersdk.Popup({ offset: 25 })
              .setHTML(`
                <div style="font-family: system-ui, -apple-system, sans-serif;">
                  <strong>${markerData.name || 'Unknown location'}</strong><br/>
                  <span style="color: #666; font-size: 12px;">
                    ${markerData.type.charAt(0).toUpperCase() + markerData.type.slice(1)} Point
                  </span><br/>
                  <span style="color: #666; font-size: 11px;">
                    ${markerData.lat.toFixed(4)}, ${markerData.lon.toFixed(4)}
                  </span>
                </div>
              `)
          )
          .addTo(map)

        markersRef.current.push(marker)
      })

      // Fit map to show all routes
      if (visibleRoutesData.length > 0) {
        const bounds = new maptilersdk.LngLatBounds()
        
        visibleRoutesData.forEach(route => {
          route.coordinates.forEach(([lon, lat]) => {
            bounds.extend([lon, lat])
          })
        })

        // Add extra markers to bounds
        extraMarkers.forEach(marker => {
          bounds.extend([marker.lon, marker.lat])
        })

        map.fitBounds(bounds, { 
          padding: 50,
          maxZoom: 15 // Prevent zooming in too much
        })
      }
    }

    if (map.isStyleLoaded()) {
      addRouteData()
    } else {
      map.on('load', addRouteData)
    }
  }, [routes, extraMarkers, highlightRouteId, visibleRoutes])

  return (
    <div className={`relative ${className}`}>
      <div
        ref={mapContainer}
        style={{ height: `${height}px` }}
        className="w-full rounded-md overflow-hidden"
      />
      
      {/* Loading overlay */}
      {routes.length === 0 && (
        <div 
          className="absolute inset-0 bg-gray-100 rounded-md flex items-center justify-center"
          style={{ height: `${height}px` }}
        >
          <div className="text-center text-gray-600">
            <div className="text-4xl mb-2">🗺️</div>
            <div className="text-sm">Loading route map...</div>
          </div>
        </div>
      )}
    </div>
  )
}
