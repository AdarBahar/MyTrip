'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, MapPin, Calendar, Users, Settings, Share2, Plus } from 'lucide-react'
import { fetchWithAuth } from '@/lib/auth'
import { MinimalDebugToggle } from '@/components/minimal-debug'
import { TripDateActions } from '@/components/trips/trip-date-actions'
import { DaysList } from '@/components/days'
import TripDayManagement from '@/components/trips/TripDayManagement'
import GenericModal from '@/components/ui/GenericModal'
import { Trip, listTripsEnhanced } from '@/lib/api/trips'
import { getApiBase } from '@/lib/api/base'
import { getDaysSummary, DayLocationsSummary } from '@/lib/api/days'
import { getBulkDayActiveSummaries } from '@/lib/api/routing'
import { listStops } from '@/lib/api/stops'
import { MapPreview } from '@/components/places'
import TripRouteMap from '@/components/trips/TripRouteMap'
import type { Day } from '@/types'
import { getUserSettings, updateUserSettings } from '@/lib/api/settings'
import { checkHealth } from '@/lib/api/health'
import { useToast } from '@/components/ui/use-toast'
import ManageDayRoutesDialog from '@/components/days/ManageDayRoutesDialog'

// Reusable state components
const LoadingState = ({ message }: { message: string }) => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">{message}</p>
    </div>
  </div>
)

const ErrorState = ({
  title,
  message,
  actionLabel,
  actionHref
}: {
  title: string
  message: string
  actionLabel: string
  actionHref: string
}) => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">{title}</h1>
      <p className="text-gray-600 mb-6">{message}</p>
      <Button asChild>
        <Link href={actionHref}>{actionLabel}</Link>
      </Button>
    </div>
  </div>
)

// Helper function to convert trip data to TripRouteMap format (moved outside component)
function convertToTripRouteData(summaryDays: any[], dayLocations: any, dayColors: string[]) {
  if (!summaryDays || !Array.isArray(summaryDays) || !dayLocations) {
    return []
  }

  return summaryDays
    .sort((a, b) => a.seq - b.seq)
    .map((day, idx) => {
      const loc = dayLocations[day.id]
      const coords = loc?.route_coordinates as [number, number][] | undefined



      if (!coords || !coords.length) {
        return null
      }

      // Create comprehensive stops array
      const stops = []

      // Strategy 1: Use explicit start/stops/end if available
      if (loc.start || loc.end || (loc.stops && loc.stops.length > 0)) {
        // Add start point
        if (loc.start) {
          stops.push({
            lat: loc.start.lat,
            lon: loc.start.lon,
            name: loc.start.name || `Day ${day.seq} Start`,
            type: 'start'
          })
        }

        // Add intermediate stops - handle multiple data structures
        if (loc.stops && Array.isArray(loc.stops) && loc.stops.length > 0) {


          loc.stops.forEach((stop: any, stopIdx: number) => {
            // Handle different stop data structures
            let stopLat, stopLon, stopName

            // Try different data structures
            if (stop.place) {
              // Stop with place object
              stopLat = stop.place.lat
              stopLon = stop.place.lon
              stopName = stop.place.name
            } else if (stop.lat && stop.lon) {
              // Direct lat/lon on stop
              stopLat = stop.lat
              stopLon = stop.lon
              stopName = stop.name
            } else if (stop.location) {
              // Stop with location object
              stopLat = stop.location.lat
              stopLon = stop.location.lon
              stopName = stop.location.name
            }

            // Fallback name
            if (!stopName) {
              stopName = `Day ${day.seq} Stop ${stopIdx + 1}`
            }



            if (stopLat && stopLon) {
              stops.push({
                lat: stopLat,
                lon: stopLon,
                name: stopName,
                type: 'stop'
              })
            } else {

            }
          })
        } else {

        }

        // Add end point
        if (loc.end) {
          stops.push({
            lat: loc.end.lat,
            lon: loc.end.lon,
            name: loc.end.name || `Day ${day.seq} End`,
            type: 'end'
          })
        }
      }

      // Strategy 2: If no explicit points, create from route coordinates
      if (stops.length <= 2 && coords.length >= 2) { // Changed condition to include cases with only start/end


        const startCoord = coords[0]
        const endCoord = coords[coords.length - 1]

        // Only add start if not already present
        if (!stops.some(s => s.type === 'start')) {
          stops.push({
            lat: startCoord[1],
            lon: startCoord[0],
            name: `Day ${day.seq} Start`,
            type: 'start'
          })
        }

        // Add intermediate points if route is long enough
        if (coords.length > 20) {
          // Calculate indices for intermediate points
          const indices = [
            Math.floor(coords.length / 4),      // quarter
            Math.floor(coords.length / 2),      // mid
            Math.floor((coords.length * 3) / 4) // three-quarter
          ]

          indices.forEach((index, i) => {
            const coord = coords[index]
            stops.push({
              lat: coord[1],
              lon: coord[0],
              name: `Day ${day.seq} Point ${i + 1}`,
              type: 'stop'
            })
          })
        } else if (coords.length > 10) {
          const midIndex = Math.floor(coords.length / 2)
          const midCoord = coords[midIndex]
          stops.push({
            lat: midCoord[1],
            lon: midCoord[0],
            name: `Day ${day.seq} Midpoint`,
            type: 'stop'
          })
        }

        // Only add end if not already present and different from start
        if (!stops.some(s => s.type === 'end') &&
            (startCoord[0] !== endCoord[0] || startCoord[1] !== endCoord[1])) {
          stops.push({
            lat: endCoord[1],
            lon: endCoord[0],
            name: `Day ${day.seq} End`,
            type: 'end'
          })
        }
      }

      // Strategy 3: Ensure we always have at least start and end
      if (stops.length === 0) {
        const startCoord = coords[0]
        const endCoord = coords[coords.length - 1]

        stops.push({
          lat: startCoord[1],
          lon: startCoord[0],
          name: `Day ${day.seq} Start`,
          type: 'start'
        })

        if (startCoord[0] !== endCoord[0] || startCoord[1] !== endCoord[1]) {
          stops.push({
            lat: endCoord[1],
            lon: endCoord[0],
            name: `Day ${day.seq} End`,
            type: 'end'
          })
        }
      }



      return {
        id: day.id,
        coordinates: coords,
        color: dayColors[idx % dayColors.length],
        stops: stops,
        daySeq: day.seq
      }
    })
    .filter(Boolean)
}

export default function TripDetailPage({ params }: { params: { slug: string } }) {
  const [trip, setTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [totalRouteKm, setTotalRouteKm] = useState<number | null>(null)
  const [stopsLoading, setStopsLoading] = useState(false)
  const [totalRouteMin, setTotalRouteMin] = useState<number | null>(null)
  const [tripRouteCoords, setTripRouteCoords] = useState<[number, number][]>([])
  const [summaryDays, setSummaryDays] = useState<Day[]>([])
  const [showDebug, setShowDebug] = useState(false)
  const [hoverDayId, setHoverDayId] = useState<string | null>(null)
  const [visibleDays, setVisibleDays] = useState<Record<string, boolean>>({})
  const [showCountrySuffix, setShowCountrySuffix] = useState(false)
  const [hasUserSettingShowCountry, setHasUserSettingShowCountry] = useState<boolean | null>(null)
  const [showRoutes, setShowRoutes] = useState(false)
  const [routesDayId, setRoutesDayId] = useState<string | null>(null)
  const router = useRouter()
  const searchParams = useSearchParams()
  const isFullMap = (searchParams?.get('view') || '') === 'map'
  const [fullMapHeight, setFullMapHeight] = useState<number>(0)
  useEffect(() => {
    if (!isFullMap) return
    const calc = () => setFullMapHeight(Math.max(300, window.innerHeight - 120))
    calc()
    window.addEventListener('resize', calc)
    return () => window.removeEventListener('resize', calc)
  }, [isFullMap])
  const { toast } = useToast()

  // Function to load stops for all days (pure function without state updates)
  const loadStopsForAllDays = async (tripId: string, days: Day[]) => {
    if (!days.length) return {}

    const stopsMap: Record<string, any[]> = {}

    try {
      // Load stops for each day
      await Promise.all(
        days.map(async (day) => {
          try {
            const stopsResponse = await listStops(tripId, day.id, { includePlaces: true })
            stopsMap[day.id] = stopsResponse.data || []
          } catch (error) {
            console.warn(`Failed to load stops for day ${day.seq}:`, error)
            stopsMap[day.id] = []
          }
        })
      )
    } catch (error) {
      console.error('Error loading stops for days:', error)
    }

    return stopsMap
  }

  // Initialize visibleDays from URL when in full-screen map
  useEffect(() => {
    if (!isFullMap) return
    const v = (searchParams?.get('visible') || '')
    if (!v) return
    const ids = new Set(v.split(',').filter(Boolean))
    setVisibleDays(prev => {
      const next: Record<string, boolean> = { ...prev }
      for (const d of [...summaryDays]) next[d.id] = ids.has(d.id)
      return next
    })
  }, [isFullMap, searchParams, summaryDays.length])

  // Keep URL in sync with day visibility while in full-screen map
  useEffect(() => {
    if (!isFullMap || !summaryDays.length) return

    const visible = [...summaryDays]
      .sort((a,b)=>a.seq-b.seq)
      .filter(d => (visibleDays[d.id] ?? true))
      .map(d => d.id)

    const qs = new URLSearchParams(searchParams?.toString() || '')
    qs.set('view', 'map')
    if (visible.length) qs.set('visible', visible.join(','))
    else qs.delete('visible')

    // Use setTimeout to avoid state update during render
    setTimeout(() => {
      router.replace(`?${qs.toString()}`)
    }, 0)
  }, [visibleDays, isFullMap, summaryDays.length, searchParams, router])

  // Prefilled locations for DaysList summary
  const [dayLocations, setDayLocations] = useState<Record<string, { start?: any; end?: any; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][]; stops?: any[] }>>({})
  useEffect(() => {
    const onStops = (e: any) => {
      const { dayId, stops } = e.detail || {}
      if (!dayId || !stops) return
      setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), stops } }))
    }
    window.addEventListener('day-stops-updated', onStops as any)
    return () => window.removeEventListener('day-stops-updated', onStops as any)
  }, [])


  // Load user default for country suffix
  useEffect(() => {
    (async () => {
      try {
        const s = await getUserSettings()
        if (typeof s.show_country_suffix === 'boolean') {
          setShowCountrySuffix(s.show_country_suffix)
          setHasUserSettingShowCountry(true)
        } else {
          setHasUserSettingShowCountry(false)
        }
      } catch {
        setHasUserSettingShowCountry(false)
      }
    })()
  }, [])

  // If user setting not set, infer from trip places and persist once
  useEffect(() => {
    if (hasUserSettingShowCountry !== false) return
    if (!summaryDays.length || !Object.keys(dayLocations).length) return

    // Try to find first country code from any day's start/end
    const days = [...summaryDays].sort((a,b) => a.seq - b.seq)
    let cc: string | null = null
    for (const d of days) {
      const loc: any = dayLocations[d.id]
      if (!loc) continue
      const placeCandidates = [loc?.start, loc?.end]
      for (const p of placeCandidates) {
        if (!p || !p.meta) continue
        const m: any = p.meta
        const nm: any = m.normalized?.components || {}
        const cand = (nm.country_code || m.country_code || nm.country || m.country)
        if (cand) { cc = String(cand).toUpperCase(); break }
      }
      if (cc) break
    }
    const inferred = cc && cc !== 'US' && cc !== 'USA'
    const val = !!inferred
    setShowCountrySuffix(val)
    updateUserSettings({ show_country_suffix: val }).catch(() => {})
    setHasUserSettingShowCountry(true)
  }, [summaryDays.length, Object.keys(dayLocations).length, hasUserSettingShowCountry])

  // Color palette for per-day segments
  const dayColors = ['#ef4444','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ec4899','#22c55e','#eab308','#06b6d4','#f97316'] as const

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('auth_token')
    if (!token) {
      // Use setTimeout to avoid state update during render
      setTimeout(() => {
        router.push('/login')
      }, 0)
      return
    }

    // Quick backend health check for better error messaging
    ;(async () => {
      const ok = await checkHealth(2500)
      if (!ok) {
        setError('Backend unavailable. Please check connection and try again.')
        setLoading(false)
        return
      }
      fetchTripDetails()
    })()
  }, [params.slug])

  useEffect(() => {
    const onUpdate = (e: any) => {
      const { dayId, loc } = e.detail || {}
      if (!dayId || !loc) return

      // Use setTimeout to avoid state updates during render
      setTimeout(() => {
        setDayLocations(prev => {
          const next = { ...prev, [dayId]: {
            start: loc.start || null,
            end: loc.end || null,
            route_total_km: loc.route_total_km ?? undefined,
            route_total_min: loc.route_total_min ?? undefined,
            route_coordinates: loc.route_coordinates ?? undefined,
          } }

          // Recompute totals and combined coords
          let kmSum = 0; let minSum = 0; const combined: [number, number][] = []
          for (const d of [...summaryDays].sort((a,b)=>a.seq-b.seq)) {
            const l: any = (next as any)[d.id]
            if (l) {
              if (typeof l.route_total_km === 'number') kmSum += l.route_total_km
              if (typeof l.route_total_min === 'number') minSum += l.route_total_min
              if (l.route_coordinates && l.route_coordinates.length) combined.push(...l.route_coordinates)
            }
          }

          // Batch all state updates
          setTotalRouteKm(combined.length ? kmSum : null)
          setTotalRouteMin(combined.length ? minSum : null)
          setTripRouteCoords(combined)
          setVisibleDays(v => ({ ...v, [dayId]: !!(next[dayId]?.route_coordinates && next[dayId]!.route_coordinates!.length) }))

          return next
        })
      }, 0)
    }
    window.addEventListener('day-summary-updated', onUpdate as any)
    return () => window.removeEventListener('day-summary-updated', onUpdate as any)
  }, [summaryDays.length])

  // When a day is added, ensure it's visible in the main map breakdown and totals
  useEffect(() => {
    const onDayAdded = (e: any) => {
      const { day } = e.detail || {}
      if (!day) return
      setSummaryDays(prev => {
        const exists = prev.find(d => d.id === day.id)
        if (exists) return prev
        const next = [...prev, day]
        // Initialize visibility off until a route exists
        setVisibleDays(v => ({ ...v, [day.id]: false }))
        return next
      })
    }
    window.addEventListener('day-added', onDayAdded as any)
    return () => window.removeEventListener('day-added', onDayAdded as any)
  }, [])

  const fetchTripDetails = async () => {
    try {
      // Use the enhanced API function instead of raw fetch
      const tripsResponse = await listTripsEnhanced()
      console.log('Trips API response:', tripsResponse) // Debug log

      if (!tripsResponse.success || !tripsResponse.data) {
        throw new Error('Failed to fetch trips')
      }

      // Find the trip with matching slug
      const trips = tripsResponse.data.data || []
      const foundTrip = trips.find((t: Trip) => t.slug === params.slug)

      if (!foundTrip) {
        console.log('Trip not found. Available trips:', trips.map((t: Trip) => ({ id: t.id, slug: t.slug, title: t.title })))
        setError('Trip not found')
        return
      }

      // Get API base URL for the remaining calls
      const apiBaseUrl = await getApiBase()

      // Fetch trip details and days summary in parallel
      const [tripResponse, summaryResp] = await Promise.all([
        fetchWithAuth(`${apiBaseUrl}/trips/${foundTrip.id}`),
        (async () => {
          try {
            // Prefer lightweight bulk route summaries
            const daysResp = await fetchWithAuth(`${apiBaseUrl}/trips/${foundTrip.id}/days`)
            if (!daysResp.ok) throw new Error('days fetch failed')
            const daysJson = await daysResp.json()
            const dayIds: string[] = (daysJson.days || []).map((d: any) => d.id)
            if (!dayIds.length) return { locations: [], days: [] }
            try {
              const bulk = await getBulkDayActiveSummaries(dayIds)
              // shape into the old summary format the page expects
              const locations = bulk.summaries.map(s => ({
                day_id: s.day_id,
                start: s.start || null,
                end: s.end || null,
                route_total_km: s.route_total_km ?? undefined,
                route_total_min: s.route_total_min ?? undefined,
                route_coordinates: s.route_coordinates ?? undefined,
              }))
              return { locations, days: daysJson.days }
            } catch {
              const s = await getDaysSummary(foundTrip.id)
              return s.data || null
            }
          } catch { return null }
        })()
      ])

      if (!tripResponse.ok) {
        throw new Error(`Failed to fetch trip details: ${tripResponse.status}`)
      }

      const tripData = await tripResponse.json()
      setTrip(tripData)

      if (summaryResp) {
        const locs = summaryResp.locations as DayLocationsSummary[]
        const map: Record<string, { start?: any; end?: any; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][] }> = {}
        let kmSum = 0; let minSum = 0; let hasAny = false
        const combined: [number, number][] = []
        for (const l of locs) {
          map[l.day_id] = {
            start: l.start || null,
            end: l.end || null,
            route_total_km: l.route_total_km ?? undefined,
            route_total_min: l.route_total_min ?? undefined,
            route_coordinates: l.route_coordinates ?? undefined,
          }
          if (typeof l.route_total_km === 'number') { kmSum += l.route_total_km; hasAny = true }
          if (typeof l.route_total_min === 'number') { minSum += l.route_total_min }
          if (l.route_coordinates && l.route_coordinates.length) {
            combined.push(...l.route_coordinates)
          }
        }
        // Load stops for all days and add to dayLocations
        setStopsLoading(true)
        const stopsMap = await loadStopsForAllDays(foundTrip.id, summaryResp.days as Day[])
        setStopsLoading(false)

        // Update dayLocations with stops data in one go
        const mapWithStops = { ...map }
        for (const [dayId, stops] of Object.entries(stopsMap)) {
          if (mapWithStops[dayId]) {
            // Filter out start and end stops, include intermediate stops
            const intermediateStops = stops.filter((stop: any) =>
              stop.kind !== 'start' && stop.kind !== 'end'
            )
            mapWithStops[dayId].stops = intermediateStops
          }
        }

        // Set all state in one batch
        setSummaryDays(summaryResp.days as Day[])
        setDayLocations(mapWithStops)

        if (hasAny) {
          setTotalRouteKm(kmSum)
          setTotalRouteMin(minSum)
          setTripRouteCoords(combined)
          // initialize visibility (default true) for days that have geometry
          const initialVis: Record<string, boolean> = {}
          for (const d of summaryResp.days as Day[]) {
            const loc = (map as any)[d.id]
            initialVis[d.id] = !!(loc && loc.route_coordinates && loc.route_coordinates.length)
          }
          setVisibleDays(initialVis)
        } else {
          setTotalRouteKm(null)
          setTotalRouteMin(null)
          setTripRouteCoords([])
          setVisibleDays({})
        }
      }
    } catch (err) {
      console.error('Error fetching trip details:', err)
      setError(err instanceof Error ? err.message : 'Failed to load trip details')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingState message="Loading trip details..." />
  }

  if (error || !trip) {
    return <ErrorState
      title="Trip Not Found"
      message={error || 'The requested trip could not be found.'}
      actionLabel="Back to Trips"
      actionHref="/trips"
    />
  }

  if (isFullMap) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="w-screen px-0 py-4">
          <div className="flex items-center justify-between mb-3 px-4">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/trips/${trip?.slug || params.slug}`}>
                <ArrowLeft className="h-4 w-4 mr-2" /> Back to Trip
              </Link>
            </Button>
            <div className="text-sm text-gray-700">
              {typeof totalRouteKm === 'number' && typeof totalRouteMin === 'number' ? (
                <span>{Math.round(totalRouteKm)} km • {Math.floor(totalRouteMin / 60)}h {Math.round(totalRouteMin % 60)}m</span>
              ) : (
                <span className="text-gray-400">Routing unavailable</span>
              )}
            </div>
          </div>
          <div className="rounded-md overflow-hidden px-0 relative">
            <TripRouteMap
              height={fullMapHeight || 600}
              routes={convertToTripRouteData(summaryDays, dayLocations, dayColors)}
              highlightRouteId={hoverDayId}
              visibleRoutes={visibleDays}
              interactive={true}
              className="w-full"
            />
            {/* Overlay legend + toggles + permalink */}
            <div className="absolute bottom-3 left-3 right-3 bg-white/85 backdrop-blur-sm rounded shadow p-2 text-xs text-gray-700 flex items-center gap-4 flex-wrap">
              {[...summaryDays].sort((a,b)=>a.seq-b.seq).map((d, idx) => (
                <label key={d.id} className="flex items-center gap-2 cursor-pointer"
                  onMouseEnter={() => setHoverDayId(d.id)}
                  onMouseLeave={() => setHoverDayId(null)}
                >
                  <input
                    type="checkbox"
                    checked={visibleDays[d.id] ?? true}
                    onChange={(e) => setVisibleDays(v => ({ ...v, [d.id]: e.target.checked }))}
                  />
                  <span className="inline-block w-3 h-0.5" style={{ backgroundColor: dayColors[idx % dayColors.length] }} />
                  <span>Day {d.seq}</span>
                </label>
              ))}
              <Button
                variant="outline"
                size="xs"
                className="ml-auto"
                onClick={() => {
                  try {
                    const qs = new URLSearchParams(searchParams?.toString() || '')
                    qs.set('view','map')
                    const visible = [...summaryDays]
                      .sort((a,b)=>a.seq-b.seq)
                      .filter(d => (visibleDays[d.id] ?? true))
                      .map(d => d.id)
                    if (visible.length) qs.set('visible', visible.join(','))
                    else qs.delete('visible')
                    const url = `${window.location.origin}/trips/${trip?.slug || params.slug}?${qs.toString()}`
                    navigator.clipboard.writeText(url)
                    toast({ title: 'Link copied', description: 'Permalink to this view was copied to clipboard.' })
                  } catch {}
                }}
                title="Copy permalink"
              >Copy link</Button>
            </div>
          </div>

        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" size="sm" asChild>
            <Link href="/trips">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Trips
            </Link>
          </Button>

          <div className="flex-1">
            <div className="flex items-center space-x-4 mb-1">
              <h1 className="text-3xl font-bold text-gray-900">{trip.title}</h1>
            </div>
                {/* Small activity indicator while recomputing trip totals/combination */}
                {loading && (
                  <div className="text-xs text-blue-600">Updating trip route…</div>
                )}

            <p className="text-gray-600">Trip to {trip.destination}</p>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Trip Route Overview */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Total Trip Route</CardTitle>
                <CardDescription>
                  Combined driving across all days
                </CardDescription>
              </div>
              <div className="flex items-center gap-4">
                {typeof totalRouteKm === 'number' && typeof totalRouteMin === 'number' && (
                  <div className="text-sm text-gray-700">
                    {Math.round(totalRouteKm)} km • {Math.floor(totalRouteMin / 60)}h {Math.round(totalRouteMin % 60)}m
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <select className="text-xs border rounded px-1 py-0.5" value={routesDayId || ''} onChange={(e) => setRoutesDayId(e.target.value || null)}>
                    <option value="">Select day…</option>
                    {[...summaryDays].sort((a,b)=>a.seq-b.seq).map(d => (
                      <option key={d.id} value={d.id}>Day {d.seq}</option>
                    ))}
                  </select>
                  <Button variant="outline" size="sm" onClick={() => {
                    const id = routesDayId || hoverDayId || (summaryDays[0]?.id || null)
                    if (!id) { toast({ title: 'No day selected', description: 'Choose a day to manage routes.' }); return }
                    setRoutesDayId(id); setShowRoutes(true)
                  }}>Manage routes</Button>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {summaryDays.length > 0 ? (
              <TripRouteMap
                routes={convertToTripRouteData(summaryDays, dayLocations, dayColors)}
                highlightRouteId={hoverDayId}
                visibleRoutes={visibleDays}
                height={280}
                className="rounded-md overflow-hidden"
                interactive={true}
              />
            ) : (
              <div className="text-sm text-gray-500">Routing unavailable yet. Set start/end for days to see total route.</div>
            )}
            {/* Legend with toggles and hover */}
            {summaryDays.length > 0 && (
              <div className="mt-2 text-xs text-gray-600 flex items-center gap-4 flex-wrap">
                {[...summaryDays].sort((a,b)=>a.seq-b.seq).map((d, idx) => (
                  <label key={d.id} className="flex items-center gap-2 cursor-pointer"
                    onMouseEnter={() => setHoverDayId(d.id)}
                    onMouseLeave={() => setHoverDayId(null)}
                  >
                    <input type="checkbox" checked={visibleDays[d.id] ?? true} onChange={(e) => setVisibleDays(v => ({ ...v, [d.id]: e.target.checked }))} />
                    <span className="inline-block w-3 h-0.5" style={{ backgroundColor: dayColors[idx % dayColors.length] }} />
                    <span>Day {d.seq}</span>
                  </label>
                ))}
              </div>
            )}
            {/* Per-day breakdown */}
            {summaryDays.length > 0 && (
              <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {[...summaryDays].sort((a, b) => a.seq - b.seq).map((d) => {
                  const loc = (dayLocations as any)[d.id]
                  const has = loc && typeof loc.route_total_km === 'number' && typeof loc.route_total_min === 'number'
                  return (
                    <div key={d.id} className="flex items-center justify-between text-sm text-gray-700 p-2 border rounded">
                      <div>
                        <span className="font-medium">Day {d.seq}</span>
                        {d.calculated_date && (
                          <span className="ml-2 text-gray-500">
                            {new Date(d.calculated_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        {has ? (
                          <span>{Math.round(loc.route_total_km)} km • {Math.floor(loc.route_total_min / 60)}h {Math.round(loc.route_total_min % 60)}m</span>
                        ) : (
                          <span className="text-gray-400">Routing unavailable</span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
            {/* Full screen map CTA */}
            {tripRouteCoords.length > 0 && (
              <div className="mt-4 text-right">
                <Button variant="outline" asChild>
                  <Link href={`/trips/${trip.slug}?view=map`}>View on full-screen map</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Trip Info Card */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Trip Overview
                </CardTitle>
                <CardDescription>
                  Plan and manage your road trip to {trip.destination}
                </CardDescription>
              </div>
              <Badge variant={trip.status === 'active' ? 'default' : 'secondary'}>
                {trip.status.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-center gap-3">
                <TripDateActions
                  trip={trip}
                  onTripUpdate={(updatedTrip) => setTrip(updatedTrip)}
                  size="sm"
                />
              </div>

              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="font-medium">Members</p>
                  <p className="text-gray-600">{trip.members.length} members</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="font-medium">Status</p>
                  <p className="text-gray-600">{trip.is_published ? 'Published' : 'Draft'}</p>
                </div>
              </div>
            </div>

            {trip.created_by_user && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  Created by <span className="font-medium text-gray-700">{trip.created_by_user.display_name}</span> on {new Date(trip.created_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Days Section integrated (full management) */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Trip Days</CardTitle>
                <CardDescription>
                  Plan your daily itinerary and routes
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <TripDayManagement
              trip={trip}
              className="max-w-7xl"
              prefilledLocations={dayLocations}
              showCountrySuffix={showCountrySuffix}
            />
            <style jsx global>{`
              /* Make trip day cards use the country suffix toggle via CSS var, if needed */
            `}</style>
          </CardContent>
        </Card>
      </div>
      {/* Manage Day Routes Dialog using GenericModal */}
      <GenericModal
        isOpen={showRoutes}
        onClose={() => setShowRoutes(false)}
        title="Manage Day Routes"
        size="xl"
        showCloseButton={true}
        closeOnBackdropClick={false}
      >
        <ManageDayRoutesDialog
          dayId={routesDayId || summaryDays[0]?.id || ''}
          open={showRoutes}
          onOpenChange={(v)=>setShowRoutes(v)}
          onRoutesChanged={async (rv) => {
            const activeDayId = routesDayId || summaryDays[0]?.id
            if (!activeDayId) return
            try {
              let loc: any = null
              if (rv && (rv.geojson || typeof rv.total_km === 'number')) {
                loc = {
                  start: (dayLocations as any)[activeDayId]?.start || null,
                  end: (dayLocations as any)[activeDayId]?.end || null,
                  route_total_km: rv.total_km ?? undefined,
                  route_total_min: rv.total_min ?? undefined,
                  route_coordinates: (rv as any).geojson?.coordinates ?? undefined,
                }
              } else {
                const { getDayActiveSummary } = await import('@/lib/api/routing')
                const s = await getDayActiveSummary(activeDayId)
                loc = {
                  start: s.start || null,
                  end: s.end || null,
                  route_total_km: s.route_total_km ?? undefined,
                  route_total_min: s.route_total_min ?? undefined,
                  route_coordinates: s.route_coordinates ?? undefined,
                }
              }
              // Update local state and totals (batch updates to avoid render issues)
              setTimeout(() => {
                setDayLocations(prev => {
                  const next = { ...prev, [activeDayId]: loc }
                  let kmSum = 0; let minSum = 0; const combined: [number, number][] = []
                  for (const d of [...summaryDays].sort((a,b)=>a.seq-b.seq)) {
                    const l: any = (next as any)[d.id]
                    if (l) {
                      if (typeof l.route_total_km === 'number') kmSum += l.route_total_km
                      if (typeof l.route_total_min === 'number') minSum += l.route_total_min
                      if (l.route_coordinates && l.route_coordinates.length) combined.push(...l.route_coordinates)
                    }
                  }

                  // Batch all state updates together
                  setTotalRouteKm(combined.length ? kmSum : null)
                  setTotalRouteMin(combined.length ? minSum : null)
                  setTripRouteCoords(combined)
                  setVisibleDays(v => ({ ...v, [activeDayId]: !!(loc.route_coordinates && loc.route_coordinates.length) }))

                  return next
                })
              }, 0)
            } catch {}
          }}
        />
      </GenericModal>
    </div>
  )
}
