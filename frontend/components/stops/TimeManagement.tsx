/**
 * TimeManagement Component
 * 
 * Handles time scheduling and duration management for stops
 */

import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle, CheckCircle, Calendar } from 'lucide-react';
import { Stop, StopWithPlace } from '../../lib/api/stops';
import { formatStopTime, formatStopDuration, validateStopTimes } from '../../lib/api/stops';

interface TimeManagementProps {
  stops: StopWithPlace[];
  onTimeUpdate?: (stopId: string, timeData: { arrival_time?: string; departure_time?: string; duration_minutes?: number }) => void;
  className?: string;
}

interface TimeConflict {
  stopId: string;
  type: 'overlap' | 'gap' | 'invalid';
  message: string;
}

export default function TimeManagement({
  stops,
  onTimeUpdate,
  className = ''
}: TimeManagementProps) {
  const [conflicts, setConflicts] = useState<TimeConflict[]>([]);
  const [totalDuration, setTotalDuration] = useState(0);
  const [dayStartTime, setDayStartTime] = useState('');
  const [dayEndTime, setDayEndTime] = useState('');

  // Calculate conflicts and statistics
  useEffect(() => {
    const newConflicts: TimeConflict[] = [];
    let duration = 0;

    // Sort stops by sequence
    const sortedStops = [...stops].sort((a, b) => a.seq - b.seq);

    for (let i = 0; i < sortedStops.length; i++) {
      const stop = sortedStops[i];
      
      // Add to total duration
      if (stop.duration_minutes) {
        duration += stop.duration_minutes;
      }

      // Check time validity
      if (stop.arrival_time && stop.departure_time) {
        const timeValidation = validateStopTimes(stop.arrival_time, stop.departure_time);
        if (!timeValidation.isValid) {
          newConflicts.push({
            stopId: stop.id,
            type: 'invalid',
            message: timeValidation.error || 'Invalid time range'
          });
        }
      }

      // Check for overlaps with next stop
      if (i < sortedStops.length - 1) {
        const nextStop = sortedStops[i + 1];
        
        if (stop.departure_time && nextStop.arrival_time) {
          const currentDeparture = new Date(`1970-01-01T${stop.departure_time}`);
          const nextArrival = new Date(`1970-01-01T${nextStop.arrival_time}`);
          
          if (currentDeparture > nextArrival) {
            newConflicts.push({
              stopId: nextStop.id,
              type: 'overlap',
              message: `Overlaps with previous stop departure time`
            });
          }
        }
      }
    }

    setConflicts(newConflicts);
    setTotalDuration(duration);

    // Calculate day start/end times
    const timesWithStops = sortedStops.filter(s => s.arrival_time || s.departure_time);
    if (timesWithStops.length > 0) {
      const firstStop = timesWithStops[0];
      const lastStop = timesWithStops[timesWithStops.length - 1];
      
      if (firstStop.arrival_time) {
        setDayStartTime(firstStop.arrival_time);
      }
      
      if (lastStop.departure_time) {
        setDayEndTime(lastStop.departure_time);
      }
    }
  }, [stops]);

  // Get conflict for a specific stop
  const getStopConflict = (stopId: string): TimeConflict | undefined => {
    return conflicts.find(c => c.stopId === stopId);
  };

  // Calculate suggested times based on duration and previous stop
  const getSuggestedTimes = (stop: StopWithPlace, previousStop?: StopWithPlace) => {
    if (!stop.duration_minutes) return null;

    let suggestedArrival = '';
    let suggestedDeparture = '';

    if (previousStop?.departure_time) {
      // Start 30 minutes after previous stop departure (travel time)
      const prevDeparture = new Date(`1970-01-01T${previousStop.departure_time}`);
      const arrival = new Date(prevDeparture.getTime() + 30 * 60 * 1000);
      suggestedArrival = arrival.toTimeString().slice(0, 5);
    } else if (!stop.arrival_time) {
      // Default to 9:00 AM if no previous stop
      suggestedArrival = '09:00';
    }

    if (suggestedArrival || stop.arrival_time) {
      const arrivalTime = suggestedArrival || stop.arrival_time!;
      const arrival = new Date(`1970-01-01T${arrivalTime}`);
      const departure = new Date(arrival.getTime() + stop.duration_minutes * 60 * 1000);
      suggestedDeparture = departure.toTimeString().slice(0, 5);
    }

    return {
      arrival: suggestedArrival,
      departure: suggestedDeparture
    };
  };

  // Auto-schedule all stops
  const handleAutoSchedule = () => {
    const sortedStops = [...stops].sort((a, b) => a.seq - b.seq);
    let currentTime = new Date(`1970-01-01T09:00:00`); // Start at 9 AM

    sortedStops.forEach((stop, index) => {
      if (index > 0) {
        // Add 30 minutes travel time between stops
        currentTime = new Date(currentTime.getTime() + 30 * 60 * 1000);
      }

      const arrivalTime = currentTime.toTimeString().slice(0, 5);
      
      // Calculate departure time based on duration
      const duration = stop.duration_minutes || 60; // Default 1 hour
      const departureTime = new Date(currentTime.getTime() + duration * 60 * 1000);
      const departure = departureTime.toTimeString().slice(0, 5);

      onTimeUpdate?.(stop.id, {
        arrival_time: arrivalTime,
        departure_time: departure,
        duration_minutes: duration
      });

      currentTime = departureTime;
    });
  };

  // Calculate total day time
  const getTotalDayTime = (): string => {
    if (!dayStartTime || !dayEndTime) return '';
    
    const start = new Date(`1970-01-01T${dayStartTime}`);
    const end = new Date(`1970-01-01T${dayEndTime}`);
    const diffMs = end.getTime() - start.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    return formatStopDuration(diffMinutes);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Day Schedule Summary
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Total Stops:</span>
            <div className="font-medium">{stops.length}</div>
          </div>
          
          <div>
            <span className="text-gray-600">Total Duration:</span>
            <div className="font-medium">{formatStopDuration(totalDuration)}</div>
          </div>
          
          {dayStartTime && (
            <div>
              <span className="text-gray-600">Day Start:</span>
              <div className="font-medium">{formatStopTime(dayStartTime)}</div>
            </div>
          )}
          
          {dayEndTime && (
            <div>
              <span className="text-gray-600">Day End:</span>
              <div className="font-medium">{formatStopTime(dayEndTime)}</div>
            </div>
          )}
        </div>

        {dayStartTime && dayEndTime && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <span className="text-gray-600 text-sm">Total Day Time:</span>
            <span className="font-medium ml-2">{getTotalDayTime()}</span>
          </div>
        )}

        {/* Auto-schedule button */}
        <div className="mt-4 flex justify-end">
          <button
            onClick={handleAutoSchedule}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            Auto-Schedule All Stops
          </button>
        </div>
      </div>

      {/* Conflicts */}
      {conflicts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Time Conflicts ({conflicts.length})
          </h4>
          <div className="space-y-2">
            {conflicts.map((conflict, index) => {
              const stop = stops.find(s => s.id === conflict.stopId);
              return (
                <div key={index} className="text-sm text-yellow-700">
                  <span className="font-medium">
                    {stop?.place?.name || 'Unknown Stop'}:
                  </span>
                  <span className="ml-1">{conflict.message}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Individual Stop Times */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900">Stop Times</h4>
        
        {stops
          .sort((a, b) => a.seq - b.seq)
          .map((stop, index) => {
            const conflict = getStopConflict(stop.id);
            const previousStop = index > 0 ? stops.find(s => s.seq === stop.seq - 1) : undefined;
            const suggested = getSuggestedTimes(stop, previousStop);
            
            return (
              <div
                key={stop.id}
                className={`border rounded-lg p-4 ${
                  conflict ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h5 className="font-medium text-gray-900">
                      #{stop.seq} {stop.place?.name || 'Unnamed Location'}
                    </h5>
                    {conflict && (
                      <p className="text-sm text-yellow-700 mt-1">
                        {conflict.message}
                      </p>
                    )}
                  </div>
                  
                  {!conflict && (
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-1" />
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Arrival Time
                    </label>
                    <input
                      type="time"
                      value={stop.arrival_time || ''}
                      onChange={(e) => onTimeUpdate?.(stop.id, { arrival_time: e.target.value })}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                    />
                    {suggested?.arrival && !stop.arrival_time && (
                      <button
                        onClick={() => onTimeUpdate?.(stop.id, { arrival_time: suggested.arrival })}
                        className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                      >
                        Use suggested: {formatStopTime(suggested.arrival)}
                      </button>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Departure Time
                    </label>
                    <input
                      type="time"
                      value={stop.departure_time || ''}
                      onChange={(e) => onTimeUpdate?.(stop.id, { departure_time: e.target.value })}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                    />
                    {suggested?.departure && !stop.departure_time && (
                      <button
                        onClick={() => onTimeUpdate?.(stop.id, { departure_time: suggested.departure })}
                        className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                      >
                        Use suggested: {formatStopTime(suggested.departure)}
                      </button>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Duration (minutes)
                    </label>
                    <input
                      type="number"
                      value={stop.duration_minutes || ''}
                      onChange={(e) => onTimeUpdate?.(stop.id, { duration_minutes: parseInt(e.target.value) || undefined })}
                      placeholder="60"
                      min="1"
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Current times display */}
                {(stop.arrival_time || stop.departure_time || stop.duration_minutes) && (
                  <div className="mt-3 pt-3 border-t border-gray-200 text-sm text-gray-600">
                    {stop.arrival_time && (
                      <span>Arrives: {formatStopTime(stop.arrival_time)}</span>
                    )}
                    {stop.arrival_time && stop.departure_time && <span className="mx-2">•</span>}
                    {stop.departure_time && (
                      <span>Departs: {formatStopTime(stop.departure_time)}</span>
                    )}
                    {stop.duration_minutes && (
                      <span className="ml-2">({formatStopDuration(stop.duration_minutes)})</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
