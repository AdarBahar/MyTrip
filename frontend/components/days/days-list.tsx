/**
 * Days List Component
 * Displays a list of days for a trip with management actions
 */

'use client';

import React, { useState } from 'react';
import { Day, Trip } from '@/types';
import { useDays } from '@/hooks/use-days';
import { DayCard } from './day-card';
import { CreateDayDialog } from './create-day-dialog';
import { EditDayDialog } from './edit-day-dialog';
import { DeleteDayDialog } from './delete-day-dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Calendar, AlertCircle } from 'lucide-react';
import { getTripDuration, formatDate } from '@/lib/date-utils';

interface DaysListProps {
  trip: Trip;
  onDayClick?: (day: Day) => void;
  className?: string;
}

export function DaysList({ trip, onDayClick, className = '' }: DaysListProps) {
  const { days, loading, error, createDay, updateDay, deleteDay, toggleRestDay } = useDays({
    tripId: trip.id,
    includeStops: false,
    autoRefresh: true
  });

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingDay, setEditingDay] = useState<Day | null>(null);
  const [deletingDay, setDeletingDay] = useState<Day | null>(null);

  const tripDuration = getTripDuration(trip, days);

  const handleCreateDay = async (dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> }) => {
    const newDay = await createDay(dayData);
    if (newDay) {
      setShowCreateDialog(false);
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
            <DayCard
              key={day.id}
              day={day}
              onClick={onDayClick}
              onEdit={setEditingDay}
              onDelete={setDeletingDay}
              onToggleRestDay={handleToggleRestDay}
            />
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
    </div>
  );
}
