'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: any): State {
    // Normalize the error to ensure it's an Error instance
    let normalizedError: Error
    
    try {
      if (error instanceof Error) {
        normalizedError = error
      } else if (typeof error === 'string') {
        normalizedError = new Error(error)
      } else if (error && typeof error === 'object') {
        normalizedError = new Error(JSON.stringify(error))
      } else {
        normalizedError = new Error('An unknown error occurred')
      }
    } catch (e) {
      normalizedError = new Error('An error occurred that could not be processed')
    }
    
    return { hasError: true, error: normalizedError }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Handle different types of errors more robustly
    let errorMessage = 'An unexpected error occurred'
    let errorDetails = error
    
    try {
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (typeof error === 'string') {
        errorMessage = error
      } else if (error && typeof error === 'object') {
        errorMessage = JSON.stringify(error)
        errorDetails = new Error(errorMessage)
      }
    } catch (e) {
      errorMessage = 'An error occurred that could not be serialized'
      errorDetails = new Error(errorMessage)
    }
    
    console.error('ErrorBoundary caught an error:', {
      error: errorDetails,
      errorInfo,
      originalError: error
    })
    
    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(errorDetails, errorInfo)
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI
      return (
        <div className="min-h-[200px] flex items-center justify-center bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="text-center max-w-md">
            <div className="flex justify-center mb-4">
              <svg 
                className="h-12 w-12 text-red-500" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" 
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-red-900 mb-2">
              Something went wrong
            </h3>
            <p className="text-red-700 mb-4 text-sm">
              {this.state.error?.message || 'An unexpected error occurred. Please try again.'}
            </p>
            <div className="flex justify-center space-x-3">
              <button
                onClick={this.handleRetry}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}