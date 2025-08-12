import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ currentRole: string }> }
) {
  try {
    const { searchParams } = new URL(request.url)
    const userBackground = searchParams.get('user_background') || ''
    const maxSuggestions = searchParams.get('max_suggestions') || '5'
    
    // Get user ID from request headers
    const userIdHeader = request.headers.get('X-User-ID')
    if (!userIdHeader) {
      return NextResponse.json(
        { success: false, error: 'User authentication required' },
        { status: 401 }
      )
    }
    
    const resolvedParams = await params
    const encodedRole = encodeURIComponent(resolvedParams.currentRole)
    const queryParams = new URLSearchParams({
      user_background: userBackground,
      max_suggestions: maxSuggestions
    })
    
    // Forward the request to the FastAPI backend
    const response = await fetch(
      `${BACKEND_URL}/api/roadmap/suggestions/${encodedRole}?${queryParams}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userIdHeader,
        }
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json(
        { success: false, error: errorData.detail || 'Failed to get suggestions' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error in career suggestions API:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}