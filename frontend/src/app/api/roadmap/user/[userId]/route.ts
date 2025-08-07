import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  try {
    const { userId } = await params

    // Add timeout to prevent hanging requests
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 seconds

    const response = await fetch(`${BACKEND_URL}/api/roadmap/user/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let errorMessage = 'Failed to get user roadmaps'
      let errorDetails = null

      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
        errorDetails = errorData
      } catch {
        errorMessage = response.statusText || errorMessage
      }

      console.error('Backend error:', {
        status: response.status,
        message: errorMessage,
        details: errorDetails,
        userId
      })

      return NextResponse.json(
        { 
          error: errorMessage,
          code: response.status.toString(),
          retryable: response.status >= 500 || response.status === 408 || response.status === 429
        },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Get user roadmaps API error:', error)
    
    // Handle different types of errors
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return NextResponse.json(
          { 
            error: 'Request timed out. Please try again.',
            code: '408',
            retryable: true
          },
          { status: 408 }
        )
      }
      
      if (error.message.includes('fetch')) {
        return NextResponse.json(
          { 
            error: 'Unable to connect to backend service. Please try again.',
            code: '503',
            retryable: true
          },
          { status: 503 }
        )
      }
    }

    return NextResponse.json(
      { 
        error: 'Internal server error. Please try again.',
        code: '500',
        retryable: true
      },
      { status: 500 }
    )
  }
}