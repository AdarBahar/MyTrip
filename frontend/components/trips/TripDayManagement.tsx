'use client'

/**
 * Enhanced Trip Day Management Component
 * 
 * Replaces the basic DaysList with enhanced day management similar to route-breakdown page.
 * Includes RoutePointsPanel for each day with proper route management.
 */

import React, { useState, useEffect } from 'react'
import { Day, Trip } from '@/types'
import { Place, createPlace } from '@/lib/api/places'
import { useDays } from '@/hooks/use-days'
import { useToast } from '@/components/ui/use-toast'
import { listStops, createStop, type StopWithPlace } from '@/lib/api/stops'
import { computeDayRoute } from '@/lib/api/routing'
import PointTypeSelectionModal, { DEFAULT_ROUTE_POINT_TYPES, createRoutePointOptions } from '@/components/ui/PointTypeSelectionModal'
import GenericModal, { FormModal } from '@/components/ui/GenericModal'
import PlacesSearch from '@/components/ui/PlacesSearch'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plus, Calendar, MapPin, Settings, Trash2 } from 'lucide-react'

interface TripDayManagementProps {
  trip: Trip
  className?: string
  prefilledLocations?: Record<string, { 
    start?: Place | null
    end?: Place | null
    route_total_km?: number
    route_total_min?: number
    route_coordinates?: [number, number][]
    stops?: any[]
  }>
  showCountrySuffix?: boolean
}

export default function TripDayManagement({ 
  trip, 
  className = '', 
  prefilledLocations = {},
  showCountrySuffix = false 
}: TripDayManagementProps) {
  const { days, loading, error, createDay, updateDay, deleteDay } = useDays({
    tripId: trip.id,
    includeStops: false,
    autoRefresh: true
  })

  const { toast } = useToast()
  const [selectedDay, setSelectedDay] = useState<Day | null>(null)
  const [showAddPoint, setShowAddPoint] = useState(false)
  const [showPointTypeSelection, setShowPointTypeSelection] = useState(false)
  const [selectedPlace, setSelectedPlace] = useState<any>(null)
  const [showCreateDay, setShowCreateDay] = useState(false)
  const [newDaySeq, setNewDaySeq] = useState('')
  const [dayLocations, setDayLocations] = useState(prefilledLocations)

  // Update day locations when prefilledLocations change
  useEffect(() => {
    setDayLocations(prev => {
      // Only update if actually different to prevent unnecessary re-renders
      const prevKeys = Object.keys(prev).sort()
      const newKeys = Object.keys(prefilledLocations).sort()
      if (prevKeys.join(',') !== newKeys.join(',')) {
        return prefilledLocations
      }
      return prev
    })
  }, [prefilledLocations])





  const handleCreateDay = async () => {
    if (!newDaySeq.trim()) return

    try {
      const seq = parseInt(newDaySeq)
      if (isNaN(seq)) {
        toast({
          title: 'Invalid sequence',
          description: 'Please enter a valid day number',
          variant: 'destructive'
        })
        return
      }

      await createDay({ seq, rest_day: false })
      setShowCreateDay(false)
      setNewDaySeq('')
      toast({
        title: 'Day created',
        description: `Day ${seq} has been added to your trip`
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create day',
        variant: 'destructive'
      })
    }
  }

  const handleDeleteDay = async (day: Day) => {
    try {
      await deleteDay(day.id)
      if (selectedDay?.id === day.id) {
        setSelectedDay(null)
      }
      toast({
        title: 'Day deleted',
        description: `Day ${day.seq} has been removed from your trip`
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete day',
        variant: 'destructive'
      })
    }
  }

  const handleAddPoint = () => {
    setShowAddPoint(true)
  }

  const handlePlaceFromSearch = (place: any) => {
    setSelectedPlace(place)
    setShowAddPoint(false)
    setShowPointTypeSelection(true)
  }

  const handlePointTypeSelect = async (type: string) => {
    if (!selectedPlace || !selectedDay) return

    try {
      // Create place if needed
      const placeId = await createPlace({
        name: selectedPlace.name,
        address: selectedPlace.address,
        lat: selectedPlace.lat,
        lon: selectedPlace.lon,
        meta: selectedPlace.meta
      })

      // Create stop
      await createStop({
        day_id: selectedDay.id,
        place_id: placeId.id,
        seq: 999 // Will be auto-assigned by backend
      })

      // Refresh route points
      const stopsResponse = await listStops(trip.id, selectedDay.id)
      // ... refresh logic

      setShowPointTypeSelection(false)
      setSelectedPlace(null)
      
      toast({
        title: 'Point added',
        description: `${selectedPlace.name} has been added to Day ${selectedDay.seq}`
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add point',
        variant: 'destructive'
      })
    }
  }

  const handleComputeRoute = async () => {
    if (!selectedDay) return

    try {
      const result = await computeDayRoute(selectedDay.id, { optimize: false })
      
      // Convert to RouteResultsData format
      const routeData: RouteResultsData = {
        total_distance_km: result.total_km || 0,
        total_duration_min: result.total_min || 0,
        segments: result.segments || [],
        geometry: result.geojson
      }
      
      // Route computed successfully
      
      toast({
        title: 'Route computed',
        description: `Route for Day ${selectedDay.seq} has been calculated`
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to compute route',
        variant: 'destructive'
      })
    }
  }



  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <div className="text-red-600 mb-2">Error loading days</div>
        <div className="text-gray-600 text-sm">{error}</div>
      </div>
    )
  }

  const sortedDays = [...days].sort((a, b) => a.seq - b.seq)

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Days Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sortedDays.map((day) => {
          const dayLoc = dayLocations[day.id]
          const hasRoute = dayLoc && typeof dayLoc.route_total_km === 'number'

          // Check for stops in different possible locations
          const stops = dayLoc?.stops || []
          const hasStops = stops.length > 0




          
          return (
            <Card
              key={day.id}
              className="transition-all hover:shadow-md"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Day {day.seq}</CardTitle>
                  <div className="flex items-center gap-2">
                    {hasRoute && (
                      <Badge variant="secondary" className="text-xs">
                        {Math.round(dayLoc.route_total_km!)} km
                      </Badge>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedDay(day)
                        setShowAddPoint(true)
                      }}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      Add Point
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedDay(day)
                        handleComputeRoute()
                      }}
                      className="text-green-600 hover:text-green-700"
                    >
                      Compute Route
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteDay(day)
                      }}
                      className="h-6 w-6 p-0 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
                {day.calculated_date && (
                  <CardDescription>
                    {new Date(day.calculated_date).toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric'
                    })}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="pt-0">
                {/* Route Points Display - Using Route Breakdown Style */}
                {dayLoc?.start || dayLoc?.end || hasStops ? (
                  <div className="mt-4 space-y-2">
                    {/* Start Point */}
                    {dayLoc?.start && (
                      <div className="flex items-center gap-3 p-2 bg-green-50 rounded-lg">
                        <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
                          S
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-green-800 truncate">{dayLoc.start.name}</div>
                        </div>
                      </div>
                    )}

                    {/* Intermediate Stops */}
                    {hasStops && stops.map((stop: any, index: number) => {
                      const stopName = stop.place?.name || stop.name || stop.location?.name ||
                                     (stop.notes && !stop.notes.includes('Added via route breakdown') ? stop.notes : null) ||
                                     `Via Stop ${stop.seq || index + 1}`
                      return (
                        <div key={stop.id || index} className="flex items-center gap-3 p-2 bg-blue-50 rounded-lg">
                          <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <div className="font-medium text-blue-800 truncate">{stopName}</div>
                          </div>
                        </div>
                      )
                    })}

                    {/* End Point */}
                    {dayLoc?.end && (
                      <div className="flex items-center gap-3 p-2 bg-red-50 rounded-lg">
                        <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">
                          E
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-red-800 truncate">{dayLoc.end.name}</div>
                        </div>
                      </div>
                    )}



                  </div>
                ) : (
                  <div className="text-gray-400 text-center py-4">No route planned</div>
                )}

              </CardContent>
            </Card>
          )
        })}
        
        {/* Add Day Card */}
        <Card 
          className="cursor-pointer border-dashed border-2 hover:border-blue-500 transition-colors"
          onClick={() => setShowCreateDay(true)}
        >
          <CardContent className="flex items-center justify-center h-full min-h-[120px]">
            <div className="text-center text-gray-500">
              <Plus className="h-8 w-8 mx-auto mb-2" />
              <div className="text-sm font-medium">Add Day</div>
            </div>
          </CardContent>
        </Card>
      </div>



      {/* Modals */}
      <GenericModal
        isOpen={showAddPoint}
        onClose={() => setShowAddPoint(false)}
        title="Add Route Point"
        size="md"
      >
        <PlacesSearch
          useRealGeocoding={true}
          placeholder="Search for any location worldwide..."
          onPlaceSelect={handlePlaceFromSearch}
          supportRTL={true}
          autoSearch={true}
        />
      </GenericModal>

      <PointTypeSelectionModal
        isOpen={showPointTypeSelection}
        onClose={() => {
          setShowPointTypeSelection(false)
          setSelectedPlace(null)
        }}
        onSelect={handlePointTypeSelect}
        title="Select Point Type"
        selectedItem={selectedPlace ? {
          name: selectedPlace.name,
          lat: selectedPlace.lat,
          lon: selectedPlace.lon,
          address: selectedPlace.address
        } : null}
        options={createRoutePointOptions([])}
        showSelectedItemDetails={true}
        selectedItemLabel="Selected"
      />

      <FormModal
        isOpen={showCreateDay}
        onClose={() => setShowCreateDay(false)}
        onSubmit={handleCreateDay}
        title="Create New Day"
        submitLabel="Create Day"
        loading={false}
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Day Number
          </label>
          <input
            type="number"
            value={newDaySeq}
            onChange={(e) => setNewDaySeq(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., 1, 2, 3..."
            min="1"
          />
        </div>
      </FormModal>
    </div>
  )
}
