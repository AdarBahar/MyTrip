/**
 * Create Day Dialog Component
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

const createDaySchema = z.object({
  seq: z.number().min(1, 'Sequence must be at least 1').optional(),
  rest_day: z.boolean().default(false),
  description: z.string().optional(),
  activities: z.string().optional(),
});

type CreateDayFormData = z.infer<typeof createDaySchema>;

interface CreateDayDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateDay: (dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> }) => Promise<void>;
  existingDays: Day[];
}

export function CreateDayDialog({ 
  open, 
  onOpenChange, 
  onCreateDay, 
  existingDays 
}: CreateDayDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<CreateDayFormData>({
    resolver: zodResolver(createDaySchema),
    defaultValues: {
      rest_day: false,
      description: '',
      activities: '',
    },
  });

  const getNextSequence = () => {
    if (existingDays.length === 0) return 1;
    const maxSeq = Math.max(...existingDays.map(day => day.seq));
    return maxSeq + 1;
  };

  const handleSubmit = async (data: CreateDayFormData) => {
    setIsSubmitting(true);
    
    try {
      const dayData: { seq?: number; rest_day?: boolean; notes?: Record<string, any> } = {
        seq: data.seq || getNextSequence(),
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
      }

      await onCreateDay(dayData);
      
      // Reset form
      form.reset();
    } catch (error) {
      console.error('Failed to create day:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    form.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Day</DialogTitle>
          <DialogDescription>
            Add a new day to your trip. The sequence will be auto-generated if not specified.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="seq"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Day Number (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min="1"
                      placeholder={`Auto-generate (${getNextSequence()})`}
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                      value={field.value || ''}
                    />
                  </FormControl>
                  <FormDescription>
                    Leave empty to auto-generate the next sequence number.
                  </FormDescription>
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
                  <FormLabel>Description (Optional)</FormLabel>
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
                  <FormLabel>Activities (Optional)</FormLabel>
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
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creating...' : 'Create Day'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
