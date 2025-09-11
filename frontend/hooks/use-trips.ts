/**
 * Trip Management Hook
 *
 * Simple hook for managing trip data and operations
 */

'use client'

import { useState, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Trip, TripListResponse } from '@/types/trip'
import { listTripsEnhanced, deleteTrip as deleteTrip } from '@/lib/api/trips'


export const useTrips = () => {
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTrips = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await listTripsEnhanced()
      console.log('useTrips: Received response:', response)

      if (response.success && response.data) {
        // The API returns { data: Trip[], meta: any, links: any }
        const trips = response.data.data || []
        console.log('useTrips: Setting trips:', trips)
        setTrips(trips)
      } else {
        console.error('useTrips: Failed to fetch trips:', response.error)
        setError(response.error?.message || 'Failed to fetch trips')
        setTrips([])
      }
    } catch (error) {
      console.error('useTrips: Error fetching trips:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch trips')
      setTrips([])
    } finally {
      setLoading(false)
    }
  }, []) // No dependencies to prevent infinite loop

  const handleDeleteTrip = useCallback(async (tripId: string) => {
    try {
      await deleteTrip(tripId)
      setTrips(prev => prev.filter(trip => trip.id !== tripId))
    } catch (error) {
      console.error('Error deleting trip:', error)
      throw error
    }
  }, [])

  useEffect(() => {
    fetchTrips()
  }, [fetchTrips])

  return {
    trips,
    loading,
    error,
    fetchTrips,
    deleteTrip: handleDeleteTrip
  }
}

// Simple auth hook
export const useAuth = () => {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    try {
      const token = localStorage.getItem('auth_token')
      const userData = localStorage.getItem('user_data')

      if (token && userData) {
        setUser(JSON.parse(userData))
      }
    } catch (error) {
      console.error('Error parsing user data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    setUser(null)
    router.push('/login')
  }, [router])

  return {
    user,
    loading,
    isAuthenticated: !!user,
    logout
  }
}
