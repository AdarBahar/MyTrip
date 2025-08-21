'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, MapPin, Calendar, Users, Settings, Share2, Plus } from 'lucide-react'
import { fetchWithAuth } from '@/lib/auth'
import { DebugStatus } from '@/components/debug'
import { TripDateActions } from '@/components/trips/trip-date-actions'

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

export default function TripDetailPage({ params }: { params: { slug: string } }) {
  const [trip, setTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('auth_token')
    if (!token) {
      router.push('/login')
      return
    }
    
    fetchTripDetails()
  }, [params.slug])

  const fetchTripDetails = async () => {
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8100'
      
      // First, get all trips to find the one with matching slug
      const tripsResponse = await fetchWithAuth(`${apiBaseUrl}/trips/`)
      if (!tripsResponse.ok) {
        throw new Error(`Failed to fetch trips: ${tripsResponse.status}`)
      }
      
      const tripsData = await tripsResponse.json()
      const foundTrip = tripsData.trips.find((t: Trip) => t.slug === params.slug)
      
      if (!foundTrip) {
        setError('Trip not found')
        return
      }
      
      // Now get the specific trip details
      const tripResponse = await fetchWithAuth(`${apiBaseUrl}/trips/${foundTrip.id}`)
      if (!tripResponse.ok) {
        throw new Error(`Failed to fetch trip details: ${tripResponse.status}`)
      }
      
      const tripData = await tripResponse.json()
      setTrip(tripData)
    } catch (err) {
      console.error('Error fetching trip details:', err)
      setError(err instanceof Error ? err.message : 'Failed to load trip details')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trip details...</p>
        </div>
      </div>
    )
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Trip Not Found</h1>
          <p className="text-gray-600 mb-6">{error || 'The requested trip could not be found.'}</p>
          <Button asChild>
            <Link href="/trips">Back to Trips</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" size="sm" asChild>
            <Link href="/trips">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Trips
            </Link>
          </Button>
          
          <div className="flex-1">
            <div className="flex items-center space-x-4 mb-1">
              <h1 className="text-3xl font-bold text-gray-900">{trip.title}</h1>
              <DebugStatus />
            </div>
            <p className="text-gray-600">Trip to {trip.destination}</p>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Trip Info Card */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Trip Overview
                </CardTitle>
                <CardDescription>
                  Plan and manage your road trip to {trip.destination}
                </CardDescription>
              </div>
              <Badge variant={trip.status === 'active' ? 'default' : 'secondary'}>
                {trip.status.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-center gap-3">
                <TripDateActions
                  trip={trip}
                  onTripUpdate={(updatedTrip) => setTrip(updatedTrip)}
                  size="sm"
                />
              </div>
              
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="font-medium">Members</p>
                  <p className="text-gray-600">{trip.members.length} members</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="font-medium">Status</p>
                  <p className="text-gray-600">{trip.is_published ? 'Published' : 'Draft'}</p>
                </div>
              </div>
            </div>
            
            {trip.created_by_user && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  Created by <span className="font-medium text-gray-700">{trip.created_by_user.display_name}</span> on {new Date(trip.created_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Days Section */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Trip Days</CardTitle>
                <CardDescription>
                  Plan your daily itinerary and routes
                </CardDescription>
              </div>
              <Button asChild>
                <Link href={`/trips/${trip.slug}/days`}>
                  <Plus className="h-4 w-4 mr-2" />
                  Manage Days
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12">
              <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No days planned yet</h3>
              <p className="text-gray-600 mb-6">
                Start planning your trip by adding your first day
              </p>
              <Button asChild>
                <Link href={`/trips/${trip.slug}/days`}>
                  <Plus className="h-4 w-4 mr-2" />
                  Start Planning Days
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
