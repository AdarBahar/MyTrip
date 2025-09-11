'use client'

/**
 * Geocoding Map Component
 * 
 * Interactive map that displays geocoding search results
 * using MapTiler SDK
 */

import React, { useEffect, useRef, useState } from 'react'
import { MapPin, Navigation, Maximize2, Minimize2 } from 'lucide-react'
import { type GeocodingResult } from '@/lib/api/places'

// MapTiler SDK types
declare global {
  interface Window {
    maptilersdk: any
  }
}

interface GeocodingMapProps {
  result: GeocodingResult | null
  height?: number
  className?: string
  interactive?: boolean
  showControls?: boolean
  onMapClick?: (lat: number, lng: number) => void
}

export default function GeocodingMap({
  result,
  height = 400,
  className = "",
  interactive = true,
  showControls = true,
  onMapClick
}: GeocodingMapProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<any>(null)
  const markerRef = useRef<any>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [mapError, setMapError] = useState<string | null>(null)

  // Initialize map
  useEffect(() => {
    const initializeMap = async () => {
      try {
        // Load MapTiler SDK if not already loaded
        if (!window.maptilersdk) {
          const script = document.createElement('script')
          script.src = 'https://cdn.maptiler.com/maptiler-sdk-js/v2.0.3/maptiler-sdk.umd.js'
          script.async = true
          
          await new Promise((resolve, reject) => {
            script.onload = resolve
            script.onerror = reject
            document.head.appendChild(script)
          })

          // Load CSS
          const link = document.createElement('link')
          link.rel = 'stylesheet'
          link.href = 'https://cdn.maptiler.com/maptiler-sdk-js/v2.0.3/maptiler-sdk.css'
          document.head.appendChild(link)
        }

        // Configure API key
        const apiKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY
        if (apiKey && window.maptilersdk) {
          window.maptilersdk.config.apiKey = apiKey
        }

        // Initialize map
        if (mapContainer.current && !mapRef.current && window.maptilersdk) {
          mapRef.current = new window.maptilersdk.Map({
            container: mapContainer.current,
            style: window.maptilersdk.MapStyle.STREETS,
            center: [0, 0], // Will be updated when result is available
            zoom: 2,
            interactive
          })

          // Add click handler
          if (onMapClick) {
            mapRef.current.on('click', (e: any) => {
              const { lng, lat } = e.lngLat
              onMapClick(lat, lng)
            })
          }

          setMapLoaded(true)
        }
      } catch (error) {
        console.error('Failed to initialize map:', error)
        setMapError('Failed to load map')
      }
    }

    initializeMap()

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [interactive, onMapClick])

  // Update map when result changes
  useEffect(() => {
    if (!mapRef.current || !result || !mapLoaded) return

    try {
      // Remove existing marker
      if (markerRef.current) {
        markerRef.current.remove()
        markerRef.current = null
      }

      // Add new marker
      if (window.maptilersdk) {
        markerRef.current = new window.maptilersdk.Marker({ color: '#3B82F6' })
          .setLngLat([result.lon, result.lat])
          .addTo(mapRef.current)

        // Add popup with address info
        const popup = new window.maptilersdk.Popup({ offset: 25 })
          .setHTML(`
            <div class="p-2">
              <div class="font-medium text-gray-900 mb-1">${result.formatted_address || result.address}</div>
              <div class="text-xs text-gray-600">
                ${result.lat.toFixed(6)}, ${result.lon.toFixed(6)}
              </div>
              ${result.types && result.types.length > 0 ? `
                <div class="text-xs text-gray-500 mt-1">
                  ${result.types.join(', ')}
                </div>
              ` : ''}
            </div>
          `)

        markerRef.current.setPopup(popup)

        // Center map on result
        mapRef.current.easeTo({
          center: [result.lon, result.lat],
          zoom: 14,
          duration: 1000
        })
      }
    } catch (error) {
      console.error('Error updating map:', error)
    }
  }, [result, mapLoaded])

  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  // Handle fullscreen effect
  useEffect(() => {
    if (mapRef.current) {
      // Trigger map resize after fullscreen change
      setTimeout(() => {
        mapRef.current.resize()
      }, 100)
    }
  }, [isFullscreen])

  if (mapError) {
    return (
      <div 
        className={`bg-red-50 border border-red-200 rounded-lg flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <div className="text-center text-red-600">
          <MapPin className="h-8 w-8 mx-auto mb-2" />
          <div className="text-sm">{mapError}</div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div 
        className={`bg-gray-100 border border-gray-200 rounded-lg flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <div className="text-center text-gray-500">
          <Navigation className="h-8 w-8 mx-auto mb-2" />
          <div className="text-sm">Search for a location to see it on the map</div>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {/* Map Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">Map Location</span>
        </div>
        
        {showControls && (
          <div className="flex items-center gap-2">
            <button
              onClick={toggleFullscreen}
              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </button>
          </div>
        )}
      </div>

      {/* Map Container */}
      <div 
        ref={mapContainer}
        className={`
          bg-gray-200 border border-gray-200 rounded-b-lg
          ${isFullscreen ? 'fixed inset-0 z-50 rounded-none' : ''}
        `}
        style={{ 
          height: isFullscreen ? '100vh' : height,
          width: isFullscreen ? '100vw' : '100%'
        }}
      />

      {/* Loading Overlay */}
      {!mapLoaded && !mapError && (
        <div 
          className="absolute inset-0 bg-gray-100 flex items-center justify-center rounded-lg"
          style={{ height }}
        >
          <div className="text-center text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <div className="text-sm">Loading map...</div>
          </div>
        </div>
      )}

      {/* Location Info Overlay */}
      {result && mapLoaded && (
        <div className="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg p-3 shadow-lg">
          <div className="text-sm font-medium text-gray-900 truncate">
            {result.formatted_address || result.address}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            <span className="font-mono">{result.lat.toFixed(6)}, {result.lon.toFixed(6)}</span>
            {result.types && result.types.length > 0 && (
              <span className="ml-2">• {result.types.join(', ')}</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
