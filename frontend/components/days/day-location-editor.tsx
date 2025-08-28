/**
 * Day Location Editor Dialog
 * Edit start and end locations for a day
 */

'use client';

import React, { useState, useEffect } from 'react';
import { MapPin, Navigation, Calendar, AlertCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { LocationPicker } from '@/components/places/location-picker';
import { MapPreview } from '@/components/places';
import { Day } from '@/types';
import { Place } from '@/lib/api/places';
import { listStops, type StopWithPlace } from '@/lib/api/stops';
import { formatDate } from '@/lib/date-utils';

interface DayLocationEditorProps {
  day: Day | null;
  tripId: string;
  previousDayEndLocation?: Place | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (...args: any[]) => Promise<void>; // Remove unused param warnings
}

export function DayLocationEditor({
  day,
  tripId,
  previousDayEndLocation,
  open,
  onOpenChange,
  onSave
}: DayLocationEditorProps) {
  const [startLocation, setStartLocation] = useState<Place | null>(null);
  const [endLocation, setEndLocation] = useState<Place | null>(null);
  const [useInheritedStart, setUseInheritedStart] = useState(false);
  const [loading, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when day changes
  useEffect(() => {
    if (day && open) {
      // Load existing stops to populate start/end
      const loadExistingStops = async () => {
        try {
          const response = await listStops(tripId, day.id, { includePlaces: true });
          const stops = response.stops as StopWithPlace[];

          const startStop = stops.find(s => s.kind === 'start');
          const endStop = stops.find(s => s.kind === 'end');

          if (startStop?.place) {
            setStartLocation(startStop.place);
            setUseInheritedStart(false); // explicit start exists
          } else {
            // No explicit start - check inheritance
            const canInherit = !!previousDayEndLocation && day.seq > 1;
            setUseInheritedStart(canInherit);
            setStartLocation(canInherit ? previousDayEndLocation! : null);
          }

          if (endStop?.place) {
            setEndLocation(endStop.place);
          } else {
            setEndLocation(null);
          }
        } catch (err) {
          console.error('Failed to load existing stops:', err);
          // Fallback to inheritance logic
          const canInherit = !!previousDayEndLocation && day.seq > 1;
          setUseInheritedStart(canInherit);
          setStartLocation(canInherit ? previousDayEndLocation! : null);
          setEndLocation(null);
        }
      };

      loadExistingStops();
    }
    setError(null);
  }, [day, tripId, previousDayEndLocation, open]);

  const handleSave = async () => {
    if (!day) return;

    // Validation
    if (day.seq === 1 && !startLocation) {
      setError('Day 1 must have a start location');
      return;
    }

    if (!endLocation) {
      setError('All days must have an end location');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await onSave(day.id, startLocation, endLocation);
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save locations');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
    setError(null);
  };



  if (!day) return null;

  const isDay1 = day.seq === 1;
  const hasPreviousEnd = day.seq > 1 && previousDayEndLocation;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Calendar className="h-5 w-5" />
            <span>Day {day.seq} Locations</span>
            {day.calculated_date && (
              <Badge variant="outline">
                {formatDate(new Date(day.calculated_date))}
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription className="sr-only" id="day-location-desc">
            Edit the start and end locations for this day. Required for trip routing and planning.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Start Location */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="flex items-center space-x-2">
                <Navigation className="h-4 w-4 text-green-600" />
                <span>Start Location</span>
                {isDay1 && <span className="text-red-500">*</span>}
                {!isDay1 && useInheritedStart && (
                  <span className="ml-2 text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">Inherited</span>
                )}
              </Label>

              {hasPreviousEnd && (
                <label className="flex items-center gap-2 text-xs text-gray-700">
                  <input
                    type="checkbox"
                    checked={useInheritedStart}
                    onChange={(e) => {
                      const on = e.target.checked;
                      setUseInheritedStart(on);
                      setStartLocation(on ? previousDayEndLocation || null : null);
                    }}
                  />
                  <span>Use previous day&apos;s end as start</span>
                </label>
              )}
            </div>

            {hasPreviousEnd && useInheritedStart && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Using previous day&apos;s end as start:
                  <strong className="ml-1">{previousDayEndLocation?.name}</strong>
                </AlertDescription>
              </Alert>
            )}

            <LocationPicker
              value={startLocation}
              onChange={(p) => { setStartLocation(p); setUseInheritedStart(false); }}
              placeholder={isDay1 ? "Where does your trip start?" : "Where does this day start?"}
              disabled={loading}
            />

            {!isDay1 && !startLocation && (
              <p className="text-sm text-gray-500">
                Leave empty to continue from the previous day&apos;s end location
              </p>
            )}
          </div>

          {/* End Location */}
          <div className="space-y-3">
            <Label className="flex items-center space-x-2">
              <MapPin className="h-4 w-4 text-red-600" />
              <span>End Location</span>
              <span className="text-red-500">*</span>
            </Label>

            <LocationPicker
              value={endLocation}
              onChange={setEndLocation}
              placeholder="Where does this day end?"
              disabled={loading}
            />

            <p className="text-sm text-gray-500">
              This will be the starting point for Day {day.seq + 1} (if applicable)
            </p>
          </div>

          {/* Map + Location Summary */}
          {(startLocation || endLocation) && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <h4 className="font-medium text-gray-900">Day {day.seq} Route Preview</h4>
              <MapPreview start={startLocation || null} end={endLocation || null} />

              {startLocation && (
                <div className="flex items-center space-x-2 text-sm">
                  <Navigation className="h-3 w-3 text-green-600" />
                  <span className="text-gray-600">Start:</span>
                  <span className="font-medium">{startLocation.name}</span>
                </div>
              )}
              {endLocation && (
                <div className="flex items-center space-x-2 text-sm">
                  <MapPin className="h-3 w-3 text-red-600" />
                  <span className="text-gray-600">End:</span>
                  <span className="font-medium">{endLocation.name}</span>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? 'Saving...' : 'Save Locations'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
