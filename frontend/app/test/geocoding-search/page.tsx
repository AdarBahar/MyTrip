'use client'

/**
 * Free-Form Geocoding Search Demo
 * 
 * Demonstrates real-world geocoding search using MapTiler API
 * with interactive map display
 */

import React, { useState } from 'react'
import GeocodingSearch from '@/components/ui/GeocodingSearch'
import GeocodingMap from '@/components/ui/GeocodingMap'
import { Globe, MapPin, Search, Zap, Code, Eye } from 'lucide-react'
import { type GeocodingResult } from '@/lib/api/places'

export default function GeocodingSearchDemo() {
  const [selectedLocation, setSelectedLocation] = useState<GeocodingResult | null>(null)
  const [searchHistory, setSearchHistory] = useState<GeocodingResult[]>([])
  const [showCode, setShowCode] = useState(false)

  const handleLocationSelect = (result: GeocodingResult) => {
    console.log('Demo: Location selected:', result.formatted_address || result.address)
    console.log('Demo: Coordinates:', result.lat, result.lon)

    setSelectedLocation(result)
    setSearchHistory(prev => {
      // Add to history, avoiding duplicates
      const filtered = prev.filter(item =>
        !(item.lat === result.lat && item.lon === result.lon)
      )
      return [result, ...filtered.slice(0, 4)] // Keep last 5
    })
  }

  const handleMapClick = (lat: number, lng: number) => {
    console.log('Map clicked at:', lat, lng)
    // Could trigger reverse geocoding here
  }

  const exampleSearches = [
    {
      category: "Cities & Countries",
      examples: [
        { query: "New York, USA", description: "Major city search" },
        { query: "Tokyo, Japan", description: "International city" },
        { query: "London, UK", description: "European capital" },
        { query: "תל אביב, ישראל", description: "Hebrew city name" }
      ]
    },
    {
      category: "Specific Addresses",
      examples: [
        { query: "1600 Pennsylvania Avenue, Washington DC", description: "Famous address" },
        { query: "Times Square, New York", description: "Landmark location" },
        { query: "Eiffel Tower, Paris", description: "Tourist attraction" },
        { query: "שדרות רוטשילד 1, תל אביב", description: "Hebrew address" }
      ]
    },
    {
      category: "Natural Features",
      examples: [
        { query: "Mount Everest", description: "Mountain peak" },
        { query: "Amazon River", description: "River system" },
        { query: "Sahara Desert", description: "Desert region" },
        { query: "Mediterranean Sea", description: "Sea/ocean" }
      ]
    },
    {
      category: "Postal Codes & Areas",
      examples: [
        { query: "90210, USA", description: "US ZIP code" },
        { query: "SW1A 1AA, London", description: "UK postcode" },
        { query: "75001, Paris", description: "French postal code" },
        { query: "10001, Tel Aviv", description: "Israeli postal code" }
      ]
    }
  ]

  const codeExample = `import GeocodingSearch from '@/components/ui/GeocodingSearch'
import GeocodingMap from '@/components/ui/GeocodingMap'

// Basic usage
<GeocodingSearch
  onLocationSelect={(result) => {
    console.log('Selected:', result.formatted_address)
    console.log('Coordinates:', result.lat, result.lon)
  }}
  placeholder="Search anywhere in the world..."
/>

// With map integration
const [location, setLocation] = useState(null)

<GeocodingSearch
  onLocationSelect={setLocation}
  showMap={false}
/>

<GeocodingMap
  result={location}
  height={400}
  onMapClick={(lat, lng) => {
    console.log('Map clicked:', lat, lng)
  }}
/>`

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center gap-3">
              <Globe className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Free-Form Geocoding Search</h1>
                <p className="text-gray-600">Search for any address, city, or location worldwide using MapTiler API</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Search Column */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Live Geocoding Search */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Search className="h-5 w-5 text-blue-600" />
                Live Geocoding Search
              </h2>
              <p className="text-gray-600 mb-4">
                Search for any address, city, landmark, or location worldwide. Results are powered by MapTiler's global geocoding API.
              </p>
              <GeocodingSearch
                onLocationSelect={handleLocationSelect}
                placeholder="Search for any location worldwide..."
                autoSearch={true}
                minSearchLength={3}
                maxResults={8}
                supportRTL={true}
                showMap={false}
              />
            </div>

            {/* Interactive Map */}
            {selectedLocation && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <GeocodingMap
                  result={selectedLocation}
                  height={400}
                  interactive={true}
                  showControls={true}
                  onMapClick={handleMapClick}
                />
              </div>
            )}

            {/* Search Examples */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Examples</h2>
              <p className="text-gray-600 mb-6">
                Try these example searches to see the geocoding capabilities:
              </p>
              
              <div className="space-y-6">
                {exampleSearches.map((section, sectionIndex) => (
                  <div key={sectionIndex}>
                    <h3 className="text-lg font-medium text-gray-800 mb-3">{section.category}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {section.examples.map((example, index) => (
                        <div
                          key={index}
                          className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                          onClick={() => {
                            // You could auto-fill the search here
                            console.log('Example search:', example.query)
                          }}
                        >
                          <div className="font-mono text-sm text-blue-600 mb-1">
                            "{example.query}"
                          </div>
                          <div className="text-xs text-gray-600">
                            {example.description}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* API Features */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">API Features</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Real-time geocoding</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Worldwide coverage</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Multi-language support</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Address normalization</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Precise coordinates</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Location types</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Interactive maps</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Mobile responsive</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Code Example */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Integration Example</h2>
                <button
                  onClick={() => setShowCode(!showCode)}
                  className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                >
                  <Code className="h-4 w-4" />
                  {showCode ? 'Hide' : 'Show'} Code
                </button>
              </div>
              
              {showCode && (
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                  <code>{codeExample}</code>
                </pre>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            
            {/* Selected Location */}
            {selectedLocation && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-blue-600" />
                  Selected Location
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="font-medium text-gray-900 break-words">
                      {selectedLocation.formatted_address || selectedLocation.address}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500">Coordinates:</span>
                      <div className="font-mono text-xs">
                        {selectedLocation.lat.toFixed(6)}, {selectedLocation.lon.toFixed(6)}
                      </div>
                    </div>
                  </div>

                  {selectedLocation.types && selectedLocation.types.length > 0 && (
                    <div>
                      <span className="text-gray-500 text-sm">Types:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedLocation.types.map((type, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedLocation.place_id && (
                    <div className="text-xs text-gray-500">
                      Place ID: {selectedLocation.place_id}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Search History */}
            {searchHistory.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Searches</h3>
                <div className="space-y-2">
                  {searchHistory.map((location, index) => (
                    <div
                      key={`${location.lat}-${location.lon}-${index}`}
                      className="flex items-start gap-3 p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => setSelectedLocation(location)}
                    >
                      <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-gray-900 text-sm truncate">
                          {location.formatted_address || location.address}
                        </div>
                        <div className="text-xs text-gray-600 font-mono">
                          {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* API Info */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">API Information</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Provider:</span>
                  <span className="ml-2 font-medium">MapTiler Geocoding API</span>
                </div>
                <div>
                  <span className="text-gray-500">Coverage:</span>
                  <span className="ml-2">Worldwide</span>
                </div>
                <div>
                  <span className="text-gray-500">Languages:</span>
                  <span className="ml-2">Multi-language support</span>
                </div>
                <div>
                  <span className="text-gray-500">Accuracy:</span>
                  <span className="ml-2">Address-level precision</span>
                </div>
                <div>
                  <span className="text-gray-500">Response Time:</span>
                  <span className="ml-2">~200-500ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
