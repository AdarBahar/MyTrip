/**
 * Delete Day Dialog Component
 */

'use client';

import React, { useState } from 'react';
import { Day } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { getDayDisplayDate } from '@/lib/date-utils';

interface DeleteDayDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  day: Day;
  onDeleteDay: (dayId: string) => Promise<void>;
}

export function DeleteDayDialog({ 
  open, 
  onOpenChange, 
  day,
  onDeleteDay
}: DeleteDayDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const displayDate = getDayDisplayDate(day, { format: 'medium' });

  const handleDelete = async () => {
    setIsDeleting(true);
    
    try {
      await onDeleteDay(day.id);
    } catch (error) {
      console.error('Failed to delete day:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <span>Delete Day {day.seq}</span>
          </DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete the day and all associated data.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Warning:</strong> Deleting this day will also remove any stops, routes, and other data associated with it.
            </AlertDescription>
          </Alert>

          <div className="rounded-lg border p-4 bg-gray-50">
            <h4 className="font-medium text-gray-900">Day Details:</h4>
            <div className="mt-2 space-y-1 text-sm text-gray-600">
              <p><strong>Day:</strong> {day.seq}</p>
              {displayDate && <p><strong>Date:</strong> {displayDate}</p>}
              {day.rest_day && <p><strong>Type:</strong> Rest Day</p>}
              {day.notes?.description && (
                <p><strong>Description:</strong> {day.notes.description}</p>
              )}
              {day.notes?.activities && Array.isArray(day.notes.activities) && (
                <p><strong>Activities:</strong> {day.notes.activities.join(', ')}</p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Day'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
