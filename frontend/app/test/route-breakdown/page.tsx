'use client'

/**
 * Route Breakdown Planning Tool - Clean Refactored Version
 */

import React, { useState, useEffect } from 'react'
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
import { createStop, getNextSequenceNumber, deleteStop, updateStop, listStops, type StopWithPlace } from '@/lib/api/stops'
import { createPlace, type Place } from '@/lib/api/places'
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
  fixed?: boolean
}

export default function RouteBreakdownPage() {
  // Core state
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null)
  const [selectedDay, setSelectedDay] = useState<Day | null>(null)
  const [routePoints, setRoutePoints] = useState<RoutePoint[]>([])
  const [breakdown, setBreakdown] = useState<DayRouteBreakdownResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string>('')

  // UI state
  const [showSearch, setShowSearch] = useState(false)
  const [showCreateTrip, setShowCreateTrip] = useState(false)
  const [newTripName, setNewTripName] = useState('')
  const [newTripLocation, setNewTripLocation] = useState('')
  const [selectedPlace, setSelectedPlace] = useState<any>(null)
  const [showPointTypeSelection, setShowPointTypeSelection] = useState(false)

  // Set up authentication for testing
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      // Set a fake token for testing
      localStorage.setItem('auth_token', 'fake_token_01K365YF7N0QVENA3HQZKGH7XA')
      localStorage.setItem('user_data', JSON.stringify({
        id: '01K365YF7N0QVENA3HQZKGH7XA',
        email: 'test@example.com',
        display_name: 'Test User'
      }))
      console.log('Set fake auth token for testing')
    }
  }, [])

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

  // Debug function to test API call
  const debugApiCall = async () => {
    if (!selectedTrip || !selectedDay) {
      setDebugInfo('No trip or day selected')
      return
    }

    try {
      setDebugInfo('Making API call...')
      const result = await listStops(selectedTrip.id, selectedDay.id, { includePlaces: true })
      setDebugInfo(`API Success: ${JSON.stringify(result, null, 2)}`)
      console.log('Debug API result:', result)

      // Also test the loadExistingStops function
      console.log('Testing loadExistingStops...')
      const routePoints = await loadExistingStops(selectedTrip.id, selectedDay.id)
      console.log('loadExistingStops result:', routePoints)

    } catch (error) {
      setDebugInfo(`API Error: ${error}`)
      console.error('Debug API error:', error)
    }
  }

  // Debug function to test route optimization directly
  const debugRouteOptimization = async () => {
    try {
      const testRequest = {
        trip_id: "01K4HZYAQ99EXAB30ZCGPF34FC",
        day_id: "01K4J0CYB3YSGWDZB9N92V3ZQ4",
        start: {
          lat: 32.1878296,
          lon: 34.9354013,
          name: "Start Point"
        },
        stops: [
          {
            lat: 32.0944,
            lon: 34.7806,
            name: "Stop 1"
          },
          {
            lat: 32.0892,
            lon: 34.7751,
            name: "Stop 2"
          }
        ],
        end: {
          lat: 32.067444,
          lon: 34.7936703,
          name: "End Point"
        },
        profile: "car",
        optimize: true,
        fixed_stop_indices: []
      }

      console.log('Testing route optimization with known good data:', testRequest)
      const result = await computeDayRouteBreakdown(testRequest)
      console.log('Route optimization result:', result)
      setDebugInfo(`Route optimization success: ${JSON.stringify(result.optimization_savings, null, 2)}`)

    } catch (error) {
      console.error('Route optimization error:', error)
      setDebugInfo(`Route optimization error: ${error}`)
    }
  }

  // Note: Global debug assignment moved to after function declarations

  // Helper function to fix missing place data by fetching places separately
  const _fixMissingPlaceData = async (routePoints: RoutePoint[], tripId: string, dayId: string): Promise<RoutePoint[]> => {
    const pointsNeedingFix = routePoints.filter(p => !p.lat || !p.lon || isNaN(p.lat) || isNaN(p.lon))

    if (pointsNeedingFix.length === 0) {
      return routePoints
    }

    console.log(`Fixing ${pointsNeedingFix.length} route points with missing place data`)

    // Get the original stops to find place_ids
    const stopsResponse = await listStops(tripId, dayId, { includePlaces: false })
    const stops = stopsResponse.stops

    const fixedPoints = await Promise.all(routePoints.map(async (point) => {
      if (point.lat && point.lon && !isNaN(point.lat) && !isNaN(point.lon)) {
        return point // Already has valid coordinates
      }

      // Find the corresponding stop
      const stop = stops.find(s => s.id === point.id)
      if (!stop || !stop.place_id) {
        console.warn(`Cannot fix point ${point.id}: no stop or place_id found`)
        return point
      }

      try {
        // Fetch place data directly
        const response = await fetchWithAuth(`/places/${stop.place_id}`)
        if (!response.ok) {
          console.warn(`Failed to fetch place ${stop.place_id}:`, response.status)
          return point
        }

        const place = await response.json()
        console.log(`Fixed place data for ${point.id}:`, place.name)

        return {
          ...point,
          lat: place.lat,
          lon: place.lon,
          name: place.name || point.name
        }
      } catch (error) {
        console.warn(`Error fetching place ${stop.place_id}:`, error)
        return point
      }
    }))

    return fixedPoints
  }

  // Load existing stops for a day
  const loadExistingStops = async (tripId: string, dayId: string) => {
    try {
      setLoading(true)

      // Use the proper API function
      const result = await listStops(tripId, dayId, { includePlaces: true })
      const stops = result.stops as StopWithPlace[]

      console.log('Loaded existing stops:', stops)
      console.log('Raw API result:', result)
      console.log('Number of stops:', stops?.length || 0)

      if (stops && stops.length > 0) {
        stops.forEach((stop, index) => {
          console.log(`Stop ${index}:`, {
            id: stop.id,
            kind: stop.kind,
            seq: stop.seq,
            place_id: stop.place_id,
            place: stop.place,
            hasPlace: !!stop.place,
            placeName: stop.place?.name,
            placeLat: stop.place?.lat,
            placeLon: stop.place?.lon,
            placeKeys: stop.place ? Object.keys(stop.place) : 'no place',
            fullStop: stop
          })
        })
      } else {
        console.log('No stops found or stops array is empty')
      }

      // Convert stops to route points
      console.log('Processing stops for route points:', stops)

      console.log('About to filter stops. Total stops:', stops.length)

      const filteredStops = stops.filter((stop: StopWithPlace) => {
        // Check if place exists and has valid coordinates
        const hasPlace = stop.place && typeof stop.place === 'object'
        const hasCoords = hasPlace &&
          typeof stop.place.lat === 'number' &&
          typeof stop.place.lon === 'number' &&
          !isNaN(stop.place.lat) &&
          !isNaN(stop.place.lon)

        console.log(`Filtering stop ${stop.id}: hasPlace=${hasPlace}, hasCoords=${hasCoords}`, {
          place: stop.place,
          lat: stop.place?.lat,
          lon: stop.place?.lon,
          latType: typeof stop.place?.lat,
          lonType: typeof stop.place?.lon
        })

        return hasPlace && hasCoords
      })

      console.log('Filtered stops count:', filteredStops.length)

      const routePoints: RoutePoint[] = filteredStops
        .map((stop: StopWithPlace) => {
          const mappedType = stop.kind === 'start' ? 'start' : stop.kind === 'end' ? 'end' : 'stop'
          console.log(`Mapping stop ${stop.id}: kind="${stop.kind}" -> type="${mappedType}"`)

          // Add extra safety checks for place data
          const place = stop.place
          if (!place) {
            console.error(`Stop ${stop.id} has no place data:`, stop)
            throw new Error(`Stop ${stop.id} missing place data`)
          }

          // Handle potential type conversion issues
          let lat: number
          let lon: number

          try {
            lat = typeof place.lat === 'number' ? place.lat : parseFloat(String(place.lat))
            lon = typeof place.lon === 'number' ? place.lon : parseFloat(String(place.lon))
          } catch (e) {
            console.error(`Stop ${stop.id} coordinate parsing failed:`, { place, error: e })
            throw new Error(`Stop ${stop.id} coordinate parsing failed`)
          }

          if (isNaN(lat) || isNaN(lon)) {
            console.error(`Stop ${stop.id} has invalid coordinates after parsing:`, { lat, lon, place })
            throw new Error(`Stop ${stop.id} has invalid coordinates: lat=${lat}, lon=${lon}`)
          }

          const name = place.name || 'Unknown location'

          return {
            id: stop.id,
            lat: lat,
            lon: lon,
            name: name,
            type: mappedType,
            fixed: stop.fixed || false
          }
        })
        .sort((a: RoutePoint, b: RoutePoint) => {
          // Sort by sequence: start first, then stops, then end
          const aStop = stops.find((s: StopWithPlace) => s.id === a.id)
          const bStop = stops.find((s: StopWithPlace) => s.id === b.id)
          return (aStop?.seq || 0) - (bStop?.seq || 0)
        })

      console.log('Final route points:', routePoints)
      console.log('Route points count:', routePoints.length)

      setLoading(false)
      // Check if any route points are missing coordinates and try to fix them
      const fixedRoutePoints = await _fixMissingPlaceData(routePoints, tripId, dayId)

      setLoading(false)
      return fixedRoutePoints
    } catch (error) {
      console.error('Error loading existing stops:', error)
      setLoading(false)
      return []
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

  // Add route point and persist to database
  const handlePointTypeSelect = async (type: 'start' | 'stop' | 'end') => {
    if (!selectedPlace || !selectedTrip || !selectedDay) return

    try {
      setLoading(true)
      setError(null)

      // First, create the place in the database if it doesn't exist
      let place: Place
      try {
        console.log('Creating place with data:', {
          name: selectedPlace.name,
          address: selectedPlace.address || selectedPlace.name,
          lat: selectedPlace.center.lat,
          lon: selectedPlace.center.lng,
          meta: {
            source: 'route-breakdown',
            original_id: selectedPlace.id
          }
        })

        place = await createPlace({
          name: selectedPlace.name,
          address: selectedPlace.address || selectedPlace.name,
          lat: selectedPlace.center.lat,
          lon: selectedPlace.center.lng,
          meta: {
            source: 'route-breakdown',
            original_id: selectedPlace.id
          }
        })
        console.log('Created place in database:', place.id)
      } catch (error) {
        // If place creation fails (e.g., duplicate), try to use the original ID
        console.warn('Place creation failed, using original ID:', error)
        place = {
          id: selectedPlace.id,
          name: selectedPlace.name,
          address: selectedPlace.address || selectedPlace.name,
          lat: selectedPlace.center.lat,
          lon: selectedPlace.center.lng
        } as Place
      }

      // Get current stops to determine sequence number
      const currentStopsResponse = await listStops(selectedTrip.id, selectedDay.id, { includePlaces: true })
      const currentStops = currentStopsResponse.stops as StopWithPlace[]

      // Remove existing start/end stop if adding new one and track deleted IDs
      const deletedStopIds: string[] = []

      if (type === 'start') {
        const existingStart = currentStops.find(s => s.kind === 'start')
        if (existingStart) {
          await deleteStop(selectedTrip.id, selectedDay.id, existingStart.id)
          deletedStopIds.push(existingStart.id)
          console.log('Removed existing start stop:', existingStart.id)
        }
      } else if (type === 'end') {
        const existingEnd = currentStops.find(s => s.kind === 'end')
        if (existingEnd) {
          await deleteStop(selectedTrip.id, selectedDay.id, existingEnd.id)
          deletedStopIds.push(existingEnd.id)
          console.log('Removed existing end stop:', existingEnd.id)
        }
      }

      // Determine sequence number based on remaining stops (excluding deleted ones)
      const remainingStops = currentStops.filter(s => !deletedStopIds.includes(s.id))
      const maxSeq = Math.max(...remainingStops.map(s => s.seq || 0), 0)

      console.log('Remaining stops for sequence calculation:', remainingStops.map(s => ({
        id: s.id,
        seq: s.seq,
        kind: s.kind
      })))
      console.log(`Max sequence from remaining stops: ${maxSeq}`)
      let seq: number

      if (type === 'start') {
        // START is always sequence 1
        seq = 1
      } else if (type === 'end') {
        // END should be the last stop, so use max + 1
        seq = maxSeq + 1
      } else {
        // VIA stops go in the middle, use next available
        seq = maxSeq + 1
      }

      // Create the stop in the database
      const stopKind = type === 'stop' ? 'VIA' : type.toUpperCase()

      // Database constraint: START and END stops must be fixed
      const shouldBeFixed = type === 'start' || type === 'end'

      console.log(`Creating ${type} stop with seq=${seq} (maxSeq was ${maxSeq}, shouldBeFixed=${shouldBeFixed})`)

      const stopData = {
        place_id: place.id,
        seq: seq,
        kind: stopKind as 'START' | 'VIA' | 'END',
        fixed: shouldBeFixed,
        notes: `Added via route breakdown on ${new Date().toLocaleDateString()}`,
        stop_type: 'OTHER',
        priority: 3
      }

      console.log('Creating stop with data:', stopData)

      const newStop = await createStop(selectedTrip.id, selectedDay.id, stopData)

      console.log('Created stop in database:', newStop.id, 'type:', stopKind, 'seq:', seq)

      // Reload existing stops to update the UI
      const updatedPoints = await loadExistingStops(selectedTrip.id, selectedDay.id)
      setRoutePoints(updatedPoints)

      setShowSearch(false)
      setShowPointTypeSelection(false)
      setSelectedPlace(null)

      // Show success feedback
      console.log(`✅ Successfully added ${stopKind} stop: ${place.name}`)

    } catch (error) {
      console.error('Error adding route point:', error)
      setError(error instanceof Error ? error.message : 'Failed to add route point')
    } finally {
      setLoading(false)
    }
  }

  // Remove route point and delete from database
  const removePoint = async (pointId: string) => {
    if (!selectedTrip || !selectedDay) return

    try {
      setLoading(true)
      setError(null)

      // Delete from database
      await deleteStop(selectedTrip.id, selectedDay.id, pointId)
      console.log('Deleted stop from database:', pointId)

      // Reload existing stops to update the UI
      const updatedPoints = await loadExistingStops(selectedTrip.id, selectedDay.id)
      setRoutePoints(updatedPoints)

      console.log(`✅ Successfully removed stop: ${pointId}`)

    } catch (error) {
      console.error('Error removing route point:', error)
      setError(error instanceof Error ? error.message : 'Failed to remove route point')
    } finally {
      setLoading(false)
    }
  }

  // Toggle fixed status of a stop
  const toggleFixed = async (pointId: string, currentFixed: boolean) => {
    if (!selectedTrip || !selectedDay) return

    try {
      setLoading(true)
      setError(null)

      // Update in database
      await updateStop(selectedTrip.id, selectedDay.id, pointId, {
        fixed: !currentFixed
      })
      console.log('Updated stop fixed status:', pointId, 'fixed:', !currentFixed)

      // Reload existing stops to update the UI
      const updatedPoints = await loadExistingStops(selectedTrip.id, selectedDay.id)
      setRoutePoints(updatedPoints)

      console.log(`✅ Successfully updated stop fixed status: ${pointId} -> fixed: ${!currentFixed}`)

    } catch (error) {
      console.error('Error updating stop fixed status:', error)
      setError(error instanceof Error ? error.message : 'Failed to update stop')
    } finally {
      setLoading(false)
    }
  }

  // Compute route breakdown
  const handleComputeBreakdown = async (optimize: boolean = false) => {
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

    // Check for missing coordinates (place data not loaded properly)
    const allPoints = [startPoint, ...stopPoints, endPoint]
    const invalidPoints = allPoints.filter(p => {
      const hasValidLat = typeof p.lat === 'number' && !isNaN(p.lat) && p.lat !== 0
      const hasValidLon = typeof p.lon === 'number' && !isNaN(p.lon) && p.lon !== 0
      return !hasValidLat || !hasValidLon
    })

    if (invalidPoints.length > 0) {
      console.error('Invalid route points detected:', invalidPoints.map(p => ({
        id: p.id,
        name: p.name,
        lat: p.lat,
        lon: p.lon,
        latType: typeof p.lat,
        lonType: typeof p.lon,
        latValid: typeof p.lat === 'number' && !isNaN(p.lat) && p.lat !== 0,
        lonValid: typeof p.lon === 'number' && !isNaN(p.lon) && p.lon !== 0
      })))
      setError(`Some route points are missing coordinates. Please refresh the page and try again. Invalid points: ${invalidPoints.map(p => p.name || 'Unknown').join(', ')}`)
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Build fixed stop indices for optimization
      const fixedStopIndices = optimize
        ? stopPoints
            .map((p, index) => p.fixed ? index : -1)
            .filter(index => index !== -1)
        : undefined

      const requestData = {
        trip_id: selectedTrip.id,
        day_id: selectedDay.id,
        start: { lat: startPoint.lat, lon: startPoint.lon, name: startPoint.name },
        stops: stopPoints.map(p => ({ lat: p.lat, lon: p.lon, name: p.name })),
        end: { lat: endPoint.lat, lon: endPoint.lon, name: endPoint.name },
        profile: 'car',
        optimize: optimize,
        fixed_stop_indices: fixedStopIndices
      }

      console.log('Sending route optimization request:', JSON.stringify(requestData, null, 2))
      console.log('Route points summary:', {
        start: `${startPoint.name} (${startPoint.lat}, ${startPoint.lon})`,
        stops: stopPoints.map(p => `${p.name} (${p.lat}, ${p.lon})`),
        end: `${endPoint.name} (${endPoint.lat}, ${endPoint.lon})`,
        optimize,
        fixedStopIndices
      })

      const result = await computeDayRouteBreakdown(requestData)

      setBreakdown(result)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to compute route breakdown')
    } finally {
      setLoading(false)
    }
  }

  // Make functions available globally for debugging (after all functions are declared)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).debugRouteBreakdown = {
        debugApiCall,
        debugRouteOptimization,
        loadExistingStops,
        listStops,
        selectedTrip,
        selectedDay,
        computeDayRouteBreakdown
      }
    }
  }, [selectedTrip, selectedDay]) // Update when trip/day changes

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

        {/* Debug Info Display */}
        {debugInfo && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Debug Info:</h4>
            <pre className="text-xs text-blue-800 whitespace-pre-wrap overflow-auto max-h-40">
              {debugInfo}
            </pre>
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

                  {selectedTrip && selectedDay && (
                    <button
                      onClick={debugApiCall}
                      className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700"
                    >
                      🐛 Debug API
                    </button>
                  )}
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
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">Route Points ({routePoints.length})</h4>
                      <div className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
                        💾 Auto-saved to database
                      </div>
                    </div>
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
                          <div className="flex items-center gap-3 flex-1">
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
                              {point.fixed && (
                                <div className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full font-medium">
                                  FIXED
                                </div>
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="font-medium text-gray-900">
                                {point.name}
                              </div>
                              <div className="text-xs text-gray-600">
                                {point.lat.toFixed(6)}, {point.lon.toFixed(6)}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {point.type === 'stop' && (
                              <button
                                onClick={() => toggleFixed(point.id, point.fixed || false)}
                                className={`px-2 py-1 text-xs rounded transition-colors ${
                                  point.fixed
                                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                                title={point.fixed ? 'Unfix stop (allow optimization)' : 'Fix stop (prevent optimization)'}
                              >
                                {point.fixed ? '🔒' : '🔓'}
                              </button>
                            )}
                            <button
                              onClick={() => removePoint(point.id)}
                              className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                              title="Remove point"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                )}

                {routePoints.length >= 2 && (
                  <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                    <button
                      onClick={() => handleComputeBreakdown(false)}
                      disabled={loading}
                      className="w-full py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                    >
                      {loading ? 'Computing...' : 'Compute Route Breakdown'}
                    </button>

                    {routePoints.filter(p => p.type === 'stop').length > 1 && (
                      <button
                        onClick={() => handleComputeBreakdown(true)}
                        disabled={loading}
                        className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <span>🚀</span>
                        {loading ? 'Optimizing...' : 'Optimize & Compute Route'}
                      </button>
                    )}

                    {routePoints.filter(p => p.type === 'stop').length <= 1 && (
                      <p className="text-sm text-gray-500 text-center">
                        Add 2+ stops to enable route optimization
                      </p>
                    )}
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

                {/* Optimization Results */}
                {breakdown?.optimization_savings && (
                  <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">🚀</span>
                      <h3 className="font-semibold text-yellow-800">Route Optimization Results</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="font-medium text-yellow-800">Distance Saved</div>
                        <div className="text-yellow-700">
                          {breakdown.optimization_savings.distance_km_saved.toFixed(2)} km
                          ({breakdown.optimization_savings.distance_improvement_percent.toFixed(1)}% improvement)
                        </div>
                      </div>
                      <div>
                        <div className="font-medium text-yellow-800">Time Saved</div>
                        <div className="text-yellow-700">
                          {Math.round(breakdown.optimization_savings.duration_min_saved)} min
                          ({breakdown.optimization_savings.duration_improvement_percent.toFixed(1)}% improvement)
                        </div>
                      </div>
                    </div>
                  </div>
                )}

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
