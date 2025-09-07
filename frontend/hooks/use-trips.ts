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
import { useAPIResponseHandler } from '@/components/ui/error-display'

export const useTrips = () => {
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(false)
  const { handleResponse } = useAPIResponseHandler()

  const fetchTrips = useCallback(async () => {
    setLoading(true)
    try {
      const response = await listTripsEnhanced()
      const result = handleResponse(response)
      if (result) {
        setTrips(result.data || [])
      }
    } catch (error) {
      console.error('Error fetching trips:', error)
    } finally {
      setLoading(false)
    }
  }, [handleResponse])

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
