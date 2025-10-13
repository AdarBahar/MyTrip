/**
 * Geocoding API Proxy
 * 
 * Proxies geocoding requests to the backend MapTiler service
 */

import { NextRequest, NextResponse } from 'next/server'

// Use Docker internal network when running in Docker
const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://mytrips-api.bahar.co.il'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const address = searchParams.get('address')

    if (!address) {
      return NextResponse.json(
        { error: 'Address parameter is required' },
        { status: 400 }
      )
    }

    // Build backend URL
    const backendUrl = new URL('/places/geocode', BACKEND_URL)
    backendUrl.searchParams.set('address', address)

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
    console.error('Geocoding proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to geocode address' },
      { status: 500 }
    )
  }
}
