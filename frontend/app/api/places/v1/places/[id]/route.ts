/**
 * Places API Proxy - Place Details Endpoint
 * 
 * Proxies requests to the backend Places API for place details
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://mytrips-api.bahar.co.il'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    
    // Get authorization header
    const authorization = request.headers.get('authorization')
    
    // Make request to backend
    const response = await fetch(`${BACKEND_URL}/places/v1/places/${id}`, {
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
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=1800',
      },
    })

  } catch (error) {
    console.error('Places details API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
