import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate required fields
    if (!body.current_role || !body.target_role) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Both current role and target role are required.',
          code: '400',
          retryable: false
        },
        { status: 400 }
      )
    }

    // Get user ID from request headers
    const userIdHeader = request.headers.get('X-User-ID')
    if (!userIdHeader) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'User authentication required.',
          code: '401',
          retryable: false
        },
        { status: 401 }
      )
    }

    // Add timeout to prevent hanging requests
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120000) // 2 minutes for AI generation

    // Forward the request to the FastAPI backend
    const response = await fetch(`${BACKEND_URL}/api/roadmap/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userIdHeader,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let errorMessage = 'Failed to generate roadmap'
      let errorDetails = null

      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
        errorDetails = errorData
      } catch {
        errorMessage = response.statusText || errorMessage
      }

      console.error('Backend roadmap generation error:', {
        status: response.status,
        message: errorMessage,
        details: errorDetails,
        requestBody: body
      })

      return NextResponse.json(
        { 
          success: false, 
          error: errorMessage,
          code: response.status.toString(),
          retryable: response.status >= 500 || response.status === 408 || response.status === 429
        },
        { status: response.status }
      )
    }

    const data = await response.json()
    
    // Validate response structure
    if (!data.success && !data.roadmap) {
      console.error('Invalid response structure from backend:', data)
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid response from roadmap service. Please try again.',
          code: '502',
          retryable: true
        },
        { status: 502 }
      )
    }

    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error in roadmap generation API:', error)
    
    // Handle different types of errors
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return NextResponse.json(
          { 
            success: false, 
            error: 'Roadmap generation timed out. This usually happens with complex requests. Please try again.',
            code: '408',
            retryable: true
          },
          { status: 408 }
        )
      }
      
      if (error.message.includes('fetch')) {
        return NextResponse.json(
          { 
            success: false, 
            error: 'Unable to connect to roadmap generation service. Please try again.',
            code: '503',
            retryable: true
          },
          { status: 503 }
        )
      }

      if (error.message.includes('JSON')) {
        return NextResponse.json(
          { 
            success: false, 
            error: 'Invalid request format. Please check your input and try again.',
            code: '400',
            retryable: false
          },
          { status: 400 }
        )
      }
    }

    return NextResponse.json(
      { 
        success: false, 
        error: 'Internal server error during roadmap generation. Please try again.',
        code: '500',
        retryable: true
      },
      { status: 500 }
    )
  }
}