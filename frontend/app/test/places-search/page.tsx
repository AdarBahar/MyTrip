'use client'

/**
 * Places Search Demo Page
 * 
 * Demonstrates the PlacesSearch component with various configurations
 */

import React, { useState } from 'react'
import PlacesSearch from '@/components/ui/PlacesSearch'
import { MapPin, Settings, Code, Eye } from 'lucide-react'

interface PlaceCoordinates {
  lat: number
  lng: number
}

interface PlaceDetails {
  id: string
  name: string
  formatted_address: string
  types: string[]
  center: PlaceCoordinates
  bbox?: {
    minLat: number
    minLng: number
    maxLat: number
    maxLng: number
  }
  categories: string[]
  score: number
  timezone?: string
  metadata?: {
    country?: string
    postcode?: string
  }
  phone?: string
  website?: string
  rating?: number
  popularity?: number
}

export default function PlacesSearchDemo() {
  const [selectedPlace, setSelectedPlace] = useState<PlaceDetails | null>(null)
  const [selectedCoordinates, setSelectedCoordinates] = useState<PlaceCoordinates | null>(null)
  const [searchHistory, setSearchHistory] = useState<PlaceDetails[]>([])
  const [showCode, setShowCode] = useState(false)
  const [useRealGeocoding, setUseRealGeocoding] = useState(false)

  // Tel Aviv coordinates for proximity bias
  const telAvivCoords = { lat: 32.0853, lng: 34.7818 }

  const handlePlaceSelect = (place: PlaceDetails) => {
    setSelectedPlace(place)
    setSearchHistory(prev => [place, ...prev.slice(0, 4)]) // Keep last 5
  }

  const handleCoordinatesSelect = (coordinates: PlaceCoordinates, place: PlaceDetails) => {
    setSelectedCoordinates(coordinates)
    console.log('Selected coordinates:', coordinates, 'for place:', place.name)
  }

  const codeExample = `import PlacesSearch from '@/components/ui/PlacesSearch'

// Basic usage
<PlacesSearch
  onPlaceSelect={(place) => console.log('Selected:', place)}
  onCoordinatesSelect={(coords, place) => {
    // Center map on coordinates
    map.setCenter(coords)
    // Add marker
    addMarker(coords, place)
  }}
/>

// Advanced usage with filters
<PlacesSearch
  placeholder="Search hotels in Tel Aviv..."
  categories={['hotel', 'lodging']}
  countries={['IL']}
  proximityBias={{ lat: 32.0853, lng: 34.7818 }}
  radius={10000}
  size="lg"
  variant="bordered"
  showCategories={true}
  clearOnSelect={false}
/>`

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <MapPin className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Places Search Component</h1>
                  <p className="text-gray-600">Interactive demo of the reusable Places Search UI component</p>
                </div>
              </div>

              {/* Search Mode Toggle */}
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Search Mode:</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useRealGeocoding}
                    onChange={(e) => setUseRealGeocoding(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-gray-700">
                    {useRealGeocoding ? 'Real Geocoding' : 'Mock Data'}
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Mode Status */}
        <div className="mb-6">
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
            useRealGeocoding
              ? 'bg-green-100 text-green-800 border border-green-200'
              : 'bg-blue-100 text-blue-800 border border-blue-200'
          }`}>
            <div className={`w-2 h-2 rounded-full ${useRealGeocoding ? 'bg-green-500' : 'bg-blue-500'}`}></div>
            {useRealGeocoding
              ? 'Real Geocoding Mode - Worldwide search using MapTiler API'
              : 'Mock Data Mode - Limited test data for demonstration'
            }
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Main Demo Column */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Basic Search */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {useRealGeocoding ? 'Real-World Search' : 'Basic Search'}
              </h2>
              <p className="text-gray-600 mb-4">
                {useRealGeocoding
                  ? 'Search any address, city, or location worldwide using MapTiler geocoding API.'
                  : 'Start typing to see type-ahead suggestions. Try searching for "tel", "hotel", "museum", or "restaurant".'
                }
              </p>
              <PlacesSearch
                onPlaceSelect={handlePlaceSelect}
                onCoordinatesSelect={handleCoordinatesSelect}
                placeholder={useRealGeocoding
                  ? "Search anywhere in the world..."
                  : "Search for places, addresses, or points of interest..."
                }
                useRealGeocoding={useRealGeocoding}
              />
            </div>

            {/* Search with Proximity Bias */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {useRealGeocoding ? 'Global Search' : 'Search with Proximity Bias'}
              </h2>
              <p className="text-gray-600 mb-4">
                {useRealGeocoding
                  ? 'Search for any location worldwide. Try "New York", "Tokyo", "London", or "תל אביב".'
                  : 'Results are biased towards Tel Aviv area. Distance is shown for each result.'
                }
              </p>
              <PlacesSearch
                onPlaceSelect={handlePlaceSelect}
                onCoordinatesSelect={handleCoordinatesSelect}
                placeholder={useRealGeocoding ? "Search worldwide..." : "Search near Tel Aviv..."}
                proximityBias={useRealGeocoding ? undefined : telAvivCoords}
                radius={useRealGeocoding ? undefined : 10000}
                size="lg"
                useRealGeocoding={useRealGeocoding}
              />
            </div>

            {/* Category Filtered Search */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {useRealGeocoding ? 'Address Search' : 'Category Filtered Search'}
              </h2>
              <p className="text-gray-600 mb-4">
                {useRealGeocoding
                  ? 'Search for specific addresses with street numbers. Try "123 Main Street" or "1600 Pennsylvania Avenue".'
                  : 'Search limited to hotels and restaurants only.'
                }
              </p>
              <PlacesSearch
                onPlaceSelect={handlePlaceSelect}
                onCoordinatesSelect={handleCoordinatesSelect}
                placeholder={useRealGeocoding ? "Search specific addresses..." : "Search hotels and restaurants..."}
                categories={useRealGeocoding ? undefined : ['hotel', 'restaurant', 'lodging']}
                variant="bordered"
                useRealGeocoding={useRealGeocoding}
              />
            </div>

            {/* Country Filtered Search */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {useRealGeocoding ? 'Hebrew Search' : 'Country Filtered Search'}
              </h2>
              <p className="text-gray-600 mb-4">
                {useRealGeocoding
                  ? 'Search in Hebrew for Israeli locations. Try "תל אביב", "ירושלים", or "חיפה".'
                  : 'Search limited to Israel only.'
                }
              </p>
              <PlacesSearch
                onPlaceSelect={handlePlaceSelect}
                onCoordinatesSelect={handleCoordinatesSelect}
                placeholder={useRealGeocoding ? "חפש מקומות בישראל..." : "Search in Israel..."}
                countries={useRealGeocoding ? undefined : ['IL']}
                variant="minimal"
                clearOnSelect={false}
                supportRTL={true}
                language="he"
                useRealGeocoding={useRealGeocoding}
              />
            </div>

            {/* Different Sizes */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Different Sizes</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Small</label>
                  <PlacesSearch
                    onPlaceSelect={handlePlaceSelect}
                    placeholder="Small search..."
                    size="sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Medium (Default)</label>
                  <PlacesSearch
                    onPlaceSelect={handlePlaceSelect}
                    placeholder="Medium search..."
                    size="md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Large</label>
                  <PlacesSearch
                    onPlaceSelect={handlePlaceSelect}
                    placeholder="Large search..."
                    size="lg"
                  />
                </div>
              </div>
            </div>

            {/* Code Example */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Usage Example</h2>
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
            
            {/* Selected Place */}
            {selectedPlace && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Selected Place</h3>
                <div className="space-y-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{selectedPlace.name}</h4>
                    <p className="text-sm text-gray-600">{selectedPlace.formatted_address}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Latitude:</span>
                      <div className="font-mono">{selectedPlace.center.lat.toFixed(6)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Longitude:</span>
                      <div className="font-mono">{selectedPlace.center.lng.toFixed(6)}</div>
                    </div>
                  </div>

                  {selectedPlace.types.length > 0 && (
                    <div>
                      <span className="text-gray-500 text-sm">Types:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedPlace.types.map((type, index) => (
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

                  {selectedPlace.rating && (
                    <div className="text-sm">
                      <span className="text-gray-500">Rating:</span>
                      <span className="ml-2 font-medium">⭐ {selectedPlace.rating}/5</span>
                    </div>
                  )}

                  {selectedPlace.phone && (
                    <div className="text-sm">
                      <span className="text-gray-500">Phone:</span>
                      <span className="ml-2">{selectedPlace.phone}</span>
                    </div>
                  )}

                  {selectedPlace.website && (
                    <div className="text-sm">
                      <span className="text-gray-500">Website:</span>
                      <a
                        href={selectedPlace.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        Visit
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Search History */}
            {searchHistory.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Searches</h3>
                <div className="space-y-3">
                  {searchHistory.map((place, index) => (
                    <div
                      key={`${place.id}-${index}`}
                      className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => setSelectedPlace(place)}
                    >
                      <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-gray-900 truncate">{place.name}</div>
                        <div className="text-sm text-gray-600 truncate">{place.formatted_address}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Features */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Type-ahead suggestions (200ms debounce)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Keyboard navigation (↑↓ Enter Esc)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Category icons and filtering</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Proximity bias and distance display</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Text highlighting in results</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Loading states and error handling</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Mobile responsive design</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Multiple size and style variants</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
