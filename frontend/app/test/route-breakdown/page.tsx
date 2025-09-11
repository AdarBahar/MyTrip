'use client'

/**
 * Route Breakdown Planning Tool - Clean Refactored Version
 */

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import { useTrips } from '@/hooks/use-trips'
import { useDays } from '@/hooks/use-days'
import { computeDayRouteBreakdown } from '@/lib/api/day-route-breakdown'
import { DayRouteBreakdownResponse } from '@/types/day-route-breakdown'
import PlacesSearch from '@/components/ui/PlacesSearch'
import { createTrip } from '@/lib/api/trips'
import { Trip, TripCreate } from '@/types/trip'
import { Day, DayCreate } from '@/types/day'
import { fetchWithAuth } from '@/lib/auth'
import { Plus, MapPin, X, Search } from 'lucide-react'

// Dynamic map import
const RouteBreakdownMap = dynamic(
  () => import('@/components/test/RouteBreakdownMap'),
  { 
    ssr: false,
    loading: () => (
      <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center text-gray-600">
          <div className="text-4xl mb-2">🗺️</div>
          <div>Loading map...</div>
        </div>
      </div>
    )
  }
)

// Simple route point interface
interface RoutePoint {
  id: string
  lat: number
  lon: number
  name: string
  type: 'start' | 'stop' | 'end'
}

export default function RouteBreakdownPage() {
  // Core state
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null)
  const [selectedDay, setSelectedDay] = useState<Day | null>(null)
  const [routePoints, setRoutePoints] = useState<RoutePoint[]>([])
  const [breakdown, setBreakdown] = useState<DayRouteBreakdownResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // UI state
  const [showSearch, setShowSearch] = useState(false)
  const [showCreateTrip, setShowCreateTrip] = useState(false)
  const [newTripName, setNewTripName] = useState('')
  const [newTripLocation, setNewTripLocation] = useState('')
  const [selectedPlace, setSelectedPlace] = useState<any>(null)
  const [showPointTypeSelection, setShowPointTypeSelection] = useState(false)

  // API hooks
  const { trips, loading: tripsLoading, error: tripsError, fetchTrips } = useTrips()
  const { days, loading: daysLoading, createDay } = useDays({ 
    tripId: selectedTrip?.id || '', 
    includeStops: false,
    autoRefresh: true 
  })

  // Create new trip
  const handleCreateTrip = async () => {
    if (!newTripName.trim() || !newTripLocation.trim()) return

    try {
      setLoading(true)
      const tripData: TripCreate = {
        title: newTripName.trim(),
        destination: newTripLocation.trim(),
        start_date: new Date().toISOString().split('T')[0],
        timezone: 'UTC',
        status: 'draft',
        is_published: false
      }

      const response = await createTrip(tripData)
      
      if (response.success && response.data) {
        await fetchTrips()
        setSelectedTrip(response.data.trip)
        setNewTripName('')
        setNewTripLocation('')
        setShowCreateTrip(false)
      } else {
        setError(response.error?.message || 'Failed to create trip')
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create trip')
    } finally {
      setLoading(false)
    }
  }

  // Handle trip selection
  const handleTripSelect = (trip: Trip) => {
    setSelectedTrip(trip)
    setSelectedDay(null)
    setRoutePoints([])
    setBreakdown(null)
    setError(null)
    console.log('Selected trip:', trip.title, 'ID:', trip.id)
  }

  // Load existing stops for a day
  const loadExistingStops = async (tripId: string, dayId: string) => {
    try {
      setLoading(true)
      const response = await fetchWithAuth(`/stops/${tripId}/days/${dayId}/stops?include_place=true`)

      if (!response.ok) {
        console.warn('Failed to load existing stops:', response.status)
        return []
      }

      const result = await response.json()
      const stops = result.stops || []

      console.log('Loaded existing stops:', stops)

      // Convert stops to route points
      const routePoints: RoutePoint[] = stops
        .filter((stop: any) => stop.place && stop.place.lat && stop.place.lon)
        .map((stop: any) => {
          const mappedType = stop.kind === 'start' ? 'start' : stop.kind === 'end' ? 'end' : 'stop'
          console.log(`Mapping stop ${stop.id}: kind="${stop.kind}" -> type="${mappedType}"`)

          return {
            id: stop.id,
            lat: stop.place.lat,
            lon: stop.place.lon,
            name: stop.place.name || 'Unknown location',
            type: mappedType
          }
        })
        .sort((a: any, b: any) => {
          // Sort by sequence: start first, then stops, then end
          const aStop = stops.find((s: any) => s.id === a.id)
          const bStop = stops.find((s: any) => s.id === b.id)
          return (aStop?.seq || 0) - (bStop?.seq || 0)
        })

      return routePoints
    } catch (error) {
      console.error('Error loading existing stops:', error)
      return []
    } finally {
      setLoading(false)
    }
  }

  // Handle day selection
  const handleDaySelect = async (day: Day) => {
    setSelectedDay(day)
    setBreakdown(null)
    setError(null)

    // Load existing stops for this day
    if (selectedTrip) {
      const existingStops = await loadExistingStops(selectedTrip.id, day.id)
      setRoutePoints(existingStops)
      console.log(`Loaded ${existingStops.length} existing stops for day:`, day.title || `Day ${day.seq}`)
    } else {
      setRoutePoints([])
    }
  }

  // Handle place selection from search
  const handlePlaceFromSearch = (place: any) => {
    setSelectedPlace(place)
    setShowPointTypeSelection(true)
  }

  // Add route point
  const handlePointTypeSelect = (type: 'start' | 'stop' | 'end') => {
    if (!selectedPlace) return

    const newPoint: RoutePoint = {
      id: `${type}_${Date.now()}`,
      lat: selectedPlace.center.lat,
      lon: selectedPlace.center.lng,
      name: selectedPlace.name,
      type
    }

    setRoutePoints(prev => {
      const filtered = prev.filter(p => {
        // Remove existing start/end when adding new one
        if (type === 'start') return p.type !== 'start'
        if (type === 'end') return p.type !== 'end'
        return true
      })

      if (type === 'start') {
        return [newPoint, ...filtered]
      } else if (type === 'end') {
        return [...filtered, newPoint]
      } else {
        return [...filtered, newPoint]
      }
    })

    setShowSearch(false)
    setShowPointTypeSelection(false)
    setSelectedPlace(null)
  }

  // Remove route point
  const removePoint = (pointId: string) => {
    setRoutePoints(prev => prev.filter(p => p.id !== pointId))
  }

  // Compute route breakdown
  const handleComputeBreakdown = async () => {
    if (!selectedTrip || !selectedDay || routePoints.length < 2) {
      setError('Please select a trip, day, and add at least 2 route points')
      return
    }

    const startPoint = routePoints.find(p => p.type === 'start')
    const endPoint = routePoints.find(p => p.type === 'end')
    const stopPoints = routePoints.filter(p => p.type === 'stop')

    if (!startPoint || !endPoint) {
      setError('Please add both start and end points')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const result = await computeDayRouteBreakdown({
        trip_id: selectedTrip.id,
        day_id: selectedDay.id,
        start: { lat: startPoint.lat, lon: startPoint.lon, name: startPoint.name },
        stops: stopPoints.map(p => ({ lat: p.lat, lon: p.lon, name: p.name })),
        end: { lat: endPoint.lat, lon: endPoint.lon, name: endPoint.name },
        profile: 'car'
      })

      setBreakdown(result)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to compute route breakdown')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Route Planning & Breakdown</h1>
          <p className="text-gray-600 mt-2">
            Plan and analyze routes with comprehensive trip management
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Left Panel - Trip & Day Management */}
          <div className="xl:col-span-1 space-y-6">
            
            {/* Trip Selection */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Select Trip</h2>
                <button
                  onClick={() => setShowCreateTrip(true)}
                  className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4" />
                  New Trip
                </button>
              </div>

              {tripsLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-2">Loading trips...</p>
                </div>
              ) : trips.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <MapPin className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p>No trips available</p>
                  <p className="text-sm">Create your first trip to get started</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {trips.map((trip) => (
                    <div
                      key={trip.id}
                      onClick={() => handleTripSelect(trip)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedTrip?.id === trip.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="font-medium text-gray-900">{trip.title}</div>
                      <div className="text-sm text-gray-600">{trip.description || 'No description'}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {trip.start_date} - {trip.end_date}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Day Selection */}
            {selectedTrip && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Select Day</h2>
                </div>

                {daysLoading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600 mx-auto"></div>
                    <p className="text-gray-600 mt-2">Loading days...</p>
                  </div>
                ) : days.length === 0 ? (
                  <div className="text-center py-6 text-gray-500">
                    <p>No days available for this trip</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {days.map((day, index) => (
                      <div
                        key={day.id}
                        onClick={() => handleDaySelect(day)}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedDay?.id === day.id
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="font-medium text-gray-900">
                          Day {index + 1}: {day.title || 'Untitled Day'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {day.date || 'No date set'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Panel - Route Planning */}
          <div className="xl:col-span-2 space-y-6">
            
            {/* Route Points */}
            {selectedTrip && selectedDay && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Route Points</h2>
                  <button
                    onClick={() => setShowSearch(true)}
                    className="flex items-center gap-1 px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    <Search className="h-4 w-4" />
                    Add Point
                  </button>
                </div>

                {loading ? (
                  <div className="text-center py-6">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600 mx-auto"></div>
                    <p className="text-gray-600 mt-2">Loading existing route points...</p>
                  </div>
                ) : routePoints.length === 0 ? (
                  <div className="text-center py-6 text-gray-500">
                    <MapPin className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                    <p>No route points added yet</p>
                    <p className="text-sm">Click "Add Point" to start building your route</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {routePoints
                      .sort((a, b) => {
                        const order = { start: 0, stop: 1, end: 2 }
                        return order[a.type] - order[b.type]
                      })
                      .map((point, index) => (
                        <div
                          key={point.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border-l-4"
                          style={{
                            borderLeftColor:
                              point.type === 'start' ? '#10b981' :
                              point.type === 'end' ? '#ef4444' : '#3b82f6'
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2">
                              <div className={`w-4 h-4 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                                point.type === 'start' ? 'bg-green-500' :
                                point.type === 'end' ? 'bg-red-500' : 'bg-blue-500'
                              }`}>
                                {point.type === 'start' ? 'S' : point.type === 'end' ? 'E' : index}
                              </div>
                              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                                {point.type}
                              </div>
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">
                                {point.name}
                              </div>
                              <div className="text-xs text-gray-600">
                                {point.lat.toFixed(6)}, {point.lon.toFixed(6)}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => removePoint(point.id)}
                            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                            title="Remove point"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                  </div>
                )}

                {routePoints.length >= 2 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <button
                      onClick={handleComputeBreakdown}
                      disabled={loading}
                      className="w-full py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                    >
                      {loading ? 'Computing...' : 'Compute Route Breakdown'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Route Breakdown Results */}
            {breakdown && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Route Breakdown</h2>
                
                {/* Map */}
                <div className="mb-6">
                  <RouteBreakdownMap
                    breakdown={breakdown}
                    center={breakdown?.start ? [breakdown.start.lat, breakdown.start.lon] : undefined}
                    zoom={12}
                    height={400}
                  />
                </div>

                {/* Summary */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {(breakdown?.total_distance_km || 0).toFixed(1)} km
                    </div>
                    <div className="text-sm text-blue-800">Total Distance</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(breakdown?.total_duration_min || 0)} min
                    </div>
                    <div className="text-sm text-green-800">Total Duration</div>
                  </div>
                </div>

                {/* Segments */}
                {breakdown?.segments && breakdown.segments.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Route Segments</h3>
                    <div className="space-y-2">
                      {breakdown.segments.map((segment, index) => (
                        <div key={index} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="font-medium">
                                {segment?.from_point?.name || 'Unknown'} → {segment?.to_point?.name || 'Unknown'}
                              </div>
                              <div className="text-sm text-gray-600">
                                {(segment?.distance_km || 0).toFixed(1)} km • {Math.round(segment?.duration_min || 0)} min
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Search Modal */}
      {showSearch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Add Route Point</h3>
              <button
                onClick={() => setShowSearch(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6">
              <PlacesSearch
                useRealGeocoding={true}
                placeholder="Search for any location worldwide..."
                onPlaceSelect={handlePlaceFromSearch}
                supportRTL={true}
                autoSearch={true}
              />
            </div>
          </div>
        </div>
      )}

      {/* Point Type Selection Modal */}
      {showPointTypeSelection && selectedPlace && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Select Point Type</h3>
              <button
                onClick={() => {
                  setShowPointTypeSelection(false)
                  setSelectedPlace(null)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6">
              <p className="text-sm text-gray-600 mb-4">
                Selected: <strong>{selectedPlace.name}</strong>
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => handlePointTypeSelect('start')}
                  className="w-full p-3 text-left border border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <div>
                      <div className="font-medium">Start Point</div>
                      <div className="text-sm text-gray-600">Beginning of your journey</div>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handlePointTypeSelect('stop')}
                  className="w-full p-3 text-left border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <div>
                      <div className="font-medium">Stop Point</div>
                      <div className="text-sm text-gray-600">Intermediate destination</div>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handlePointTypeSelect('end')}
                  className="w-full p-3 text-left border border-gray-200 rounded-lg hover:border-red-500 hover:bg-red-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div>
                      <div className="font-medium">End Point</div>
                      <div className="text-sm text-gray-600">Final destination</div>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Trip Modal */}
      {showCreateTrip && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Create New Trip</h3>
              <button
                onClick={() => setShowCreateTrip(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trip Name
                  </label>
                  <input
                    type="text"
                    value={newTripName}
                    onChange={(e) => setNewTripName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., European Adventure"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Destination
                  </label>
                  <input
                    type="text"
                    value={newTripLocation}
                    onChange={(e) => setNewTripLocation(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Europe"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setShowCreateTrip(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateTrip}
                    disabled={!newTripName.trim() || !newTripLocation.trim() || loading}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Trip'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
