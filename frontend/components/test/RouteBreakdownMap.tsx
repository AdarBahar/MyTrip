'use client'

/**
 * Route Breakdown Map Component
 *
 * Interactive map showing route breakdown with real driving routes using MapTiler SDK
 */

import React, { useState, useEffect, useRef } from 'react'
import * as maptilersdk from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import {
  formatDuration,
  formatDistance,
  getSegmentTypeDisplayName,
  getSegmentColor,
  type DayRouteBreakdownResponse
} from '@/lib/api/day-route-breakdown'

interface RouteBreakdownMapProps {
  breakdown: DayRouteBreakdownResponse | null
  center?: [number, number]
  zoom?: number
  height?: number
}

export default function RouteBreakdownMap({ breakdown, center, zoom = 12, height = 400 }: RouteBreakdownMapProps) {
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null)
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maptilersdk.Map | null>(null)
  const routeLayerIdsRef = useRef<{layer: string, source: string}[]>([])
  const markersRef = useRef<maptilersdk.Marker[]>([])

  // Calculate bounds for all points from breakdown data
  const allPoints = breakdown?.segments ?
    breakdown.segments.flatMap(segment => [segment.from_point, segment.to_point])
      .filter((point, index, array) =>
        // Remove duplicates by checking if this is the first occurrence
        array.findIndex(p => p.lat === point.lat && p.lon === point.lon) === index
      ) : []

  // Early return if no breakdown data and no center provided
  if (!breakdown && !center) {
    return (
      <div
        style={{ height: `${height}px` }}
        className="bg-gray-100 rounded-lg flex items-center justify-center"
      >
        <div className="text-center text-gray-600">
          <div className="text-4xl mb-2">🗺️</div>
          <div>No route data to display</div>
        </div>
      </div>
    )
  }

  // Initialize MapTiler map
  useEffect(() => {
    if (!mapContainer.current) return

    // Set MapTiler API key
    maptilersdk.config.apiKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY || '8znfkrc2fZwgq8Zvxw9p'

    // Calculate initial bounds or use default center
    let mapOptions: any = {
      container: mapContainer.current,
      style: maptilersdk.MapStyle.STREETS,
    }

    if (allPoints.length > 0) {
      const bounds = new maptilersdk.LngLatBounds()
      allPoints.forEach(point => {
        bounds.extend([point.lon, point.lat])
      })
      mapOptions.bounds = bounds
      mapOptions.fitBoundsOptions = { padding: 50 }
    } else {
      // Use provided center or default
      const finalCenter = center || [32.0853, 34.7818]
      mapOptions.center = [finalCenter[1], finalCenter[0]] // MapTiler uses [lng, lat]
      mapOptions.zoom = zoom
    }

    // Initialize map
    const map = new maptilersdk.Map(mapOptions)

    mapRef.current = map

    // Cleanup function
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [allPoints, center, zoom])

  // Update map with route data
  useEffect(() => {
    if (!mapRef.current || !breakdown?.segments) return

    const map = mapRef.current

    // Clear existing route layers and markers
    routeLayerIdsRef.current.forEach(({ layer, source }) => {
      if (map.getLayer(layer)) {
        map.removeLayer(layer)
      }
      if (map.getSource(source)) {
        map.removeSource(source)
      }
    })
    routeLayerIdsRef.current = []

    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []

    // Wait for map to be loaded
    const addRouteData = () => {
      // Add route segments
      breakdown.segments.forEach((segment, index) => {
        const sourceId = `route-${index}`
        const layerId = `route-layer-${index}`

        // Create GeoJSON from segment geometry
        const geojson = {
          type: 'Feature' as const,
          properties: {
            segmentIndex: index,
            fromPoint: segment.from_point.name,
            toPoint: segment.to_point.name,
            distance: segment.distance_km,
            duration: segment.duration_min
          },
          geometry: {
            type: 'LineString' as const,
            coordinates: segment.geometry.coordinates
          }
        }

        // Add source
        map.addSource(sourceId, {
          type: 'geojson',
          data: geojson
        })

        // Add layer
        map.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': getSegmentColor(segment.segment_type),
            'line-width': 4,
            'line-opacity': 0.8
          }
        })

        routeLayerIdsRef.current.push({ layer: layerId, source: sourceId })

        // Add click handler for segment
        map.on('click', layerId, (e) => {
          setSelectedSegment(selectedSegment === index ? null : index)
        })

        // Change cursor on hover
        map.on('mouseenter', layerId, () => {
          map.getCanvas().style.cursor = 'pointer'
        })

        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = ''
        })
      })

      // Add markers from breakdown data
      const markers = []
      if (breakdown.segments.length > 0) {
        // Start point from first segment
        const firstSegment = breakdown.segments[0]
        markers.push({
          ...firstSegment.from_point,
          type: 'start',
          label: 'S',
          color: '#22c55e'
        })

        // Stop points (intermediate points between segments)
        for (let i = 1; i < breakdown.segments.length; i++) {
          const segment = breakdown.segments[i]
          markers.push({
            ...segment.from_point,
            type: 'stop',
            label: i.toString(),
            color: '#3b82f6'
          })
        }

        // End point from last segment
        const lastSegment = breakdown.segments[breakdown.segments.length - 1]
        markers.push({
          ...lastSegment.to_point,
          type: 'end',
          label: 'E',
          color: '#ef4444'
        })
      }

      markers.forEach((markerData) => {
        // Create marker element
        const el = document.createElement('div')
        el.className = 'custom-marker'
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
        `
        el.textContent = markerData.label

        // Create marker
        const marker = new maptilersdk.Marker({ element: el })
          .setLngLat([markerData.lon, markerData.lat])
          .setPopup(
            new maptilersdk.Popup({ offset: 25 })
              .setHTML(`
                <div style="font-family: system-ui, -apple-system, sans-serif;">
                  <strong>${markerData.name || 'Unknown location'}</strong><br/>
                  <span style="color: #666; font-size: 12px;">
                    ${markerData.lat.toFixed(4)}, ${markerData.lon.toFixed(4)}
                  </span>
                </div>
              `)
          )
          .addTo(map)

        markersRef.current.push(marker)
      })

      // Fit map to route bounds
      const bounds = new maptilersdk.LngLatBounds()
      breakdown.segments.forEach(segment => {
        segment.geometry.coordinates.forEach(([lon, lat]) => {
          bounds.extend([lon, lat])
        })
      })
      map.fitBounds(bounds, { padding: 50 })
    }

    if (map.isStyleLoaded()) {
      addRouteData()
    } else {
      map.on('load', addRouteData)
    }
  }, [breakdown, selectedSegment])





  // Get route points for legend
  const getRoutePoints = () => {
    if (!breakdown?.segments || breakdown.segments.length === 0) {
      return { start: null, stops: [], end: null }
    }

    const firstSegment = breakdown.segments[0]
    const lastSegment = breakdown.segments[breakdown.segments.length - 1]

    // Extract intermediate stops
    const stops = []
    for (let i = 1; i < breakdown.segments.length; i++) {
      stops.push(breakdown.segments[i].from_point)
    }

    return {
      start: firstSegment.from_point,
      stops: stops,
      end: lastSegment.to_point
    }
  }

  const routePoints = getRoutePoints()

  return (
    <div className="relative">
      {/* MapTiler Interactive Map */}
      <div
        ref={mapContainer}
        className="h-96 w-full rounded-lg border border-gray-200 shadow-sm overflow-hidden relative"
      />

      {/* Route info overlay */}
      {breakdown && (
        <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 text-sm pointer-events-none">
          <div className="font-semibold text-gray-800 mb-1">🛣️ Route Overview</div>
          <div className="text-gray-600 space-y-1">
            <div className="text-xs">{breakdown.segments.length} segments</div>
            <div className="font-medium text-blue-600">{formatDistance(breakdown.total_distance_km)}</div>
            <div className="font-medium text-green-600">{formatDuration(breakdown.total_duration_min)}</div>
          </div>
        </div>
      )}

      {/* Map Legend */}
      <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs pointer-events-none">
        <div className="font-semibold text-gray-800 mb-2">🗺️ Interactive Map</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500 border border-white shadow-sm"></div>
            <span>Start: {routePoints.start?.name || 'Not set'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500 border border-white shadow-sm"></div>
            <span>{routePoints.stops.length} stops</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500 border border-white shadow-sm"></div>
            <span>End: {routePoints.end?.name || 'Not set'}</span>
          </div>
        </div>
        {breakdown && (
          <div className="mt-2 pt-2 border-t text-xs text-gray-500">
            Interactive map with zoom/pan support
          </div>
        )}
      </div>

      {/* Loading state */}
      {!breakdown && (
        <div className="absolute inset-0 bg-gray-100/90 backdrop-blur-sm rounded-lg flex items-center justify-center pointer-events-none">
          <div className="text-center text-gray-600">
            <div className="text-4xl mb-2">🗺️</div>
            <div className="font-medium">Click "Compute Route Breakdown"</div>
            <div className="text-sm">to see interactive route map</div>
          </div>
        </div>
      )}

      {/* Visual Route Representation */}
      {breakdown && (
        <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
          <h4 className="font-semibold text-gray-800 mb-3">🛣️ Route Visualization</h4>

          {/* Route Path Diagram */}
          <div className="relative">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500">Route Path</span>
              <span className="text-xs text-gray-500">{formatDistance(breakdown.total_distance_km)} • {formatDuration(breakdown.total_duration_min)}</span>
            </div>

            {/* Visual route line */}
            <div className="relative h-12 bg-gray-50 rounded-lg overflow-hidden">
              {/* Route segments */}
              <div className="absolute inset-0 flex">
                {breakdown.segments.map((segment, index) => {
                  const percentage = (segment.distance_km / breakdown.total_distance_km) * 100
                  const color = getSegmentColor(segment.segment_type)

                  return (
                    <div
                      key={index}
                      className="relative h-full flex items-center justify-center cursor-pointer transition-all hover:opacity-80"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: color + '40',
                        borderLeft: index > 0 ? '1px solid white' : 'none'
                      }}
                      onClick={() => setSelectedSegment(selectedSegment === index ? null : index)}
                      title={`${segment.from_point.name} → ${segment.to_point.name}: ${formatDistance(segment.distance_km)}`}
                    >
                      <div
                        className="h-2 rounded-full"
                        style={{ backgroundColor: color, width: '80%' }}
                      />
                    </div>
                  )
                })}
              </div>

              {/* Route points */}
              <div className="absolute inset-0 flex items-center">
                {/* Start point */}
                <div className="absolute left-0 w-4 h-4 bg-green-500 rounded-full border-2 border-white shadow-md -ml-2" />

                {/* Stop points */}
                {routePoints.stops.map((stop, index) => {
                  // Calculate position based on cumulative distance
                  let cumulativeDistance = 0
                  for (let i = 0; i <= index; i++) {
                    if (breakdown.segments[i]) {
                      cumulativeDistance += breakdown.segments[i].distance_km
                    }
                  }
                  const position = (cumulativeDistance / breakdown.total_distance_km) * 100

                  return (
                    <div
                      key={index}
                      className="absolute w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow-md flex items-center justify-center -ml-2"
                      style={{ left: `${position}%` }}
                    >
                      <span className="text-white text-xs font-bold">{index + 1}</span>
                    </div>
                  )
                })}

                {/* End point */}
                <div className="absolute right-0 w-4 h-4 bg-red-500 rounded-full border-2 border-white shadow-md -mr-2" />
              </div>
            </div>

            {/* Route labels */}
            <div className="flex justify-between mt-2 text-xs text-gray-600">
              <span>{routePoints.start?.name || 'Start'}</span>
              <span>{routePoints.end?.name || 'End'}</span>
            </div>
          </div>

          {/* Selected segment details */}
          {selectedSegment !== null && breakdown.segments[selectedSegment] && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg">
              <div className="font-medium text-gray-800">
                Segment {selectedSegment + 1}: {breakdown.segments[selectedSegment].from_point.name} → {breakdown.segments[selectedSegment].to_point.name}
              </div>
              <div className="grid grid-cols-3 gap-4 mt-2 text-sm">
                <div>
                  <span className="text-gray-600">Distance:</span>
                  <div className="font-medium">{formatDistance(breakdown.segments[selectedSegment].distance_km)}</div>
                </div>
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <div className="font-medium">{formatDuration(breakdown.segments[selectedSegment].duration_min)}</div>
                </div>
                <div>
                  <span className="text-gray-600">Instructions:</span>
                  <div className="font-medium">{breakdown.segments[selectedSegment].instructions.length} steps</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Route Points List */}
      <div className="mt-4 space-y-2">
        <h4 className="font-medium text-gray-800">Route Points</h4>

        {/* Start Point */}
        {routePoints.start && (
          <div className="flex items-center gap-3 p-2 bg-green-50 rounded-lg">
            <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
              S
            </div>
            <div className="flex-1">
              <div className="font-medium text-green-800">{routePoints.start.name}</div>
              <div className="text-xs text-green-600">
                {routePoints.start.lat.toFixed(4)}, {routePoints.start.lon.toFixed(4)}
              </div>
            </div>
          </div>
        )}

        {/* Stops */}
        {routePoints.stops.map((stop, index) => (
          <div key={index} className="flex items-center gap-3 p-2 bg-blue-50 rounded-lg">
            <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold">
              {index + 1}
            </div>
            <div className="flex-1">
              <div className="font-medium text-blue-800">{stop.name}</div>
              <div className="text-xs text-blue-600">
                {stop.lat.toFixed(4)}, {stop.lon.toFixed(4)}
              </div>
            </div>
            {breakdown && breakdown.segments[index] && (
              <div className="text-right text-xs">
                <div className="font-medium text-gray-800">
                  {formatDistance(breakdown.segments[index].distance_km)}
                </div>
                <div className="text-gray-600">
                  {formatDuration(breakdown.segments[index].duration_min)}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* End Point */}
        {routePoints.end && (
          <div className="flex items-center gap-3 p-2 bg-red-50 rounded-lg">
            <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">
              E
            </div>
            <div className="flex-1">
              <div className="font-medium text-red-800">{routePoints.end.name}</div>
              <div className="text-xs text-red-600">
                {routePoints.end.lat.toFixed(4)}, {routePoints.end.lon.toFixed(4)}
              </div>
            </div>
            {breakdown && breakdown.segments.length > 0 && (
              <div className="text-right text-xs">
                <div className="font-medium text-gray-800">
                  {formatDistance(breakdown.segments[breakdown.segments.length - 1].distance_km)}
                </div>
                <div className="text-gray-600">
                  {formatDuration(breakdown.segments[breakdown.segments.length - 1].duration_min)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Route Segments Summary */}
      {breakdown && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-800 mb-2">Route Segments</h4>
          <div className="space-y-2">
            {breakdown.segments.map((segment, index) => (
              <div
                key={index}
                className={`p-2 rounded cursor-pointer transition-colors ${
                  selectedSegment === index ? 'bg-blue-100 border-blue-300' : 'bg-white hover:bg-gray-50'
                } border`}
                onClick={() => setSelectedSegment(selectedSegment === index ? null : index)}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded"
                      style={{ backgroundColor: getSegmentColor(segment.segment_type) }}
                    />
                    <span className="text-sm font-medium">
                      Segment {index + 1}: {segment.from_point.name} → {segment.to_point.name}
                    </span>
                  </div>
                  <div className="text-right text-xs">
                    <div className="font-medium">{formatDistance(segment.distance_km)}</div>
                    <div className="text-gray-600">{formatDuration(segment.duration_min)}</div>
                  </div>
                </div>

                {selectedSegment === index && (
                  <div className="mt-2 pt-2 border-t text-xs text-gray-600">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <strong>Type:</strong> {getSegmentTypeDisplayName(segment.segment_type)}<br/>
                        <strong>Instructions:</strong> {segment.instructions.length} steps
                      </div>
                      <div>
                        <strong>Geometry:</strong> {segment.geometry.coordinates.length} points<br/>
                        <strong>From:</strong> {segment.from_point.lat.toFixed(4)}, {segment.from_point.lon.toFixed(4)}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Total Summary */}
          <div className="mt-3 pt-3 border-t">
            <div className="grid grid-cols-3 gap-4 text-center text-sm">
              <div>
                <div className="font-semibold text-blue-600">{breakdown.segments.length}</div>
                <div className="text-gray-600">Segments</div>
              </div>
              <div>
                <div className="font-semibold text-green-600">{formatDistance(breakdown.total_distance_km)}</div>
                <div className="text-gray-600">Total Distance</div>
              </div>
              <div>
                <div className="font-semibold text-orange-600">{formatDuration(breakdown.total_duration_min)}</div>
                <div className="text-gray-600">Total Duration</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {!breakdown && (
        <div className="absolute inset-0 bg-gray-100/80 backdrop-blur-sm rounded-lg flex items-center justify-center">
          <div className="text-center text-gray-600">
            <div className="text-4xl mb-2">🗺️</div>
            <div className="font-medium">Click "Compute Route Breakdown"</div>
            <div className="text-sm">to see routes on the map</div>
          </div>
        </div>
      )}
    </div>
  )
}
