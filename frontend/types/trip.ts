/**
 * Trip Type Definitions
 *
 * Core types for trip-related functionality
 */

export interface TripCreator {
  id: string
  name: string
  email: string
}

export interface Trip {
  id: string
  slug: string
  title: string
  destination?: string
  start_date?: string
  timezone?: string
  status: 'draft' | 'active' | 'completed' | 'archived'
  is_published: boolean
  created_by: string
  created_at: string
  updated_at: string
  deleted_at?: string
  created_by_user?: TripCreator
}

export interface TripListResponse {
  data: Trip[]
  meta?: {
    page: number
    size: number
    total: number
    pages: number
  }
}

export interface TripCardProps {
  trip: Trip
  onDelete: (tripId: string, success: boolean) => void
  onEdit?: (trip: Trip) => void
  loading?: boolean
}

export type TripStatus = Trip['status']
