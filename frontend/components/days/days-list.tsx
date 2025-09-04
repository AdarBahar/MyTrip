/**
 * Days List Component
 * Displays a list of days for a trip with management actions
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Day, Trip } from '@/types';
import { Place, createPlace, getPlace, getPlacesBulk } from '@/lib/api/places';
import { useDays } from '@/hooks/use-days';
import { getDaysSummary, DayLocationsSummary } from '@/lib/api/days';
import { computeDayRoute } from '@/lib/api/routing';
import { useToast } from '@/components/ui/use-toast';
import { listStops, createStop, type StopWithPlace } from '@/lib/api/stops';
import { DayCard } from './day-card';
import StopsList from '@/components/stops/StopsList';
import InlineStopsPreview from '@/components/stops/InlineStopsPreview';
import { CreateDayDialog } from './create-day-dialog';
import { EditDayDialog } from './edit-day-dialog';
import { DeleteDayDialog } from './delete-day-dialog';
import { DayLocationEditor } from './day-location-editor';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Calendar, AlertCircle } from 'lucide-react';
import { getTripDuration, formatDate } from '@/lib/date-utils';

interface DaysListProps {
  trip: Trip;
  onDayClick?: (day: Day) => void;
  className?: string;
  prefilledLocations?: Record<string, { start?: Place | null; end?: Place | null; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][] }>
  showCountrySuffix?: boolean;
}

export function DaysList({ trip, onDayClick, className = '', prefilledLocations, showCountrySuffix = false }: DaysListProps) {
  const { days, loading, error, createDay, updateDay, deleteDay, toggleRestDay } = useDays({
    tripId: trip.id,
    includeStops: false,
    autoRefresh: true
  });

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const { toast } = useToast();
  const [editingDay, setEditingDay] = useState<Day | null>(null);
  const [deletingDay, setDeletingDay] = useState<Day | null>(null);
  const [editingLocationDay, setEditingLocationDay] = useState<Day | null>(null);
  const [dayLocations, setDayLocations] = useState<Record<string, { start?: Place | null; end?: Place | null; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][]; stops?: StopWithPlace[] }>>(prefilledLocations || {});

  // Keep internal state in sync with parent-provided summary
  useEffect(() => {
    if (prefilledLocations && Object.keys(prefilledLocations).length) {
      setDayLocations(prefilledLocations);
    }
  }, [prefilledLocations]);

  const tripDuration = getTripDuration(trip, days);

  const handleCreateDay = async (dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> }) => {
    const newDay = await createDay(dayData);
    if (newDay) {
      setShowCreateDialog(false);
      try { window.dispatchEvent(new CustomEvent('day-added', { detail: { day: newDay } })) } catch {}
    }
  };

  const handleEditDay = async (dayId: string, dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> }) => {
    const updatedDay = await updateDay(dayId, dayData);
    if (updatedDay) {
      setEditingDay(null);
    }
  };

  const handleDeleteDay = async (dayId: string) => {
    const success = await deleteDay(dayId);
    if (success) {
      setDeletingDay(null);
    }
  };

  const handleToggleRestDay = async (day: Day) => {
    await toggleRestDay(day.id);
  };

  const handleEditLocations = (day: Day) => {
    setEditingLocationDay(day);
  };

  const ensurePlaceSaved = async (place: Place): Promise<string> => {
    // If place.id looks like a DB ULID (26 chars), assume already saved
    if (place?.id && place.id.length === 26) return place.id;
    const created = await createPlace({
      name: place.name,
      address: place.address,
      lat: place.lat,
      lon: place.lon,
      meta: place.meta,
    });
    return created.id;
  };

  const fetchDayLocations = async (tripId: string, dayId: string) => {
    try {
      const res = await listStops(trip.id, dayId, { includePlaces: true });
      const stops = (res.stops as StopWithPlace[]);
      // Store stops for markers and broadcast to main page
      setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), stops } }))
      try { window.dispatchEvent(new CustomEvent('day-stops-updated', { detail: { dayId, stops } })) } catch {}
      const kindOf = (s: StopWithPlace) => (typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any));
      const startStopAny = stops.find(s => kindOf(s) === 'start');
      const endStopAny = stops.find(s => kindOf(s) === 'end');

      // If both embedded, no need to fetch
      const startEmbedded = (startStopAny as any)?.place;
      const endEmbedded = (endStopAny as any)?.place;

      if (startEmbedded && endEmbedded) {
        // Update start/end then compute route preview for fresh geometry
        const startPlace = { id: startEmbedded.id, name: startEmbedded.name, address: startEmbedded.address, lat: startEmbedded.lat, lon: startEmbedded.lon, meta: startEmbedded.meta, created_at: '', updated_at: '' } as Place;
        const endPlace = { id: endEmbedded.id, name: endEmbedded.name, address: endEmbedded.address, lat: endEmbedded.lat, lon: endEmbedded.lon, meta: endEmbedded.meta, created_at: '', updated_at: '' } as Place;
        try {
          setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), start: startPlace, end: endPlace } }));
          // Auto-recompute if there are at least 2 routeable points
          const via = stops.filter(s => (typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any)) === 'via')
          const canRoute = !!startPlace && !!endPlace && (via.length >= 1 || stops.length >= 2)
          if (canRoute) {
            const { throttledComputeDayRoute, commitDayRouteWithFallback, getDayActiveSummary } = await import('@/lib/api/routing')
            const preview = await throttledComputeDayRoute(dayId, { optimize: true })
            await commitDayRouteWithFallback(dayId, preview.preview_token, 'Default', { optimize: false })
            const s = await getDayActiveSummary(dayId)
            const loc = {
              start: s.start || null,
              end: s.end || null,
              route_total_km: s.route_total_km ?? undefined,
              route_total_min: s.route_total_min ?? undefined,
              route_coordinates: s.route_coordinates ?? undefined,
            }
            setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), ...loc } }))
            window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId, loc } }))
          }
        } catch {
          setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), start: startPlace, end: endPlace } }));
        }
        return;
      }

      // Bulk fetch missing places in a single request
      const toFetchIds: string[] = [];
      if (!startEmbedded && startStopAny?.place_id) toFetchIds.push(startStopAny.place_id);
      if (!endEmbedded && endStopAny?.place_id) toFetchIds.push(endStopAny.place_id);
      const fetched = toFetchIds.length ? await getPlacesBulk(toFetchIds) : [];
      const fetchedMap = new Map(fetched.map(p => [p.id, p] as const));

      const startPlace = startEmbedded ? {
        id: startEmbedded.id, name: startEmbedded.name, address: startEmbedded.address, lat: startEmbedded.lat, lon: startEmbedded.lon, meta: startEmbedded.meta, created_at: '', updated_at: ''
      } : (startStopAny?.place_id ? fetchedMap.get(startStopAny.place_id) || null : null);

      const endPlace = endEmbedded ? {
        id: endEmbedded.id, name: endEmbedded.name, address: endEmbedded.address, lat: endEmbedded.lat, lon: endEmbedded.lon, meta: endEmbedded.meta, created_at: '', updated_at: ''
      } : (endStopAny?.place_id ? fetchedMap.get(endStopAny.place_id) || null : null);

      // If both present, (re)compute automatically as well
      setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), start: startPlace || null, end: endPlace || null } }));
      const via = stops.filter(s => (typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any)) === 'via')
      const canRoute = !!startPlace && !!endPlace && (via.length >= 1 || stops.length >= 2)
      if (canRoute) {
        try {
          const { throttledComputeDayRoute, commitDayRouteWithFallback, getDayActiveSummary } = await import('@/lib/api/routing')
          const preview = await throttledComputeDayRoute(dayId, { optimize: true })
          await commitDayRouteWithFallback(dayId, preview.preview_token, 'Default', { optimize: false })
          const s = await getDayActiveSummary(dayId)
          const loc = {
            start: s.start || null,
            end: s.end || null,
            route_total_km: s.route_total_km ?? undefined,
            route_total_min: s.route_total_min ?? undefined,
            route_coordinates: s.route_coordinates ?? undefined,
          }
          setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), ...loc } }))
          window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId, loc } }))
        } catch {}
      }
    } catch (e: any) {
      if (e?.status === 429) {
        toast({ title: 'Routing temporarily unavailable', description: 'Rate-limited by routing provider. Please try again in about a minute.', variant: 'destructive' })
      }
      // ignore other errors
    }
  };

  // Listen for mini-refresh events from DayCard dialog actions
  useEffect(() => {
    const onUpdate = (e: any) => {
      const { dayId, loc } = e.detail || {}
      if (!dayId || !loc) return
      setDayLocations(prev => ({
        ...prev,
        [dayId]: {
          ...(prev[dayId] || {}),
          start: loc.start || null,
          end: loc.end || null,
          route_total_km: loc.route_total_km ?? undefined,
          route_total_min: loc.route_total_min ?? undefined,
          route_coordinates: loc.route_coordinates ?? undefined,
        },
      }))
    }
    window.addEventListener('day-summary-updated', onUpdate as any)
    return () => window.removeEventListener('day-summary-updated', onUpdate as any)
  }, [])

  useEffect(() => {
    // Respond to stop mutations by refreshing active summaries for the affected day
    const onStopsMutated = async (e: any) => {
      const did = e?.detail?.dayId
      if (!did) return
      try {
        const { getDayActiveSummary } = await import('@/lib/api/routing')
        const s = await getDayActiveSummary(did)
        const loc = {
          start: (s.start as any) || null,
          end: (s.end as any) || null,
          route_total_km: s.route_total_km ?? undefined,
          route_total_min: s.route_total_min ?? undefined,
          route_coordinates: s.route_coordinates ?? undefined,
        }
        setDayLocations(prev => ({ ...prev, [did]: { ...(prev[did] || {}), ...loc } }))
      } catch {}
    }
    window.addEventListener('stops-mutated', onStopsMutated as any)

    // Prefer lightweight bulk active summaries when days exist
    ;(async () => {
      if (!days || days.length === 0) { setDayLocations({}); return }
      try {
        const { getBulkDayActiveSummaries } = await import('@/lib/api/routing')
        const res = await getBulkDayActiveSummaries(days.map(d => d.id))
        if (res?.summaries) {
          const base: Record<string, { start?: Place | null; end?: Place | null; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][]; stops?: StopWithPlace[] }> = {}
          for (const s of res.summaries) {
            base[s.day_id] = {
              start: (s.start as any) || null,
              end: (s.end as any) || null,
              route_total_km: s.route_total_km ?? undefined,
              route_total_min: s.route_total_min ?? undefined,
              route_coordinates: s.route_coordinates ?? undefined,
              // Preserve existing stops if we already fetched them
              stops: undefined,
            }
          }
          setDayLocations(prev => {
            const next: typeof base = {}
            for (const did of Object.keys(base)) {
              next[did] = { ...base[did], stops: (prev[did] as any)?.stops || [] }
            }
            return next
          })
          return
        }
      } catch {}
      finally {
        window.removeEventListener('stops-mutated', onStopsMutated as any)
      }
      // Fallback to previous summary endpoint and old per-day flow if bulk fails
      try {
        const summary = await getDaysSummary(trip.id)
        if (summary.data) {
          const locs = summary.data.locations as DayLocationsSummary[]
          const base: Record<string, { start?: Place | null; end?: Place | null; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][]; stops?: StopWithPlace[] }> = {}
          for (const l of locs) {
            base[l.day_id] = {
              start: l.start || null,
              end: l.end || null,
              route_total_km: l.route_total_km ?? undefined,
              route_total_min: l.route_total_min ?? undefined,
              route_coordinates: l.route_coordinates ?? undefined,
              stops: [],
            }
          }
          setDayLocations(base)
          // In background, fetch stops (with places) for markers and counts
          try {
            const results = await Promise.all(days.map(d => listStops(trip.id, d.id, { includePlaces: true })))
            setDayLocations(prev => {
              const next = { ...prev }
              results.forEach((res, idx) => { next[days[idx].id] = { ...(next[days[idx].id] || {}), stops: (res.stops as StopWithPlace[]) } })
              return next
            })
          } catch {}
          return
        }
      } catch {}

      // Fallback to per-day stops + places flow
      try {
        const results = await Promise.all(days.map(d => listStops(trip.id, d.id, { includePlaces: true })))
        const neededIds = new Set<string>()
        const dayStops: Record<string, StopWithPlace[]> = {}
        results.forEach((res, idx) => {
          const d = days[idx]
          const stops = (res.stops as StopWithPlace[])
          dayStops[d.id] = stops
          for (const s of stops) {
            const kind = typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any)
            const hasPlace = (s as any).place
            if ((kind === 'start' || kind === 'end') && !hasPlace && s.place_id) {
              neededIds.add(s.place_id)
            }
          }
        })
        const bulk = neededIds.size ? await getPlacesBulk(Array.from(neededIds)) : []
        const bulkMap = new Map(bulk.map(p => [p.id, p] as const))
        const nextLocations: Record<string, { start?: Place | null; end?: Place | null }> = {}
        for (const d of days) {
          const stops = dayStops[d.id] || []
          const start = stops.find(s => (typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any)) === 'start')
          const end = stops.find(s => (typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any)) === 'end')
          const startEmbedded = (start as any)?.place
          const endEmbedded = (end as any)?.place
          const startPlace = startEmbedded ? {
            id: startEmbedded.id, name: startEmbedded.name, address: startEmbedded.address, lat: startEmbedded.lat, lon: startEmbedded.lon, meta: startEmbedded.meta, created_at: '', updated_at: ''
          } : (start?.place_id ? bulkMap.get(start.place_id) || null : null)
          const endPlace = endEmbedded ? {
            id: endEmbedded.id, name: endEmbedded.name, address: endEmbedded.address, lat: endEmbedded.lat, lon: endEmbedded.lon, meta: endEmbedded.meta, created_at: '', updated_at: ''
          } : (end?.place_id ? bulkMap.get(end.place_id) || null : null)
          nextLocations[d.id] = { start: startPlace || null, end: endPlace || null }
        }
        setDayLocations(nextLocations)
      } catch {}
    })()
  }, [days, trip.id]);

  const handleSaveLocations = async (dayId: string, startLocation: Place | null, endLocation: Place | null) => {
    try {
      console.log('Saving locations for day', dayId, { startLocation, endLocation });
      // Load current stops to determine next seq
      const current = await listStops(trip.id, dayId, {});
      const stops = current.stops as any[];
      const maxSeq = stops.length ? Math.max(...stops.map(s => s.seq)) : 0;

      // Create start stop if provided
      if (startLocation) {
        const placeId = await ensurePlaceSaved(startLocation);
        // Ensure no existing start
        const existingStart = stops.find(s => s.kind === 'start');
        if (!existingStart) {
          await createStop(trip.id, dayId, {
            place_id: placeId,
            seq: 1,
            kind: 'start',
            fixed: true,
          });
        }
      }

      // Create end stop
      if (endLocation) {
        const placeId = await ensurePlaceSaved(endLocation);
        const existingEnd = stops.find(s => s.kind === 'end');
        if (!existingEnd) {
          await createStop(trip.id, dayId, {
            place_id: placeId,
            seq: Math.max(2, maxSeq + 1),
            kind: 'end',
            fixed: true,
          });
        }
      }

      // Refresh display
      await fetchDayLocations(trip.id, dayId);
      setEditingLocationDay(null);

      // If both start and end provided and no saved route yet, auto-compute and commit immediately
      if (startLocation && endLocation) {
        try {
          const { listSavedRoutes, throttledComputeDayRoute, commitDayRouteWithFallback, getDayActiveSummary } = await import('@/lib/api/routing')
          const saved = await listSavedRoutes(dayId)
          if (!saved.routes || saved.routes.length === 0) {
            const preview = await throttledComputeDayRoute(dayId, { optimize: false })
            await commitDayRouteWithFallback(dayId, preview.preview_token, 'Default', { optimize: false })
            // Update local UI via lightweight summary and event
            const s = await getDayActiveSummary(dayId)
            const loc = {
              start: s.start || null,
              end: s.end || null,
              route_total_km: s.route_total_km ?? undefined,
              route_total_min: s.route_total_min ?? undefined,
              route_coordinates: s.route_coordinates ?? undefined,
            }
            setDayLocations(prev => ({ ...prev, [dayId]: { ...(prev[dayId] || {}), ...loc } }))
            window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId, loc } }))
          }
        } catch (e) {
          // Non-fatal: user can still compute manually
          console.warn('Auto route compute failed after saving start/end', e)
        }
      }
    } catch (e: any) {
      if (e?.status === 429) {
        toast({ title: 'Routing temporarily unavailable', description: 'Rate-limited by routing provider. Please try again in about a minute.', variant: 'destructive' })
      } else {
        console.error('Failed to save locations', e);
      }
      setEditingLocationDay(null);
    }
      // Notify trip page to recalc totals/combined route (even if auto-route failed)
      try { window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId, loc: { start: startLocation, end: endLocation } } })) } catch {}

  };

  // Get previous day's end location for auto-linking
  const getPreviousDayEndLocation = (currentDay: Day): Place | null => {
    if (currentDay.seq <= 1) return null;
    // Look up previous day's end from cached mapping
    const prevDay = days.find(d => d.seq === currentDay.seq - 1);
    if (!prevDay) return null;
    return dayLocations[prevDay.id]?.end || null;
  };

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-10 w-24" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load days: {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight">Trip Days</h2>
          <p className="text-sm text-gray-500">Manage your days here: add, edit, reorder, and set start/end locations.</p>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Calendar className="h-4 w-4" />
              <span>{days.length} day{days.length !== 1 ? 's' : ''}</span>
            </div>
            {trip.start_date && tripDuration && (
              <span>
                {formatDate(new Date(trip.start_date), { format: 'medium' })} - {' '}
                {formatDate(new Date(new Date(trip.start_date).getTime() + (tripDuration - 1) * 24 * 60 * 60 * 1000), { format: 'medium' })}
              </span>
            )}
          </div>
        </div>

        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Day
        </Button>
      </div>

      {/* Trip Date Warning */}
      {!trip.start_date && days.length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Set a start date for your trip to see calculated dates for each day.
          </AlertDescription>
        </Alert>
      )}

      {/* Days Grid */}
      {days.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No days yet</h3>
          <p className="mt-2 text-sm text-gray-500">
            Get started by adding your first day to the trip.
          </p>
          <Button
            className="mt-4"
            onClick={() => setShowCreateDialog(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add First Day
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {days.map((day) => (
            <div key={day.id} className="space-y-3">
              <DayCard
                day={day}
                startLocation={dayLocations[day.id]?.start || null}
                endLocation={dayLocations[day.id]?.end || null}
                routeKm={(dayLocations[day.id] as any)?.route_total_km}
                routeMin={(dayLocations[day.id] as any)?.route_total_min}
                routeCoordinates={(dayLocations[day.id] as any)?.route_coordinates}
                stopsCount={(dayLocations[day.id]?.stops || []).filter(s => (typeof s.kind === 'string' ? s.kind.toLowerCase() : (s.kind as any)) === 'via').length}
                onClick={onDayClick}
                onEdit={setEditingDay}
                onDelete={setDeletingDay}
                onToggleRestDay={handleToggleRestDay}
                onEditLocations={handleEditLocations}
                showCountrySuffix={showCountrySuffix}
                mapOverlayText={undefined}
                mapExtraMarkers={(dayLocations[day.id]?.stops || []).map((s, idx) => ({
                  id: `${day.id}:${s.id || s.place_id || idx}`,
                  lat: s.place?.lat ?? (s as any).lat,
                  lon: s.place?.lon ?? (s as any).lon,
                  color: s.kind === 'start' ? '#16a34a' : s.kind === 'end' ? '#dc2626' : '#111827',
                  label: [s.place?.name, s.place?.address].filter(Boolean).join(' — ')
                }))}
              />
              {/* Compact, inline stops list for the day */}
              <div className="px-2">
                <InlineStopsPreview
                  tripId={trip.id}
                  dayId={day.id}
                  daySeq={day.seq}
                  maxVisible={5}
                  maxStops={20}
                  onChange={async (stops) => {
                    await fetchDayLocations(trip.id, day.id)
                    // store latest stops for markers
                    setDayLocations(prev => ({ ...prev, [day.id]: { ...(prev[day.id] || {}), stops } }))
                    try {
                      // Recompute and commit the route after stops change
                      const { throttledComputeDayRoute, commitDayRouteWithFallback, getDayActiveSummary } = await import('@/lib/api/routing')
                      const preview = await throttledComputeDayRoute(day.id, { optimize: true })
                      await commitDayRouteWithFallback(day.id, preview.preview_token, 'Default', { optimize: false })
                      // Refresh lightweight summary and broadcast update
                      const s = await getDayActiveSummary(day.id)
                      const loc = {
                        start: s.start || null,
                        end: s.end || null,
                        route_total_km: s.route_total_km ?? undefined,
                        route_total_min: s.route_total_min ?? undefined,
                        route_coordinates: s.route_coordinates ?? undefined,
                      }
                      setDayLocations(prev => ({ ...prev, [day.id]: { ...(prev[day.id] || {}), ...loc } }))
                      window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId: day.id, loc } }))
                    } catch {}
                  }}
                  className="bg-white"
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreateDayDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onCreateDay={handleCreateDay}
        existingDays={days}
      />

      {editingDay && (
        <EditDayDialog
          open={!!editingDay}
          onOpenChange={(open) => !open && setEditingDay(null)}
          day={editingDay}
          onUpdateDay={handleEditDay}
          existingDays={days}
        />
      )}

      {deletingDay && (
        <DeleteDayDialog
          open={!!deletingDay}
          onOpenChange={(open) => !open && setDeletingDay(null)}
          day={deletingDay}
          onDeleteDay={handleDeleteDay}
        />
      )}

      {editingLocationDay && (
        <DayLocationEditor
          day={editingLocationDay}
          tripId={trip.id}
          previousDayEndLocation={getPreviousDayEndLocation(editingLocationDay)}
          open={!!editingLocationDay}
          onOpenChange={(open) => !open && setEditingLocationDay(null)}
          onSave={handleSaveLocations}
        />
      )}
    </div>
  );
}
