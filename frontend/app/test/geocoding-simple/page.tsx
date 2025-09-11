'use client'

/**
 * Simple Geocoding Test
 * 
 * Minimal test to debug click handler issues
 */

import React, { useState } from 'react'
import GeocodingSearch from '@/components/ui/GeocodingSearch'
import { type GeocodingResult } from '@/lib/api/places'

export default function SimpleGeocodingTest() {
  const [result, setResult] = useState<GeocodingResult | null>(null)
  const [clickCount, setClickCount] = useState(0)

  const handleLocationSelect = (selectedResult: GeocodingResult) => {
    console.log('=== SIMPLE TEST: Location selected ===')
    console.log('Address:', selectedResult.formatted_address || selectedResult.address)
    console.log('Coordinates:', selectedResult.lat, selectedResult.lon)
    console.log('Full result:', selectedResult)
    
    setResult(selectedResult)
    setClickCount(prev => prev + 1)
    
    // Show alert to confirm it's working
    alert(`Selected: ${selectedResult.formatted_address || selectedResult.address}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Simple Geocoding Click Test</h1>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4">Test Search</h2>
          <p className="text-gray-600 mb-4">
            Type an address and click on a suggestion. You should see an alert and the result below.
          </p>
          
          <GeocodingSearch
            onLocationSelect={handleLocationSelect}
            placeholder="Type 'New York' and click a suggestion..."
            autoSearch={true}
            minSearchLength={3}
            maxResults={5}
          />
        </div>

        {/* Debug Info */}
        <div className="mt-6 bg-gray-100 p-4 rounded-lg">
          <h3 className="font-semibold mb-2">Debug Info</h3>
          <div className="text-sm space-y-1">
            <div>Click count: <strong>{clickCount}</strong></div>
            <div>Selected result: <strong>{result ? 'Yes' : 'No'}</strong></div>
            {result && (
              <div className="mt-2 p-2 bg-white rounded border">
                <div><strong>Address:</strong> {result.formatted_address || result.address}</div>
                <div><strong>Coordinates:</strong> {result.lat}, {result.lon}</div>
                <div><strong>Types:</strong> {result.types?.join(', ') || 'None'}</div>
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">Test Instructions</h3>
          <ol className="text-sm text-blue-700 space-y-1">
            <li>1. Type "New York" in the search box</li>
            <li>2. Wait for suggestions to appear</li>
            <li>3. Click on any suggestion</li>
            <li>4. You should see an alert popup</li>
            <li>5. The debug info should update</li>
            <li>6. Check browser console for logs</li>
          </ol>
        </div>
      </div>
    </div>
  )
}
