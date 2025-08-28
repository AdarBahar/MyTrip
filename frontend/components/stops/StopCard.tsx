/**
 * StopCard Component
 * 
 * Displays a single stop with all its details and actions
 */

import React, { useState } from 'react';
import { DraggableProvidedDragHandleProps } from '@hello-pangea/dnd';
import {
  GripVertical, MapPin, Clock, DollarSign, Star, Edit, Trash2,
  Phone, Globe, Calendar, AlertCircle, CheckCircle
} from 'lucide-react';
import { StopWithPlace, deleteStop, updateStop } from '../../lib/api/stops';
import { getStopTypeInfo, getStopPriorityInfo } from '../../lib/constants/stopTypes';
import { formatStopTime, formatStopDuration } from '../../lib/api/stops';
import { formatAddress, formatShortAddress } from '../../lib/api/places';
import { useDebug } from '../../lib/debug';

interface StopCardProps {
  stop: StopWithPlace;
  tripId: string;
  dayId: string;
  dragHandleProps?: DraggableProvidedDragHandleProps;
  onUpdate?: () => void;
  onDelete?: () => void;
  className?: string;
}

export default function StopCard({
  stop,
  tripId,
  dayId,
  dragHandleProps,
  onUpdate,
  onDelete,
  className = ''
}: StopCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [togglingFixed, setTogglingFixed] = useState(false);
  
  const debug = useDebug();
  const typeInfo = getStopTypeInfo(stop.stop_type);
  const priorityInfo = getStopPriorityInfo(stop.priority);

  // Handle delete
  const handleDelete = async () => {
    try {
      setDeleting(true);
      debug.log('StopCard', 'Deleting stop', { stopId: stop.id });
      
      await deleteStop(tripId, dayId, stop.id);
      
      debug.log('StopCard', 'Stop deleted successfully');
      onDelete?.();
      
    } catch (err) {
      debug.error('StopCard', 'Failed to delete stop', err);
      // TODO: Show error toast
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  // Get display name
  const displayName = stop.place?.name || 'Unnamed Location';
  // Prefer normalized.display_short
  const normalizedShort = (stop.place?.meta as any)?.normalized?.display_short as string | undefined;
  const displayAddress = normalizedShort || (stop.place?.address ? formatShortAddress(stop.place!, { showCountry: true }) : '');

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow ${className}`}>
      {/* Main Content */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Drag Handle */}
          <div
            {...dragHandleProps}
            className="flex-shrink-0 mt-1 p-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
          >
            <GripVertical className="w-4 h-4" />
          </div>

          {/* Stop Type Icon */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${typeInfo.bgColor} flex items-center justify-center`}>
            <MapPin className={`w-5 h-5 ${typeInfo.textColor}`} />
          </div>

          {/* Main Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate">
                  {displayName}
                </h4>
                {displayAddress && (
                  <p className="text-sm text-gray-600 truncate mt-1">
                    {displayAddress}
                  </p>
                )}
                
                {/* Type and Priority */}
                <div className="flex items-center gap-3 mt-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${typeInfo.bgColor} ${typeInfo.textColor}`}>
                    {typeInfo.label}
                  </span>

                  {stop.priority !== 3 && (
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${priorityInfo.bgColor} ${priorityInfo.textColor}`}>
                      {priorityInfo.label}
                    </span>
                  )}

                  <span className="text-xs text-gray-500">#{stop.seq}</span>

                  {/* Fixed toggle (VIA only) */}
                  {stop.kind === 'via' ? (
                    <label className="flex items-center gap-1 text-xs text-gray-600 select-none">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300"
                        checked={!!stop.fixed}
                        disabled={togglingFixed}
                        onChange={async () => {
                          try {
                            setTogglingFixed(true);
                            await updateStop(tripId, dayId, stop.id, { fixed: !stop.fixed });
                            onUpdate?.();
                          } catch (e) {
                            console.error('Failed to toggle fixed', e);
                          } finally {
                            setTogglingFixed(false);
                          }
                        }}
                      />
                      <span className={stop.fixed ? 'font-semibold text-blue-700' : ''}>Fixed</span>
                    </label>
                  ) : (
                    <span className="text-[11px] text-gray-400" title="Start/End are fixed anchors">Fixed</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 ml-2">
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  title="Toggle details"
                >
                  <Clock className="w-4 h-4" />
                </button>
                
                <button
                  onClick={() => onUpdate?.()}
                  className="p-1 text-gray-400 hover:text-blue-600 rounded"
                  title="Edit stop"
                >
                  <Edit className="w-4 h-4" />
                </button>
                
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="p-1 text-gray-400 hover:text-red-600 rounded"
                  title="Delete stop"
                  disabled={deleting}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Quick Info */}
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
              {stop.arrival_time && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatStopTime(stop.arrival_time)}</span>
                </div>
              )}
              
              {stop.duration_minutes && (
                <div className="flex items-center gap-1">
                  <Star className="w-3 h-3" />
                  <span>{formatStopDuration(stop.duration_minutes)}</span>
                </div>
              )}
              
              {stop.cost_info?.estimated && (
                <div className="flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  <span>${stop.cost_info.estimated}</span>
                </div>
              )}
            </div>

            {/* Notes Preview */}
            {stop.notes && (
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                {stop.notes}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {showDetails && (
        <div className="border-t border-gray-100 p-4 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Timing */}
            {(stop.arrival_time || stop.departure_time || stop.duration_minutes) && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Timing</h5>
                <div className="space-y-1 text-sm">
                  {stop.arrival_time && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Arrival:</span>
                      <span>{formatStopTime(stop.arrival_time)}</span>
                    </div>
                  )}
                  {stop.departure_time && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Departure:</span>
                      <span>{formatStopTime(stop.departure_time)}</span>
                    </div>
                  )}
                  {stop.duration_minutes && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Duration:</span>
                      <span>{formatStopDuration(stop.duration_minutes)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Contact Info */}
            {stop.contact_info && Object.keys(stop.contact_info).length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Contact</h5>
                <div className="space-y-1 text-sm">
                  {stop.contact_info.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-3 h-3 text-gray-400" />
                      <a href={`tel:${stop.contact_info.phone}`} className="text-blue-600 hover:underline">
                        {stop.contact_info.phone}
                      </a>
                    </div>
                  )}
                  {stop.contact_info.website && (
                    <div className="flex items-center gap-2">
                      <Globe className="w-3 h-3 text-gray-400" />
                      <a href={stop.contact_info.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        Website
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Booking Info */}
            {stop.booking_info && Object.keys(stop.booking_info).length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Booking</h5>
                <div className="space-y-1 text-sm">
                  {stop.booking_info.confirmation && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Confirmation:</span>
                      <span className="font-mono">{stop.booking_info.confirmation}</span>
                    </div>
                  )}
                  {stop.booking_info.status && (
                    <div className="flex items-center gap-2">
                      {stop.booking_info.status === 'confirmed' ? (
                        <CheckCircle className="w-3 h-3 text-green-500" />
                      ) : (
                        <AlertCircle className="w-3 h-3 text-yellow-500" />
                      )}
                      <span className="capitalize">{stop.booking_info.status}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Cost Info */}
            {stop.cost_info && Object.keys(stop.cost_info).length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Cost</h5>
                <div className="space-y-1 text-sm">
                  {stop.cost_info.estimated && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estimated:</span>
                      <span>${stop.cost_info.estimated}</span>
                    </div>
                  )}
                  {stop.cost_info.actual && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Actual:</span>
                      <span>${stop.cost_info.actual}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Full Notes */}
          {stop.notes && (
            <div className="mt-4">
              <h5 className="font-medium text-gray-900 mb-2">Notes</h5>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">
                {stop.notes}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="border-t border-gray-100 p-4 bg-red-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-800">Delete this stop?</p>
              <p className="text-xs text-red-600">This action cannot be undone.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
