/**
 * Edit Day Dialog Component
 */

'use client';

import React, { useState, useEffect } from 'react';
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
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

const editDaySchema = z.object({
  seq: z.number().min(1, 'Sequence must be at least 1'),
  rest_day: z.boolean(),
  description: z.string().optional(),
  activities: z.string().optional(),
});

type EditDayFormData = z.infer<typeof editDaySchema>;

interface EditDayDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  day: Day;
  onUpdateDay: (dayId: string, dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> }) => Promise<void>;
  existingDays: Day[];
}

export function EditDayDialog({ 
  open, 
  onOpenChange, 
  day,
  onUpdateDay, 
  existingDays 
}: EditDayDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<EditDayFormData>({
    resolver: zodResolver(editDaySchema),
    defaultValues: {
      seq: day.seq,
      rest_day: day.rest_day,
      description: day.notes?.description || '',
      activities: day.notes?.activities ? day.notes.activities.join(', ') : '',
    },
  });

  // Reset form when day changes
  useEffect(() => {
    form.reset({
      seq: day.seq,
      rest_day: day.rest_day,
      description: day.notes?.description || '',
      activities: day.notes?.activities ? day.notes.activities.join(', ') : '',
    });
  }, [day, form]);

  const handleSubmit = async (data: EditDayFormData) => {
    setIsSubmitting(true);
    
    try {
      const dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> } = {
        seq: data.seq,
        rest_day: data.rest_day,
      };

      // Build notes object if there's content
      const notes: Record<string, any> = {};
      if (data.description?.trim()) {
        notes.description = data.description.trim();
      }
      if (data.activities?.trim()) {
        notes.activities = data.activities
          .split(',')
          .map(activity => activity.trim())
          .filter(activity => activity.length > 0);
      }

      if (Object.keys(notes).length > 0) {
        dayData.notes = notes;
      } else {
        dayData.notes = null; // Clear notes if empty
      }

      await onUpdateDay(day.id, dayData);
    } catch (error) {
      console.error('Failed to update day:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    form.reset();
    onOpenChange(false);
  };

  const isSequenceConflict = (seq: number) => {
    return existingDays.some(d => d.id !== day.id && d.seq === seq);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Day {day.seq}</DialogTitle>
          <DialogDescription>
            Update the details for this day in your trip.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="seq"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Day Number</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min="1"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                  {isSequenceConflict(field.value) && (
                    <FormDescription className="text-red-600">
                      Day {field.value} already exists. Choose a different number.
                    </FormDescription>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="rest_day"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                  <div className="space-y-0.5">
                    <FormLabel>Rest Day</FormLabel>
                    <FormDescription>
                      Mark this as a rest day (no driving or major activities).
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="What's planned for this day?"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="activities"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Activities</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Driving, sightseeing, hiking (comma-separated)"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Enter activities separated by commas.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={isSubmitting || isSequenceConflict(form.watch('seq'))}
              >
                {isSubmitting ? 'Updating...' : 'Update Day'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
