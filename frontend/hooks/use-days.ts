/**
 * React hooks for day management
 */

import { useState, useEffect, useCallback } from 'react';
import { Day, DayList, DayCreate, DayUpdate } from '@/types';
import * as daysApi from '@/lib/api/days';
import { sortDaysBySequence } from '@/lib/date-utils';

export interface UseDaysOptions {
  tripId: string;
  includeStops?: boolean;
  autoRefresh?: boolean;
}

export interface UseDaysReturn {
  days: Day[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createDay: (dayData: DayCreate) => Promise<Day | null>;
  updateDay: (dayId: string, dayData: DayUpdate) => Promise<Day | null>;
  deleteDay: (dayId: string) => Promise<boolean>;
  toggleRestDay: (dayId: string) => Promise<Day | null>;
  addNotes: (dayId: string, notes: Record<string, any>) => Promise<Day | null>;
}

/**
 * Hook for managing days in a trip
 */
export function useDays({ tripId, includeStops = false, autoRefresh = true }: UseDaysOptions): UseDaysReturn {
  const [days, setDays] = useState<Day[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDays = useCallback(async () => {
    if (!tripId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await daysApi.listDays(tripId, includeStops);
      
      if (response.error) {
        setError(response.error);
        setDays([]);
      } else if (response.data) {
        const sortedDays = sortDaysBySequence(response.data.days);
        setDays(sortedDays);
      }
    } catch (err) {
      setError(`Failed to fetch days: ${err}`);
      setDays([]);
    } finally {
      setLoading(false);
    }
  }, [tripId, includeStops]);

  const createDay = useCallback(async (dayData: DayCreate): Promise<Day | null> => {
    try {
      const response = await daysApi.createDay(tripId, dayData);
      
      if (response.error) {
        setError(response.error);
        return null;
      }
      
      if (response.data) {
        // Add the new day to the list and sort
        setDays(prevDays => sortDaysBySequence([...prevDays, response.data!]));
        return response.data;
      }
      
      return null;
    } catch (err) {
      setError(`Failed to create day: ${err}`);
      return null;
    }
  }, [tripId]);

  const updateDay = useCallback(async (dayId: string, dayData: DayUpdate): Promise<Day | null> => {
    try {
      const response = await daysApi.updateDay(tripId, dayId, dayData);
      
      if (response.error) {
        setError(response.error);
        return null;
      }
      
      if (response.data) {
        // Update the day in the list
        setDays(prevDays => {
          const updatedDays = prevDays.map(day => 
            day.id === dayId ? response.data! : day
          );
          return sortDaysBySequence(updatedDays);
        });
        return response.data;
      }
      
      return null;
    } catch (err) {
      setError(`Failed to update day: ${err}`);
      return null;
    }
  }, [tripId]);

  const deleteDay = useCallback(async (dayId: string): Promise<boolean> => {
    try {
      const response = await daysApi.deleteDay(tripId, dayId);
      
      if (response.error) {
        setError(response.error);
        return false;
      }
      
      // Remove the day from the list
      setDays(prevDays => prevDays.filter(day => day.id !== dayId));
      return true;
    } catch (err) {
      setError(`Failed to delete day: ${err}`);
      return false;
    }
  }, [tripId]);

  const toggleRestDay = useCallback(async (dayId: string): Promise<Day | null> => {
    try {
      const response = await daysApi.toggleRestDay(tripId, dayId);
      
      if (response.error) {
        setError(response.error);
        return null;
      }
      
      if (response.data) {
        // Update the day in the list
        setDays(prevDays => 
          prevDays.map(day => 
            day.id === dayId ? response.data! : day
          )
        );
        return response.data;
      }
      
      return null;
    } catch (err) {
      setError(`Failed to toggle rest day: ${err}`);
      return null;
    }
  }, [tripId]);

  const addNotes = useCallback(async (dayId: string, notes: Record<string, any>): Promise<Day | null> => {
    try {
      const response = await daysApi.addDayNotes(tripId, dayId, notes);
      
      if (response.error) {
        setError(response.error);
        return null;
      }
      
      if (response.data) {
        // Update the day in the list
        setDays(prevDays => 
          prevDays.map(day => 
            day.id === dayId ? response.data! : day
          )
        );
        return response.data;
      }
      
      return null;
    } catch (err) {
      setError(`Failed to add notes: ${err}`);
      return null;
    }
  }, [tripId]);

  // Auto-fetch on mount and when dependencies change
  useEffect(() => {
    if (autoRefresh) {
      fetchDays();
    }
  }, [fetchDays, autoRefresh]);

  return {
    days,
    loading,
    error,
    refetch: fetchDays,
    createDay,
    updateDay,
    deleteDay,
    toggleRestDay,
    addNotes
  };
}

/**
 * Hook for managing a single day
 */
export function useDay(tripId: string, dayId: string) {
  const [day, setDay] = useState<Day | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDay = useCallback(async () => {
    if (!tripId || !dayId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await daysApi.getDay(tripId, dayId);
      
      if (response.error) {
        setError(response.error);
        setDay(null);
      } else if (response.data) {
        setDay(response.data);
      }
    } catch (err) {
      setError(`Failed to fetch day: ${err}`);
      setDay(null);
    } finally {
      setLoading(false);
    }
  }, [tripId, dayId]);

  useEffect(() => {
    fetchDay();
  }, [fetchDay]);

  return {
    day,
    loading,
    error,
    refetch: fetchDay
  };
}
