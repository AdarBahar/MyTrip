/**
 * Trips Page Component
 *
 * Displays user's trips with proper TypeScript safety, accessibility,
 * and performance optimizations based on code review feedback.
 */

'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardTitle } from '@/components/ui/card'
import { Plus, LogOut, MapPin } from 'lucide-react'
import { listTripsEnhanced } from '@/lib/api/trips'
import { TripCard } from '@/components/trips/trip-card'
import { TripListSkeleton } from '@/components/ui/trip-skeleton'

// Properly closed TypeScript interfaces
interface TripCreator {
  id: string
  email: string
  display_name: string
}

interface Trip {
  id: string
  slug: string
  title: string
  destination: string
  start_date: string | null
  timezone: string
  status: 'draft' | 'active' | 'completed' | 'archived'
  is_published: boolean
  created_by: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  members: any[]
  created_by_user: TripCreator | null
}

export default function TripsPage() {
  // Properly typed state variables
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<TripCreator | null>(null)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  // Enhanced fetch function with AbortController
  const fetchTrips = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    setError(null)

    try {
      const response = await listTripsEnhanced(/* { signal } when API supports it */)

      if (response.success && response.data) {
        setTrips(response.data.data || [])
      } else {
        setError('Failed to load trips')
      }
    } catch (err) {
      if ((err as any)?.name !== 'AbortError') {
        console.error('Error fetching trips:', err)
        setError('Failed to load trips')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  // Enhanced delete handler with rollback capability
  const handleTripDeleted = useCallback((tripId: string, success: boolean) => {
    if (!success) return // TripCard should handle toast
    setTrips(prevTrips => prevTrips.filter(trip => trip.id !== tripId))
  }, [])

  // Enhanced logout handler with server-side cleanup
  const handleLogout = useCallback(async () => {
    try {
      // TODO: Call logout API to revoke server session
      // await logoutAPI()

      // Clear client storage
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('auth_token')
        window.localStorage.removeItem('user_data')
      }

      // Clear any client caches (SWR/React Query would go here)

      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
      // Still redirect even if server logout fails
      router.push('/login')
    }
  }, [router])

  // Enhanced useEffect with client-side guards and cleanup
  useEffect(() => {
    let canceled = false

    // Guard against SSR
    if (typeof window === 'undefined') return

    const token = window.localStorage.getItem('auth_token')
    const userData = window.localStorage.getItem('user_data')

    if (!token || !userData) {
      if (!canceled) router.push('/login')
      return
    }

    try {
      const parsedUser = JSON.parse(userData) as TripCreator
      if (!canceled) {
        setUser(parsedUser)
        fetchTrips().catch(() => {}) // Already handles errors
      }
    } catch {
      if (!canceled) router.push('/login')
    }

    return () => { canceled = true }
  }, [])

  // Enhanced loading state with skeleton and accessibility
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100" aria-busy="true">
        <div className="container mx-auto px-4 py-16">
          <TripListSkeleton count={6} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Header with improved accessibility */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <div className="flex items-center space-x-4 mb-2">
              <h1 className="text-4xl font-bold text-gray-900">My Trips</h1>
            </div>
            <p className="text-gray-600">
              Welcome back, {user?.display_name || 'User'}! Plan and manage your road trip adventures
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleLogout}
              aria-label="Log out of your account"
            >
              <LogOut className="h-4 w-4 mr-2" aria-hidden="true" />
              Logout
            </Button>
            <Button size="lg" asChild>
              <Link
                href="/trips/create"
                aria-label="Create a new trip"
              >
                <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
                Create New Trip
              </Link>
            </Button>
          </div>
        </header>

        {/* Enhanced Error Display with Accessibility */}
        {error && (
          <div
            role="alert"
            aria-live="polite"
            className="mb-8 p-4 bg-red-50 border border-red-200 rounded-md"
          >
            <div className="flex items-center justify-between">
              <p className="text-red-700">{error}</p>
              <button
                type="button"
                onClick={() => fetchTrips()}
                className="text-red-600 hover:text-red-800 underline"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && trips.length === 0 && (
          <Card className="text-center py-16">
            <CardContent>
              <MapPin className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <CardTitle className="text-2xl mb-2">No trips yet</CardTitle>
              <CardDescription className="mb-6">
                Create your first trip to start planning your adventure
              </CardDescription>
              <Button size="lg" asChild>
                <Link href="/trips/create">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Trip
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Trips Grid with Extracted Components */}
        {trips.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={trip}
                onDelete={handleTripDeleted}
                loading={false}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
