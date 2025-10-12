/**
 * Reverse Geocoding API Proxy
 * 
 * Proxies reverse geocoding requests to the backend MapTiler service
 */

import { NextRequest, NextResponse } from 'next/server'

// Use Docker internal network when running in Docker
const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://mytrips-api.bahar.co.il'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const lat = searchParams.get('lat')
    const lon = searchParams.get('lon')

    if (!lat || !lon) {
      return NextResponse.json(
        { error: 'Latitude and longitude parameters are required' },
        { status: 400 }
      )
    }

    // Validate coordinates
    const latitude = parseFloat(lat)
    const longitude = parseFloat(lon)

    if (isNaN(latitude) || isNaN(longitude)) {
      return NextResponse.json(
        { error: 'Invalid latitude or longitude values' },
        { status: 400 }
      )
    }

    if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      return NextResponse.json(
        { error: 'Latitude must be between -90 and 90, longitude between -180 and 180' },
        { status: 400 }
      )
    }

    // Build backend URL
    const backendUrl = new URL('/places/reverse-geocode', BACKEND_URL)
    backendUrl.searchParams.set('lat', lat)
    backendUrl.searchParams.set('lon', lon)

    // Forward request to backend
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer fake_token_01K365YF7N0QVENA3HQZKGH7XA',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, max-age=300', // Cache for 5 minutes
      },
    })

  } catch (error) {
    console.error('Reverse geocoding proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to reverse geocode coordinates' },
      { status: 500 }
    )
  }
}
