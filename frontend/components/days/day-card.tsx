/**
 * Day Card Component
 * Displays a single day with date, status, and actions
 */

'use client';

import React from 'react';
import { Day } from '@/types';
import UpdateRouteButton from './UpdateRouteButton';
import { Place } from '@/lib/api/places';
import {
  getDayDisplayDate,
  getDayDateWithWeekday,
  getRelativeDayDescription,
  getDayTimeStatus
} from '@/lib/date-utils';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { LazyMapPreview } from '@/components/places/lazy-map-preview';
import { formatShortAddress } from '@/lib/api/places';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Calendar,
  MapPin,
  Moon,
  MoreVertical,
  Edit,
  Trash2,
  Navigation,
  Route,
} from 'lucide-react';
import RecomputeRouteButton from './RecomputeRouteButton';
import ManageDayRoutesDialog from './ManageDayRoutesDialog';
import { listSavedRoutes, activateRouteVersion } from '@/lib/api/routing';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';

interface DayCardProps {
  day: Day;
  startLocation?: Place | null;
  endLocation?: Place | null;
  routeKm?: number;
  routeMin?: number;
  routeCoordinates?: [number, number][] | null;
  stopsCount?: number;
  onEdit?: (day: Day) => void;
  onDelete?: (day: Day) => void;
  onToggleRestDay?: (day: Day) => void;
  onEditLocations?: (day: Day) => void;
  onClick?: (day: Day) => void;
  className?: string;
  showCountrySuffix?: boolean;
  mapOverlayText?: string | null;
  mapExtraMarkers?: { id: string; lat: number; lon: number; color?: string }[];
}

export function DayCard({
  day,
  startLocation,
  endLocation,
  routeKm,
  routeMin,
  routeCoordinates,
  stopsCount = 0,
  onEdit,
  onDelete,
  onToggleRestDay,
  onEditLocations,
  onClick,
  className = '',
  showCountrySuffix = true,
  mapOverlayText = null,
  mapExtraMarkers = [],
}: DayCardProps) {
  const hasRouteSummary = typeof routeKm === 'number' && typeof routeMin === 'number';
  const [showRoutes, setShowRoutes] = React.useState(false);
  const [quickRoutes, setQuickRoutes] = React.useState<{ id: string; name: string }[]>([]);

  // Auto-save a default route if start+end exist and no saved routes yet
  const hasStartEnd = !!startLocation && !!endLocation
  const autoAttemptedRef = React.useRef(false)
  const [routingBusy, setRoutingBusy] = React.useState(false)
  const { toast } = useToast()

  // Listen to routing start/finish events to show a tiny indicator
  React.useEffect(() => {
    const onComputeStart = (e: any) => { if (e?.detail?.dayId === day.id) setRoutingBusy(true) }
    const onComputeFinish = (e: any) => { if (e?.detail?.dayId === day.id) setRoutingBusy(false) }
    const onCommitStart = (e: any) => { if (e?.detail?.dayId === day.id) setRoutingBusy(true) }
    const onCommitFinish = (e: any) => { if (e?.detail?.dayId === day.id) setRoutingBusy(false) }
    const onWatchdog = (e: any) => {
      if (e?.detail?.dayId === day.id) {
        toast({ title: 'Auto-committing route', description: 'No commit detected. Watchdog is saving the latest computed route.', duration: 2500 })
      }
    }
    window.addEventListener('routing-compute-start', onComputeStart as any)
    window.addEventListener('routing-compute-finish', onComputeFinish as any)
    window.addEventListener('routing-commit-start', onCommitStart as any)
    window.addEventListener('routing-commit-finish', onCommitFinish as any)
    window.addEventListener('routing-commit-watchdog', onWatchdog as any)
    return () => {
      window.removeEventListener('routing-compute-start', onComputeStart as any)
      window.removeEventListener('routing-compute-finish', onComputeFinish as any)
      window.removeEventListener('routing-commit-start', onCommitStart as any)
      window.removeEventListener('routing-commit-finish', onCommitFinish as any)
      window.removeEventListener('routing-commit-watchdog', onWatchdog as any)
    }
  }, [day.id])

  React.useEffect(() => {
    (async () => {
      try {
        if (autoAttemptedRef.current) return
        if (!hasStartEnd || hasRouteSummary) return
        const { listSavedRoutes: apiList, computeDayRoute, commitDayRoute } = await import('@/lib/api/routing')
        const res = await apiList(day.id)
        if (res.routes && res.routes.length > 0) { autoAttemptedRef.current = true; return }
        // Try compute+commit, retry once on failure
        try {
          const { throttledComputeDayRoute, commitDayRouteWithFallback } = await import('@/lib/api/routing')
          const preview = await throttledComputeDayRoute(day.id, { optimize: true })
          await commitDayRouteWithFallback(day.id, preview.preview_token, 'Default', { optimize: false })
        } catch (e1) {
          await new Promise(r => setTimeout(r, 2000))
          try {
            const preview2 = await throttledComputeDayRoute(day.id, { optimize: true })
            await commitDayRouteWithFallback(day.id, preview2.preview_token, 'Default', { optimize: false })
          } catch (e2: any) {
            toast({ title: 'Could not auto-create route', description: 'Click Manage routes to generate it manually.', variant: 'destructive' })
          }
        }
        // After success attempt, fetch summary and dispatch mini-refresh
        try {
          const { getDaysSummary } = await import('@/lib/api/days')
          const summary = await getDaysSummary(day.trip_id)
          if (summary.data) {
            const loc = summary.data.locations.find((l: any) => l.day_id === day.id)
            if (loc) {
              window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId: day.id, loc } }))
            }
          }
        } catch {}
      } finally {
        autoAttemptedRef.current = true
      }
    })()
  }, [hasStartEnd, hasRouteSummary, day.id, day.trip_id])

  React.useEffect(() => {
    // Load for quick switch buttons only when route summary is missing (to avoid extra API calls)
    if (hasRouteSummary) return
    (async () => {
      try {
        const { listSavedRoutes: apiList } = await import('@/lib/api/routing')
        const res = await apiList(day.id)
        const routes = res.routes || []
        const top = routes.slice(0, 3).map(r => ({ id: r.id, name: r.name || `Version ${r.version}` }))
        setQuickRoutes(top)
      } catch {}
    })()
  }, [day.id, hasRouteSummary])



  const displayDate = getDayDisplayDate(day, { format: 'medium', showYear: false });
  const dateWithWeekday = getDayDateWithWeekday(day);
  const relativeDay = day.calculated_date ? getRelativeDayDescription(new Date(day.calculated_date)) : null;
  const timeStatus = getDayTimeStatus(day);

  const handleCardClick = () => {
    if (onClick) {
      onClick(day);
    }
  };

  const getTimeStatusColor = () => {
    switch (timeStatus) {
      case 'past': return 'text-gray-500';
      case 'present': return 'text-blue-600 font-semibold';
      case 'future': return 'text-gray-900';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card
      className={`transition-all duration-200 hover:shadow-md ${
        onClick ? 'cursor-pointer hover:bg-gray-50' : ''
      } ${className}`}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <span className="font-semibold text-lg">Day {day.seq}</span>
            </div>

            {day.rest_day && (
              <Badge variant="secondary" className="flex items-center space-x-1">
                <Moon className="h-3 w-3" />
                <span>Rest Day</span>
              </Badge>
            )}

            {day.status === 'inactive' && (
              <Badge variant="outline">Inactive</Badge>
            )}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onEditLocations && (
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEditLocations(day); }}>
                  <Route className="mr-2 h-4 w-4" />
                  Edit Locations
                </DropdownMenuItem>
              )}
              {onEdit && (
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEdit(day); }}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Day
                </DropdownMenuItem>
              )}
              {onToggleRestDay && (
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onToggleRestDay(day); }}>
                  <Moon className="mr-2 h-4 w-4" />
                  {day.rest_day ? 'Remove Rest Day' : 'Mark as Rest Day'}
                </DropdownMenuItem>
              )}
              {(onEditLocations || onEdit) && onDelete && <DropdownMenuSeparator />}
              {onDelete && (
                <DropdownMenuItem
                  onClick={(e) => { e.stopPropagation(); onDelete(day); }}
                  className="text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Day
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3">
          {/* Date Information */}
          <div className="space-y-1">
            {displayDate ? (
              <>
                <p className={`text-sm font-medium ${getTimeStatusColor()}`}>
                  {dateWithWeekday}
                </p>
                {relativeDay && (
                  <p className="text-xs text-gray-500">
                    {relativeDay}
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-500 italic">
                No date set for trip
              </p>
            )}
          </div>

          {/* Notes Preview */}
          {day.notes && Object.keys(day.notes).length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Notes</p>
              <div className="text-sm text-gray-700">
                {day.notes.description && (
                  <p className="line-clamp-2">{day.notes.description}</p>
                )}
                {day.notes.activities && Array.isArray(day.notes.activities) && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {day.notes.activities.slice(0, 3).map((activity: string, index: number) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {activity}
                      </Badge>
                    ))}
                    {day.notes.activities.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{day.notes.activities.length - 3} more
                {startLocation && endLocation && !hasRouteSummary && (
                  <div className="text-[11px] text-blue-600">Compute running…</div>
                )}

                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Location Information with mini map preview */}
          <div className="space-y-2">
            {startLocation || endLocation ? (
              <>
                <LazyMapPreview
                  start={startLocation || undefined}
                  end={endLocation || undefined}
                  waypoints={[]}
                  routeCoordinates={routeCoordinates || undefined}
                  height={140}
                  className="rounded-md overflow-hidden"
                  overlayText={mapOverlayText || undefined}
                  extraMarkers={mapExtraMarkers}
                  interactive={false}
                />
                {(startLocation && endLocation) && (hasRouteSummary ? (
                  <div className="flex items-center justify-between mt-1">
                    <div className="text-xs text-gray-600">
                      {Math.round(routeKm!)} km • {Math.floor(routeMin! / 60)}h {Math.round(routeMin! % 60)}m
                      {routingBusy && <span className="ml-2 text-[10px] text-blue-600">Updating route…</span>}
                    </div>
                    <div className="flex items-center gap-3">
                      <UpdateRouteButton dayId={day.id} />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between mt-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] text-gray-500" title="Routing unavailable or still computing">
                        {startLocation && endLocation ? (routingBusy ? 'Updating route…' : 'Computing route…') : 'Routing unavailable'}
                      </Badge>
                      {quickRoutes.length > 0 && (
                        <div className="flex items-center gap-1">
                          {quickRoutes.map(q => (
                            <button key={q.id} className="text-[11px] text-blue-600 hover:underline" onClick={async (e) => {
                              e.stopPropagation();
                              try { await activateRouteVersion(day.id, q.id) } catch {}
                            }}>{q.name}</button>
                          ))}
                        </div>
                      )}
                      <button className="text-[11px] text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); setShowRoutes(true); }}>Manage routes</button>
                    </div>
                    <div className="flex items-center gap-3">
                      <RecomputeRouteButton dayId={day.id} />
                      <UpdateRouteButton dayId={day.id} />
                    </div>
                  </div>
                ))}
                <div className="space-y-1">
                  {startLocation && (
                    <div className="flex items-center space-x-2 text-sm">
                      <Navigation className="h-3 w-3 text-green-600 flex-shrink-0" />
                      <span className="text-gray-600 text-xs">Start:</span>
                      {startLocation.address && (
                        <span className="font-medium text-gray-900 truncate">
                          {formatShortAddress(startLocation, { showCountry: showCountrySuffix })}
                        </span>
                      )}
                    </div>
                  )}
                  {endLocation && (
                    <div className="flex items-center space-x-2 text-sm">
                      <MapPin className="h-3 w-3 text-red-600 flex-shrink-0" />
                      <span className="text-gray-600 text-xs">End:</span>
                      {endLocation.address && (
                        <span className="font-medium text-gray-900 truncate">
                          {formatShortAddress(endLocation, { showCountry: showCountrySuffix })}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Route className="h-3 w-3" />
                <span>No locations set</span>
                {onEditLocations && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => { e.stopPropagation(); onEditLocations(day); }}
                    className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700"
                  >
                    Add locations
                  </Button>
                )}
              </div>
            )}

            {/* Stops count */}
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <MapPin className="h-3 w-3" />
                <span>{stopsCount} stops</span>
              </div>
            </div>
          </div>
      <ManageDayRoutesDialog dayId={day.id} open={showRoutes} onOpenChange={setShowRoutes} onRoutesChanged={async (rv) => {
  // Prefer using returned routeVersion to avoid refetching
  if (rv && (rv.geojson || (typeof rv.total_km === 'number'))) {
    const loc = {
      start: startLocation || null,
      end: endLocation || null,
      route_total_km: rv.total_km ?? undefined,
      route_total_min: rv.total_min ?? undefined,
      route_coordinates: (rv as any).geojson?.coordinates ?? undefined,
    }
    window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId: day.id, loc, routeVersion: rv } }))
    return
  }
  // Use new lightweight per-day summary instead of full trip summary
  try {
    const { getDayActiveSummary } = await import('@/lib/api/routing')
    const s = await getDayActiveSummary(day.id)
    const loc = {
      start: s.start || null,
      end: s.end || null,
      route_total_km: s.route_total_km ?? undefined,
      route_total_min: s.route_total_min ?? undefined,
      route_coordinates: s.route_coordinates ?? undefined,
    }
    window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId: day.id, loc } }))
  } catch {}
}} />
        </div>
      </CardContent>
    </Card>
  );
}
