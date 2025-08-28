/**
 * Type definitions for the MyTrip application
 */

export type TripStatus = 'draft' | 'active' | 'completed' | 'archived';

export type DayStatus = 'active' | 'inactive';

export interface Trip {
  id: string;
  slug: string;
  title: string;
  destination: string;
  start_date: string | null; // ISO date string or null
  timezone: string;
  status: TripStatus;
  is_published: boolean;
  created_by: string;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Day {
  id: string;
  trip_id: string;
  seq: number;
  status: DayStatus;
  rest_day: boolean;
  notes: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  
  // Computed fields from API
  trip_start_date: string | null; // ISO date string or null
  calculated_date: string | null; // ISO date string or null
}

export interface DayWithStops extends Day {
  stops_count: number;
  has_route: boolean;
}

export interface DayList {
  days: Day[];
  total: number;
  trip_id: string;
}

export interface DayListWithStops {
  days: DayWithStops[];
  total: number;
  trip_id: string;
}

export interface DayCreate {
  seq?: number;
  status?: DayStatus;
  rest_day?: boolean;
  notes?: Record<string, any> | null;
}

export interface DayUpdate {
  seq?: number;
  status?: DayStatus;
  rest_day?: boolean;
  notes?: Record<string, any> | null;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Date utility types
export interface DateDisplayOptions {
  format?: 'short' | 'medium' | 'long' | 'full';
  showWeekday?: boolean;
  showYear?: boolean;
  fallback?: string;
}

export interface DayDateInfo {
  day: Day;
  displayDate: string | null;
  isCalculated: boolean;
  dayOfWeek: string | null;
  relativeDay: string | null; // "Today", "Tomorrow", "In 3 days", etc.
}
