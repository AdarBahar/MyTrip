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
import { createTrip, TripCreate } from '@/lib/api/trips'
import { ErrorDisplay, SuccessDisplay, useAPIResponseHandler } from '@/components/ui/error-display'

export default function CreateTripPage() {
  const [formData, setFormData] = useState<TripCreate>({
    title: '',
    destination: '',
    start_date: null
  })
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { error, success, handleResponse, clearMessages } = useAPIResponseHandler()

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value || null
    }))

    // Clear messages when user starts typing
    if (error || success) {
      clearMessages()
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    clearMessages()

    try {
      // Check authentication
      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/login')
        return
      }

      const response = await createTrip(formData)
      const result = handleResponse(response, `Trip "${formData.title}" created successfully!`)

      if (result) {
        // Handle successful creation (201 Created)
        const tripData = result.trip

        // Redirect to the new trip's detail page
        router.push(`/trips/${tripData.slug}`)
      }
    } catch (err) {
      console.error('Error creating trip:', err)
      // Error is handled by useAPIResponseHandler
    } finally {
      setLoading(false)
    }
  }

  const isFormValid = formData.title.trim() && formData.destination?.trim()

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
                {/* Success Message */}
                {success && (
                  <SuccessDisplay
                    message={success.message}
                    type={success.type}
                    onDismiss={clearMessages}
                  />
                )}

                {/* Enhanced Error Display */}
                {error && (
                  <ErrorDisplay
                    error={error}
                    showSuggestions={true}
                    showRequestId={true}
                    onRetry={() => handleSubmit({ preventDefault: () => {} } as React.FormEvent)}
                  />
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
                    value={formData.destination || ''}
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
                    value={formData.start_date || ''}
                    onChange={handleInputChange}
                    disabled={loading}
                    min={new Date().toISOString().split('T')[0]} // Prevent past dates
                  />
                </div>

                {/* Enhanced Features Notice */}
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">✨ Enhanced Features</h4>
                  <ul className="text-xs text-blue-700 space-y-1">
                    <li>• Returns 201 Created on successful creation</li>
                    <li>• Shows structured validation errors</li>
                    <li>• Displays actionable suggestions</li>
                    <li>• Includes request tracking for debugging</li>
                  </ul>
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
