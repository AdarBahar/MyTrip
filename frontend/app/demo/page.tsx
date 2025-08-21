import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { MapPin, Users, Calendar, Route, ArrowRight } from 'lucide-react'

export default function DemoPage() {
  // Mock demo data
  const demoTrips = [
    {
      id: 'demo-1',
      name: 'Pacific Coast Highway Adventure',
      description: 'A scenic drive along California\'s stunning coastline from San Francisco to Los Angeles',
      status: 'ACTIVE' as const,
      member_count: 4,
      day_count: 7,
      distance: '465 miles',
      highlights: ['Golden Gate Bridge', 'Big Sur', 'Monterey Bay', 'Santa Barbara']
    },
    {
      id: 'demo-2', 
      name: 'Rocky Mountain Explorer',
      description: 'Explore the majestic Rocky Mountains through Colorado and Wyoming',
      status: 'ACTIVE' as const,
      member_count: 2,
      day_count: 10,
      distance: '1,200 miles',
      highlights: ['Rocky Mountain National Park', 'Yellowstone', 'Grand Teton', 'Aspen']
    },
    {
      id: 'demo-3',
      name: 'New England Fall Foliage',
      description: 'Experience the beautiful autumn colors across Vermont, New Hampshire, and Maine',
      status: 'ACTIVE' as const,
      member_count: 6,
      day_count: 5,
      distance: '800 miles',
      highlights: ['White Mountains', 'Acadia National Park', 'Stowe', 'Burlington']
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Demo: RoadTrip Planner in Action
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Explore these sample road trips to see how our platform helps you plan, 
            collaborate, and navigate your perfect journey.
          </p>
          <Badge variant="secondary" className="text-sm">
            Interactive Demo - No Account Required
          </Badge>
        </div>

        {/* Demo Trips Grid */}
        <div className="grid md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8 mb-16">
          {demoTrips.map((trip) => (
            <Card key={trip.id} className="hover:shadow-xl transition-all duration-300 border-2 hover:border-blue-200">
              <CardHeader>
                <div className="flex justify-between items-start mb-2">
                  <Badge variant="outline" className="text-xs">
                    DEMO TRIP
                  </Badge>
                  <Badge variant={trip.status === 'ACTIVE' ? 'default' : 'secondary'}>
                    {trip.status}
                  </Badge>
                </div>
                <CardTitle className="text-xl mb-2">{trip.name}</CardTitle>
                <CardDescription className="text-sm leading-relaxed">
                  {trip.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Trip Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-blue-600" />
                    <span>{trip.member_count} travelers</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-green-600" />
                    <span>{trip.day_count} days</span>
                  </div>
                  <div className="flex items-center gap-2 col-span-2">
                    <Route className="h-4 w-4 text-purple-600" />
                    <span>{trip.distance} total</span>
                  </div>
                </div>

                {/* Highlights */}
                <div className="mb-6">
                  <h4 className="font-semibold text-sm mb-2 text-gray-700">Key Highlights:</h4>
                  <div className="flex flex-wrap gap-1">
                    {trip.highlights.map((highlight, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {highlight}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-2">
                  <Button className="w-full" asChild>
                    <Link href={`/demo/${trip.id}`}>
                      Explore This Trip
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Link>
                  </Button>
                  <Button variant="outline" className="w-full" size="sm">
                    <MapPin className="h-4 w-4 mr-2" />
                    View on Map
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Features Showcase */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          <Card className="text-center">
            <CardHeader>
              <Route className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <CardTitle>Smart Route Planning</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                See how our intelligent routing considers traffic, road conditions, 
                and your preferences to create optimal routes.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Users className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <CardTitle>Real-time Collaboration</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Experience how team members can collaborate on trip planning, 
                share ideas, and coordinate travel plans together.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <MapPin className="h-12 w-12 text-red-600 mx-auto mb-4" />
              <CardTitle>Interactive Maps</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Explore our high-quality maps with multiple view modes, 
                custom markers, and detailed route visualization.
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <Card className="max-w-2xl mx-auto bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-2xl">Ready to Plan Your Own Trip?</CardTitle>
              <CardDescription>
                Start creating your personalized road trip with all the features you just explored.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button size="lg" className="w-full" asChild>
                <Link href="/trips">Create Your First Trip</Link>
              </Button>
              <Button variant="outline" size="lg" className="w-full" asChild>
                <Link href="/">Back to Home</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
