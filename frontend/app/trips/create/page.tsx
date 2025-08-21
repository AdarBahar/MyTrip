'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

import { ArrowLeft, MapPin, Calendar, Loader2 } from 'lucide-react'
import { fetchWithAuth } from '@/lib/auth'

export default function CreateTripPage() {
  const [formData, setFormData] = useState({
    title: '',
    destination: '',
    start_date: '',
    description: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Check authentication
      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/login')
        return
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8100'
      
      // Create the trip
      const requestBody: any = {
        title: formData.title,
        destination: formData.destination,
        timezone: 'UTC', // Default timezone
        status: 'draft', // Default status
        is_published: false // Default to unpublished
      }

      // Only include start_date if it's provided
      if (formData.start_date) {
        requestBody.start_date = formData.start_date
      }

      const response = await fetchWithAuth(`${apiBaseUrl}/trips/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        const errorData = await response.json()
        let errorMessage = `Failed to create trip: ${response.status}`

        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors
            errorMessage = errorData.detail.map((err: any) => err.msg || err).join(', ')
          } else {
            errorMessage = errorData.detail
          }
        }

        throw new Error(errorMessage)
      }

      const newTrip = await response.json()
      
      // Redirect to the new trip's detail page
      router.push(`/trips/${newTrip.slug}`)
    } catch (err) {
      console.error('Error creating trip:', err)
      setError(err instanceof Error ? err.message : 'Failed to create trip')
    } finally {
      setLoading(false)
    }
  }

  const isFormValid = formData.title.trim() && formData.destination.trim()

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
          
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Create New Trip</h1>
            <p className="text-gray-600">Plan your next adventure</p>
          </div>
        </div>

        {/* Create Trip Form */}
        <div className="max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Trip Details
              </CardTitle>
              <CardDescription>
                Enter the basic information for your new trip
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Error Message */}
                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-red-800 text-sm">{error}</p>
                  </div>
                )}

                {/* Trip Title */}
                <div className="space-y-2">
                  <Label htmlFor="title">Trip Title *</Label>
                  <Input
                    id="title"
                    name="title"
                    type="text"
                    placeholder="e.g., Summer Road Trip 2025"
                    value={formData.title}
                    onChange={handleInputChange}
                    required
                    disabled={loading}
                  />
                </div>

                {/* Destination */}
                <div className="space-y-2">
                  <Label htmlFor="destination">Destination *</Label>
                  <Input
                    id="destination"
                    name="destination"
                    type="text"
                    placeholder="e.g., California, USA"
                    value={formData.destination}
                    onChange={handleInputChange}
                    required
                    disabled={loading}
                  />
                </div>

                {/* Start Date */}
                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date (Optional)</Label>
                  <Input
                    id="start_date"
                    name="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={handleInputChange}
                    disabled={loading}
                    min={new Date().toISOString().split('T')[0]} // Prevent past dates
                  />
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <textarea
                    id="description"
                    name="description"
                    placeholder="Tell us about your trip plans..."
                    value={formData.description}
                    onChange={handleInputChange}
                    disabled={loading}
                    rows={4}
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>

                {/* Form Actions */}
                <div className="flex gap-4 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    asChild
                    disabled={loading}
                  >
                    <Link href="/trips">Cancel</Link>
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={!isFormValid || loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Calendar className="h-4 w-4 mr-2" />
                        Create Trip
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Tips Card */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-lg">💡 Tips for Creating Your Trip</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Choose a descriptive title that helps you identify your trip</li>
                <li>• Be specific with your destination (city, state, country)</li>
                <li>• You can always edit these details later</li>
                <li>• After creating, you'll be able to add daily itineraries and routes</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
