import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth-options'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Get user session
    const session = await getServerSession(authOptions)
    if (!session?.user?.id) {
      return NextResponse.json(
        { 
          error: 'Authentication required. Please log in again.',
          code: '401',
          retryable: false
        },
        { status: 401 }
      )
    }

    // Get the form data from the request
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json(
        { 
          error: 'No file provided. Please select a file to upload.',
          code: '400',
          retryable: false
        },
        { status: 400 }
      )
    }

    // Validate file type and size
    if (file.type !== 'application/pdf') {
      return NextResponse.json(
        { 
          error: 'Only PDF files are allowed. Please convert your resume to PDF format.',
          code: '400',
          retryable: false
        },
        { status: 400 }
      )
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB
      return NextResponse.json(
        { 
          error: 'File size must be less than 10MB. Please compress your PDF and try again.',
          code: '400',
          retryable: false
        },
        { status: 400 }
      )
    }

    // Create new FormData for backend request
    const backendFormData = new FormData()
    backendFormData.append('file', file)

    // Add timeout to prevent hanging requests
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 seconds for file upload

    // Forward request to backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/resume/upload`, {
      method: 'POST',
      body: backendFormData,
      headers: {
        // Add user ID for backend authentication
        'X-User-ID': session.user.id,
      },
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!backendResponse.ok) {
      let errorMessage = 'Upload failed'
      let errorDetails = null

      try {
        const errorData = await backendResponse.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
        errorDetails = errorData
      } catch {
        errorMessage = backendResponse.statusText || errorMessage
      }

      console.error('Backend upload error:', {
        status: backendResponse.status,
        message: errorMessage,
        details: errorDetails,
        fileSize: file.size,
        fileName: file.name
      })

      return NextResponse.json(
        { 
          error: errorMessage,
          code: backendResponse.status.toString(),
          retryable: backendResponse.status >= 500 || backendResponse.status === 408 || backendResponse.status === 429
        },
        { status: backendResponse.status }
      )
    }

    const result = await backendResponse.json()
    
    return NextResponse.json(result)

  } catch (error) {
    console.error('Resume upload API error:', error)
    
    // Handle different types of errors
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return NextResponse.json(
          { 
            error: 'Upload timed out. Please check your connection and try again.',
            code: '408',
            retryable: true
          },
          { status: 408 }
        )
      }
      
      if (error.message.includes('fetch')) {
        return NextResponse.json(
          { 
            error: 'Unable to connect to upload service. Please try again.',
            code: '503',
            retryable: true
          },
          { status: 503 }
        )
      }
    }

    return NextResponse.json(
      { 
        error: 'Internal server error during upload. Please try again.',
        code: '500',
        retryable: true
      },
      { status: 500 }
    )
  }
}