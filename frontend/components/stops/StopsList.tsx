/**
 * StopsList Component
 * 
 * Displays a list of stops for a specific day with drag-and-drop reordering
 */

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Plus, MapPin, Clock, DollarSign, Star } from 'lucide-react';
import { Stop, StopWithPlace, listStops, reorderStops } from '../../lib/api/stops';
import { computeDayRoute, commitDayRoute, type RoutePreview } from '@/lib/api/routing';
import { getStopTypeInfo, getStopPriorityInfo, StopType, StopPriority } from '../../lib/constants/stopTypes';
import { formatStopTime, formatStopDuration } from '../../lib/api/stops';
import { formatAddress } from '../../lib/api/places';
import StopCard from './StopCard';
import AddStopModal from './AddStopModal';
import { useDebug } from '../../lib/debug';

interface StopsListProps {
  tripId: string;
  dayId: string;
  dayName?: string;
  onStopUpdate?: () => void;
  className?: string;
}

export default function StopsList({
  tripId,
  dayId,
  dayName,
  onStopUpdate,
  className = ''
}: StopsListProps) {
  const [stops, setStops] = useState<StopWithPlace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [reordering, setReordering] = useState(false);
  const [filterType, setFilterType] = useState<StopType | 'all'>('all');
  const [routePreview, setRoutePreview] = useState<RoutePreview | null>(null);
  const [computingRoute, setComputingRoute] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  
  const debug = useDebug();

  // Load stops
  const loadStops = async () => {
    try {
      setLoading(true);
      setError(null);
      
      debug.log('StopsList', 'Loading stops', { tripId, dayId, filterType });
      
      const response = await listStops(tripId, dayId, {
        includePlaces: true,
        stopType: filterType === 'all' ? undefined : filterType
      });
      
      setStops(response.stops as StopWithPlace[]);
      debug.log('StopsList', 'Stops loaded', { count: response.stops.length });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load stops';
      setError(errorMessage);
      debug.error('StopsList', 'Failed to load stops', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStops();
  }, [tripId, dayId, filterType]);

  // Handle drag and drop reordering
  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;

    const sourceIndex = result.source.index;
    const destinationIndex = result.destination.index;

    if (sourceIndex === destinationIndex) return;

    try {
      setReordering(true);
      debug.log('StopsList', 'Reordering stops', { sourceIndex, destinationIndex });

      // Optimistically update UI
      const newStops = Array.from(stops);
      const [reorderedStop] = newStops.splice(sourceIndex, 1);
      newStops.splice(destinationIndex, 0, reorderedStop);

      // Update sequence numbers
      const reorders = newStops.map((stop, index) => ({
        stop_id: stop.id,
        new_seq: index + 1
      }));

      setStops(newStops);

      // Send to API
      await reorderStops(tripId, dayId, reorders);
      
      debug.log('StopsList', 'Stops reordered successfully');
      onStopUpdate?.();

    } catch (err) {
      debug.error('StopsList', 'Failed to reorder stops', err);
      // Revert optimistic update
      loadStops();
    } finally {
      setReordering(false);
    }
  };

  // Handle stop added
  const handleStopAdded = () => {
    setShowAddModal(false);
    loadStops();
    onStopUpdate?.();
    // Auto compute preview after add
    void (async () => {
      try { setComputingRoute(true); setRoutePreview(await computeDayRoute(dayId, { optimize: false })); } catch {} finally { setComputingRoute(false); }
    })();
  };

  // Handle stop updated/deleted
  const handleStopChanged = () => {
    loadStops();
    onStopUpdate?.();
    // Auto compute preview after update/delete/toggle-fixed/reorder
    void (async () => {
      try { setComputingRoute(true); setRoutePreview(await computeDayRoute(dayId, { optimize: false })); } catch {} finally { setComputingRoute(false); }
    })();
  };

  // Get unique stop types for filter
  const availableTypes = Array.from(new Set(stops.map(stop => stop.stop_type)));

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Stops</h3>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Stops</h3>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
          <button
            onClick={loadStops}
            className="mt-2 text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            Stops {dayName && `for ${dayName}`}
          </h3>
          <p className="text-sm text-gray-600">
            {stops.length} {stops.length === 1 ? 'stop' : 'stops'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Stop
          </button>
          <button
            onClick={async () => {
              try {
                setComputingRoute(true);
                const preview = await computeDayRoute(dayId, { optimize: false });
                setRoutePreview(preview);
              } catch (err) {
                console.error('Failed to compute route', err);
              } finally {
                setComputingRoute(false);
              }
            }}
            className="px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"
            disabled={computingRoute}
            title="Compute route with current order"
          >
            {computingRoute ? 'Computing…' : 'Recompute Route'}
          </button>
          <button
            onClick={async () => {
              try {
                setOptimizing(true);
                const preview = await computeDayRoute(dayId, { optimize: true });
                setRoutePreview(preview);
              } catch (err) {
                console.error('Failed to optimize route', err);
              } finally {
                setOptimizing(false);
              }
            }}
            className="px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"
            disabled={optimizing}
            title="Find optimized order (respects fixed stops)"
          >
            {optimizing ? 'Optimizing…' : 'Optimize Route'}
          </button>
        </div>
      </div>

      {/* Filters */}
      {availableTypes.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
              filterType === 'all'
                ? 'bg-blue-100 text-blue-800'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All Types
          </button>
          {availableTypes.map(type => {
            const typeInfo = getStopTypeInfo(type);
            return (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
                  filterType === type
                    ? `${typeInfo.bgColor} ${typeInfo.textColor}`
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {typeInfo.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Route preview summary */}
      {routePreview && (
        <div className="p-3 border rounded-lg bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Total: {routePreview.total_km.toFixed(1)} km • {Math.round(routePreview.total_min)} min
            </div>
            <div className="flex gap-2">
              {routePreview.proposed_order && (
                <button
                  onClick={async () => {
                    try {
                      // Reorder stops in DB to match proposed order
                      const newOrderIds = routePreview.proposed_order!
                      const reorders = newOrderIds.map((id, idx) => ({ stop_id: id, new_seq: idx + 1 }))
                      await reorderStops(tripId, dayId, reorders)
                      // Commit the route version
                      await commitDayRoute(dayId, routePreview.preview_token, 'Optimized')
                      setRoutePreview(null)
                      // Refresh list to reflect new order
                      loadStops()
                    } catch (e) { console.error(e) }
                  }}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded-md"
                >
                  Accept Optimized Order
                </button>
              )}
              <button
                onClick={() => setRoutePreview(null)}
                className="px-3 py-1 text-sm border rounded-md"
              >
                Close
              </button>
            </div>
          </div>
          {routePreview.warnings && routePreview.warnings.length > 0 && (
            <div className="mt-2 text-xs text-amber-700">
              {routePreview.warnings.map((w, i) => (
                <div key={i}>⚠️ {w.type} {w.stop_id ? `(stop ${w.stop_id})` : ''} {w.ratio ? `ratio ${w.ratio}` : ''} {w.extra_min ? `+${w.extra_min} min` : ''}</div>
              ))}
            </div>
          )}
          {/* Highlight stops flagged in warnings */}
          {routePreview.warnings && routePreview.warnings.length > 0 && (
            <div className="sr-only" aria-hidden>
              {/* Placeholder to indicate we will visually mark flagged stops below */}
            </div>
          )}
          {routePreview.legs && routePreview.legs.length > 0 && (
            <div className="mt-2 text-xs text-gray-700 grid grid-cols-1 sm:grid-cols-2 gap-1">
              {routePreview.legs.map((leg, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white rounded border">
                  <div>Leg {idx + 1}</div>
                  <div>{leg.distance_km.toFixed(1)} km • {Math.round(leg.duration_min)} min</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stops List */}
      {stops.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">No stops yet</h4>
          <p className="text-gray-600 mb-4">
            Add your first stop to start planning this day
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add First Stop
          </button>
        </div>
      ) : (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="stops-list">
            {(provided, snapshot) => (
              <div
                {...provided.droppableProps}
                ref={provided.innerRef}
                className={`space-y-3 ${
                  snapshot.isDraggingOver ? 'bg-blue-50 rounded-lg p-2' : ''
                }`}
              >
                {stops.map((stop, index) => (
                  <Draggable
                    key={stop.id}
                    draggableId={stop.id}
                    index={index}
                    isDragDisabled={reordering}
                  >
                    {(provided, snapshot) => {
                      const flaggedStopIds = new Set((routePreview?.warnings || []).filter(w => w.stop_id).map(w => w.stop_id as string))
                      const isFlagged = flaggedStopIds.has(stop.id)
                      return (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          className={`${snapshot.isDragging ? 'shadow-lg' : ''} ${isFlagged ? 'ring-2 ring-amber-400 rounded-md' : ''}`}
                        >
                          <StopCard
                            stop={stop}
                            tripId={tripId}
                            dayId={dayId}
                            dragHandleProps={provided.dragHandleProps}
                            onUpdate={handleStopChanged}
                            onDelete={handleStopChanged}
                          />
                        </div>
                      )
                    }}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      )}

      {/* Add Stop Modal */}
      {showAddModal && (
        <AddStopModal
          tripId={tripId}
          dayId={dayId}
          existingStops={stops}
          onClose={() => setShowAddModal(false)}
          onStopAdded={handleStopAdded}
        />
      )}
    </div>
  );
}
