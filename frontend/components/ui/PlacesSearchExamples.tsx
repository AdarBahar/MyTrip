'use client'

/**
 * Places Search Usage Examples
 * 
 * Collection of common usage patterns for the PlacesSearch component
 */

import React, { useState } from 'react'
import PlacesSearch from './PlacesSearch'

// Example 1: Basic Trip Planning Search
export function TripPlanningSearch() {
  const [selectedDestination, setSelectedDestination] = useState<any>(null)

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Trip Planning Search</h3>
      <PlacesSearch
        placeholder="Where would you like to go?"
        onPlaceSelect={(place) => {
          setSelectedDestination(place)
          // Add to trip itinerary
          console.log('Adding to trip:', place)
        }}
        onCoordinatesSelect={(coords, place) => {
          // Center map on destination
          console.log('Center map on:', coords)
        }}
        showCategories={true}
        size="lg"
        variant="bordered"
      />
      
      {selectedDestination && (
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            Selected: <strong>{selectedDestination.name}</strong>
          </p>
        </div>
      )}
    </div>
  )
}

// Example 2: Hotel Search with Filters
export function HotelSearch({ location }: { location?: { lat: number; lng: number } }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Hotel Search</h3>
      <PlacesSearch
        placeholder="Search for hotels..."
        categories={['hotel', 'lodging', 'accommodation']}
        proximityBias={location}
        radius={5000}
        onPlaceSelect={(place) => {
          // Open hotel booking flow
          console.log('Book hotel:', place)
        }}
        showCategories={false}
        clearOnSelect={false}
      />
    </div>
  )
}

// Example 3: Restaurant Finder
export function RestaurantFinder({ userLocation }: { userLocation?: { lat: number; lng: number } }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Restaurant Finder</h3>
      <PlacesSearch
        placeholder="Find restaurants nearby..."
        categories={['restaurant', 'food', 'cafe', 'bar']}
        proximityBias={userLocation}
        radius={2000}
        onPlaceSelect={(place) => {
          // Show restaurant details
          console.log('View restaurant:', place)
        }}
        size="md"
        variant="default"
      />
    </div>
  )
}

// Example 4: Address Picker for Forms
export function AddressPicker({ 
  onAddressSelect 
}: { 
  onAddressSelect: (address: string, coordinates: { lat: number; lng: number }) => void 
}) {
  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-700">
        Delivery Address
      </label>
      <PlacesSearch
        placeholder="Enter your address..."
        categories={['address']}
        onCoordinatesSelect={(coords, place) => {
          onAddressSelect(place.formatted_address, coords)
        }}
        size="md"
        variant="default"
        clearOnSelect={false}
      />
    </div>
  )
}

// Example 5: Multi-location Trip Builder
export function TripBuilder() {
  const [stops, setStops] = useState<any[]>([])

  const addStop = (place: any) => {
    setStops(prev => [...prev, place])
  }

  const removeStop = (index: number) => {
    setStops(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Trip Builder</h3>
      
      <PlacesSearch
        placeholder="Add a stop to your trip..."
        onPlaceSelect={addStop}
        showCategories={true}
        size="lg"
      />

      {stops.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Trip Stops:</h4>
          {stops.map((stop, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium">{stop.name}</div>
                <div className="text-sm text-gray-600">{stop.formatted_address}</div>
              </div>
              <button
                onClick={() => removeStop(index)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Example 6: Map Integration
export function MapSearch({ 
  onLocationSelect 
}: { 
  onLocationSelect: (coords: { lat: number; lng: number }, place: any) => void 
}) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Map Search</h3>
      <PlacesSearch
        placeholder="Search to add marker on map..."
        onCoordinatesSelect={(coords, place) => {
          onLocationSelect(coords, place)
        }}
        showCategories={true}
        variant="minimal"
      />
    </div>
  )
}

// Example 7: Country-Specific Search
export function CountrySearch({ country }: { country: string }) {
  const countryNames: { [key: string]: string } = {
    'IL': 'Israel',
    'US': 'United States',
    'GB': 'United Kingdom',
    'FR': 'France',
    'DE': 'Germany'
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Search in {countryNames[country] || country}</h3>
      <PlacesSearch
        placeholder={`Search places in ${countryNames[country] || country}...`}
        countries={[country]}
        onPlaceSelect={(place) => {
          console.log('Selected place in', country, ':', place)
        }}
        showCategories={true}
      />
    </div>
  )
}

// Example 8: Compact Search for Sidebars
export function CompactSearch() {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">Quick Search</h3>
      <PlacesSearch
        placeholder="Quick search..."
        size="sm"
        variant="minimal"
        showCategories={false}
        onPlaceSelect={(place) => {
          console.log('Quick select:', place)
        }}
      />
    </div>
  )
}

// Integration Examples Component
export default function PlacesSearchExamples() {
  const [selectedExample, setSelectedExample] = useState('trip-planning')
  
  const examples = [
    { id: 'trip-planning', name: 'Trip Planning', component: TripPlanningSearch },
    { id: 'hotel-search', name: 'Hotel Search', component: () => <HotelSearch location={{ lat: 32.0853, lng: 34.7818 }} /> },
    { id: 'restaurant-finder', name: 'Restaurant Finder', component: () => <RestaurantFinder userLocation={{ lat: 32.0853, lng: 34.7818 }} /> },
    { id: 'address-picker', name: 'Address Picker', component: () => <AddressPicker onAddressSelect={(addr, coords) => console.log(addr, coords)} /> },
    { id: 'trip-builder', name: 'Trip Builder', component: TripBuilder },
    { id: 'map-search', name: 'Map Integration', component: () => <MapSearch onLocationSelect={(coords, place) => console.log(coords, place)} /> },
    { id: 'country-search', name: 'Country-Specific', component: () => <CountrySearch country="IL" /> },
    { id: 'compact-search', name: 'Compact Search', component: CompactSearch }
  ]

  const SelectedComponent = examples.find(ex => ex.id === selectedExample)?.component || TripPlanningSearch

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Places Search Integration Examples</h1>
        <p className="text-gray-600">
          Common usage patterns and integration examples for the PlacesSearch component.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Example Selector */}
        <div className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Examples</h3>
          <div className="space-y-1">
            {examples.map((example) => (
              <button
                key={example.id}
                onClick={() => setSelectedExample(example.id)}
                className={`
                  w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                  ${selectedExample === example.id
                    ? 'bg-blue-100 text-blue-800 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }
                `}
              >
                {example.name}
              </button>
            ))}
          </div>
        </div>

        {/* Example Display */}
        <div className="lg:col-span-3">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <SelectedComponent />
          </div>
        </div>
      </div>
    </div>
  )
}
