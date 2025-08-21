'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plus, MapPin, Users, Calendar, LogOut } from 'lucide-react'
import { fetchWithAuth } from '@/lib/auth'

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
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('auth_token')
    const userData = localStorage.getItem('user_data')

    if (!token || !userData) {
      router.push('/login')
      return
    }

    try {
      setUser(JSON.parse(userData))
      fetchTrips()
    } catch (error) {
      console.error('Error parsing user data:', error)
      router.push('/login')
    }
  }, [])

  const fetchTrips = async () => {
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8100'
      const response = await fetchWithAuth(`${apiBaseUrl}/trips/`)

      if (!response.ok) {
        throw new Error(`Failed to fetch trips: ${response.status}`)
      }

      const data = await response.json()
      setTrips(data.trips || [])
    } catch (err) {
      console.error('Error fetching trips:', err)
      setError(err instanceof Error ? err.message : 'Failed to load trips')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading trips...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">My Trips</h1>
            <p className="text-gray-600">
              Welcome back, {user?.display_name || 'User'}! Plan and manage your road trip adventures
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
            <Button size="lg" asChild>
              <Link href="/trips/create">
                <Plus className="h-4 w-4 mr-2" />
                Create New Trip
              </Link>
            </Button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <Card className="mb-8 border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <p className="text-red-600">Error: {error}</p>
              <Button 
                variant="outline" 
                onClick={fetchTrips}
                className="mt-4"
              >
                Try Again
              </Button>
            </CardContent>
          </Card>
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

        {/* Trips Grid */}
        {trips.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((trip) => (
              <Card key={trip.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-xl mb-1">{trip.title}</CardTitle>
                      <p className="text-gray-600 mb-2">{trip.destination}</p>
                      <Badge variant={trip.status === 'active' ? 'default' : 'secondary'}>
                        {trip.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <CardDescription className="mt-2">
                    Trip to {trip.destination}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      <span>
                        {trip.start_date
                          ? `Starts ${new Date(trip.start_date).toLocaleDateString()}`
                          : 'No start date'
                        }
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      <span>{trip.members.length} members</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      <span>{trip.is_published ? 'Published' : 'Draft'}</span>
                    </div>
                  </div>

                  {trip.created_by_user && (
                    <div className="text-xs text-gray-500 mb-3">
                      Created by <span className="font-medium">{trip.created_by_user.display_name}</span>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Button asChild className="flex-1">
                      <Link href={`/trips/${trip.slug}`}>View Trip</Link>
                    </Button>
                    <Button variant="outline" size="sm">
                      Share
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
