/**
 * Places API Proxy - Suggestions Endpoint
 * 
 * Proxies requests to the backend Places API for type-ahead suggestions
 */

import { NextRequest, NextResponse } from 'next/server'

// Use Docker internal network when running in Docker
const BACKEND_URL = 'http://roadtrip-backend:8000'

export async function GET(request: NextRequest) {
  try {
    // Get search parameters
    const searchParams = request.nextUrl.searchParams
    
    // Forward all query parameters
    const backendUrl = new URL(`${BACKEND_URL}/places/v1/places/suggest`)
    searchParams.forEach((value, key) => {
      backendUrl.searchParams.append(key, value)
    })

    // Get authorization header
    const authorization = request.headers.get('authorization')
    
    // Make request to backend
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Authorization': authorization || 'Bearer fake_token_01K365YF7N0QVENA3HQZKGH7XA',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Backend request failed', status: response.status },
        { status: response.status }
      )
    }

    const data = await response.json()
    
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, max-age=60, stale-while-revalidate=300',
      },
    })

  } catch (error) {
    console.error('Places suggest API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
