'use client'

import React from 'react'
import { ErrorBoundary } from './ErrorBoundary'

interface ApiErrorBoundaryProps {
  children: React.ReactNode
  operation?: string
  onRetry?: () => void
}

export function ApiErrorBoundary({ children, operation = 'operation', onRetry }: ApiErrorBoundaryProps) {
  const handleError = (error: Error) => {
    // Log API errors with more context
    console.error(`API Error in ${operation}:`, {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
    })
  }

  const fallbackUI = (
    <div className="min-h-[150px] flex items-center justify-center bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <div className="text-center max-w-sm">
        <div className="flex justify-center mb-3">
          <svg 
            className="h-10 w-10 text-yellow-500" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
        </div>
        <h3 className="text-md font-medium text-yellow-900 mb-2">
          {operation.charAt(0).toUpperCase() + operation.slice(1)} Failed
        </h3>
        <p className="text-yellow-700 mb-3 text-sm">
          We&apos;re having trouble completing this request. Please check your connection and try again.
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
          >
            Retry {operation}
          </button>
        )}
      </div>
    </div>
  )

  return (
    <ErrorBoundary fallback={fallbackUI} onError={handleError}>
      {children}
    </ErrorBoundary>
  )
}