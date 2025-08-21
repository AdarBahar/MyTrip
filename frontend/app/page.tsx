'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MapPin, Route, Users, Calendar } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token')
    if (token) {
      router.push('/trips')
    }
  }, [])
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Plan Your Perfect Road Trip
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Collaborative route planning with interactive maps, multiple routing profiles,
            and real-time collaboration for unforgettable journeys.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/trips">Get Started</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/demo">View Demo</Link>
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <Card>
            <CardHeader>
              <Route className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>Smart Routing</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Multiple routing profiles for cars, motorcycles, and bikes with real-time optimization.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Users className="h-8 w-8 text-green-600 mb-2" />
              <CardTitle>Collaboration</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Plan trips together with team members, share routes, and coordinate travel plans.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <MapPin className="h-8 w-8 text-red-600 mb-2" />
              <CardTitle>Interactive Maps</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                High-quality maps with terrain, satellite, and street views powered by MapTiler.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Calendar className="h-8 w-8 text-purple-600 mb-2" />
              <CardTitle>Trip Planning</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Organize multi-day trips with custom stops, waypoints, and detailed itineraries.
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="text-2xl">Ready to Start Planning?</CardTitle>
              <CardDescription>
                Create your first trip and experience the power of collaborative route planning.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button size="lg" className="w-full" asChild>
                <Link href="/login">Get Started</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}