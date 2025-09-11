'use client'

/**
 * Address Search Demo Page
 * 
 * Demonstrates address-specific search functionality
 */

import React, { useState } from 'react'
import PlacesSearch from '@/components/ui/PlacesSearch'
import { MapPin, Home, Building, Navigation, Search } from 'lucide-react'

interface PlaceDetails {
  id: string
  name: string
  formatted_address: string
  types: string[]
  center: { lat: number; lng: number }
  metadata?: {
    country?: string
    postcode?: string
  }
}

export default function AddressSearchDemo() {
  const [selectedAddress, setSelectedAddress] = useState<PlaceDetails | null>(null)
  const [searchHistory, setSearchHistory] = useState<PlaceDetails[]>([])

  const handleAddressSelect = (place: PlaceDetails) => {
    setSelectedAddress(place)
    setSearchHistory(prev => [place, ...prev.slice(0, 4)])
  }

  const addressExamples = [
    {
      title: "Street Names",
      examples: [
        { query: "rothschild", description: "Search for Rothschild Boulevard" },
        { query: "ben yehuda", description: "Search for Ben Yehuda Street" },
        { query: "ירקון", description: "Hebrew: Yarkon Street" },
        { query: "בן יהודה", description: "Hebrew: Ben Yehuda Street" }
      ]
    },
    {
      title: "Street + Number",
      examples: [
        { query: "123 ben yehuda", description: "Number + street name" },
        { query: "1 rothschild", description: "Specific numbered address" },
        { query: "בן יהודה 123", description: "Hebrew: 123 Ben Yehuda" },
        { query: "ירקון 1", description: "Hebrew: 1 Yarkon Street" }
      ]
    },
    {
      title: "Full Address (Street, Number, City)",
      examples: [
        { query: "123 ben yehuda tel aviv", description: "Complete address with city" },
        { query: "rothschild 1 tel aviv", description: "Boulevard with city" },
        { query: "100 oxford street london", description: "International address" },
        { query: "1234 broadway new york", description: "US address format" }
      ]
    },
    {
      title: "Address Components",
      examples: [
        { query: "boulevard", description: "Search by street type" },
        { query: "street", description: "Find streets" },
        { query: "שדרות", description: "Hebrew: Boulevard" },
        { query: "רחוב", description: "Hebrew: Street" }
      ]
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center gap-3">
              <Home className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Address Search Demo</h1>
                <p className="text-gray-600">Find specific addresses and street locations</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Search Column */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Address-Only Search */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Home className="h-5 w-5 text-green-600" />
                Address-Only Search
              </h2>
              <p className="text-gray-600 mb-4">
                Search limited to addresses only. Try "rothschild", "downing", or "רוטשילד".
              </p>
              <PlacesSearch
                onPlaceSelect={handleAddressSelect}
                placeholder="Search for addresses..."
                categories={['address']}
                showCategories={true}
                size="lg"
                variant="bordered"
                supportRTL={true}
                language="en"
              />
            </div>

            {/* Mixed Search with Address Priority */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Search className="h-5 w-5 text-blue-600" />
                Mixed Search (Addresses + POIs)
              </h2>
              <p className="text-gray-600 mb-4">
                Search all types of places. Addresses will appear alongside POIs.
              </p>
              <PlacesSearch
                onPlaceSelect={handleAddressSelect}
                placeholder="Search addresses and places..."
                showCategories={true}
                supportRTL={true}
                language="en"
              />
            </div>

            {/* Hebrew Address Search */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Building className="h-5 w-5 text-purple-600" />
                Hebrew Address Search
              </h2>
              <p className="text-gray-600 mb-4">
                Search for addresses in Hebrew. Try "רוטשילד" or "שדרות".
              </p>
              <PlacesSearch
                onPlaceSelect={handleAddressSelect}
                placeholder="חפש כתובות..."
                categories={['address']}
                countries={['IL']}
                showCategories={true}
                supportRTL={true}
                language="he"
                variant="minimal"
              />
            </div>

            {/* Search Examples */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Address Search Examples</h2>
              <div className="space-y-6">
                {addressExamples.map((section, sectionIndex) => (
                  <div key={sectionIndex}>
                    <h3 className="text-lg font-medium text-gray-800 mb-3">{section.title}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {section.examples.map((example, index) => (
                        <div
                          key={index}
                          className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                          onClick={() => {
                            // You could trigger a search here
                            console.log('Search for:', example.query)
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

            {/* API Examples */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">API Examples</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-800 mb-2">Street + Number Search</h3>
                  <pre className="bg-gray-900 text-gray-100 p-3 rounded text-sm overflow-x-auto">
{`GET /places/v1/places/suggest?q=123 ben yehuda&categories=address&limit=5`}
                  </pre>
                </div>
                <div>
                  <h3 className="font-medium text-gray-800 mb-2">Full Address with City</h3>
                  <pre className="bg-gray-900 text-gray-100 p-3 rounded text-sm overflow-x-auto">
{`GET /places/v1/places/suggest?q=rothschild 1 tel aviv&limit=5`}
                  </pre>
                </div>
                <div>
                  <h3 className="font-medium text-gray-800 mb-2">Hebrew Full Address</h3>
                  <pre className="bg-gray-900 text-gray-100 p-3 rounded text-sm overflow-x-auto">
{`GET /places/v1/places/suggest?q=בן יהודה 123&countries=IL`}
                  </pre>
                </div>
                <div>
                  <h3 className="font-medium text-gray-800 mb-2">International Address</h3>
                  <pre className="bg-gray-900 text-gray-100 p-3 rounded text-sm overflow-x-auto">
{`GET /places/v1/places/suggest?q=100 oxford street london&countries=GB`}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            
            {/* Selected Address */}
            {selectedAddress && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-green-600" />
                  Selected Address
                </h3>
                <div className="space-y-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{selectedAddress.name}</h4>
                    <p className="text-sm text-gray-600" dir={selectedAddress.name.match(/[\u0590-\u05FF]/) ? 'rtl' : 'ltr'}>
                      {selectedAddress.formatted_address}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Latitude:</span>
                      <div className="font-mono">{selectedAddress.center.lat.toFixed(6)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Longitude:</span>
                      <div className="font-mono">{selectedAddress.center.lng.toFixed(6)}</div>
                    </div>
                  </div>

                  <div>
                    <span className="text-gray-500 text-sm">Type:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedAddress.types.map((type, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800"
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>

                  {selectedAddress.metadata?.country && (
                    <div className="text-sm">
                      <span className="text-gray-500">Country:</span>
                      <span className="ml-2 font-medium">{selectedAddress.metadata.country}</span>
                    </div>
                  )}

                  {selectedAddress.metadata?.postcode && (
                    <div className="text-sm">
                      <span className="text-gray-500">Postcode:</span>
                      <span className="ml-2 font-medium">{selectedAddress.metadata.postcode}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Available Addresses */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Test Addresses</h3>
              <div className="space-y-3 text-sm">
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="font-medium text-green-800">Tel Aviv Addresses</div>
                  <div className="text-green-700 mt-1">
                    • 123 Ben Yehuda Street<br/>
                    • 1 Yarkon Street<br/>
                    • 45 Allenby Street<br/>
                    • 67 Sheinkin Street<br/>
                    • 1 Rothschild Boulevard
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="font-medium text-blue-800">Hebrew Addresses</div>
                  <div className="text-blue-700 mt-1" dir="rtl">
                    • בן יהודה 123, תל אביב-יפו<br/>
                    • ירקון 1, תל אביב-יפו<br/>
                    • אלנבי 45, תל אביב-יפו<br/>
                    • שינקין 67, תל אביב-יפו<br/>
                    • שדרות רוטשילד 1, תל אביב-יפו
                  </div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <div className="font-medium text-purple-800">International Addresses</div>
                  <div className="text-purple-700 mt-1">
                    • 100 Oxford Street, London<br/>
                    • 1234 Broadway, New York<br/>
                    • 10 Downing Street, London
                  </div>
                </div>
              </div>
            </div>

            {/* Search Tips */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Address Search Tips</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>Use <code className="bg-gray-100 px-1 rounded">categories=['address']</code> to search only addresses</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>Search by street name: "rothschild", "downing"</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>Include numbers: "1 rothschild", "10 downing"</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>Hebrew support: "רוטשילד", "שדרות"</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>Street types: "boulevard", "street", "avenue"</span>
                </div>
              </div>
            </div>

            {/* Recent Searches */}
            {searchHistory.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Address Searches</h3>
                <div className="space-y-2">
                  {searchHistory.map((address, index) => (
                    <div
                      key={`${address.id}-${index}`}
                      className="flex items-start gap-3 p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => setSelectedAddress(address)}
                    >
                      <Home className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-gray-900 text-sm truncate">{address.name}</div>
                        <div className="text-xs text-gray-600 truncate">{address.formatted_address}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
