'use client'

import { AppError, ErrorType, getErrorMessage } from '@/lib/error-utils'

interface ErrorDisplayProps {
  error: AppError | Error | string
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
  variant?: 'inline' | 'banner' | 'modal'
  showDetails?: boolean
}

export function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  className = '',
  variant = 'inline',
  showDetails = false
}: ErrorDisplayProps) {
  // Normalize error to AppError format
  const normalizedError: AppError = typeof error === 'string' 
    ? { type: ErrorType.UNKNOWN, message: error, retryable: true }
    : error instanceof Error
    ? { type: ErrorType.UNKNOWN, message: error.message, retryable: true }
    : error

  const message = getErrorMessage(normalizedError)

  // Get appropriate icon and colors based on error type
  const getErrorStyles = () => {
    switch (normalizedError.type) {
      case ErrorType.NETWORK:
        return {
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          textColor: 'text-orange-800',
          iconColor: 'text-orange-500',
          buttonColor: 'bg-orange-600 hover:bg-orange-700'
        }
      case ErrorType.AUTHENTICATION:
        return {
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-800',
          iconColor: 'text-red-500',
          buttonColor: 'bg-red-600 hover:bg-red-700'
        }
      case ErrorType.VALIDATION:
        return {
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-500',
          buttonColor: 'bg-yellow-600 hover:bg-yellow-700'
        }
      default:
        return {
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-800',
          iconColor: 'text-red-500',
          buttonColor: 'bg-red-600 hover:bg-red-700'
        }
    }
  }

  const styles = getErrorStyles()

  const ErrorIcon = () => (
    <svg 
      className={`h-5 w-5 ${styles.iconColor}`} 
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
  )

  if (variant === 'banner') {
    return (
      <div className={`${styles.bgColor} ${styles.borderColor} border-l-4 p-4 ${className}`}>
        <div className="flex">
          <div className="flex-shrink-0">
            <ErrorIcon />
          </div>
          <div className="ml-3 flex-1">
            <p className={`text-sm ${styles.textColor}`}>{message}</p>
            {showDetails && normalizedError.code && (
              <p className={`text-xs ${styles.textColor} opacity-75 mt-1`}>
                Error Code: {normalizedError.code}
              </p>
            )}
          </div>
          <div className="ml-auto pl-3">
            <div className="flex space-x-2">
              {onRetry && normalizedError.retryable && (
                <button
                  onClick={onRetry}
                  className={`text-sm ${styles.textColor} hover:opacity-75 underline`}
                >
                  Retry
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className={`text-sm ${styles.textColor} hover:opacity-75`}
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (variant === 'modal') {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
          <div className="mt-3 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <ErrorIcon />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mt-4">Error</h3>
            <div className="mt-2 px-7 py-3">
              <p className="text-sm text-gray-500">{message}</p>
              {showDetails && normalizedError.code && (
                <p className="text-xs text-gray-400 mt-2">
                  Error Code: {normalizedError.code}
                </p>
              )}
            </div>
            <div className="flex justify-center space-x-3 mt-4">
              {onRetry && normalizedError.retryable && (
                <button
                  onClick={onRetry}
                  className={`px-4 py-2 ${styles.buttonColor} text-white text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2`}
                >
                  Retry
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Default inline variant
  return (
    <div className={`${styles.bgColor} ${styles.borderColor} border rounded-md p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <ErrorIcon />
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.textColor}`}>
            {normalizedError.type === ErrorType.NETWORK ? 'Connection Error' : 'Error'}
          </h3>
          <div className={`mt-2 text-sm ${styles.textColor}`}>
            <p>{message}</p>
            {showDetails && normalizedError.code && (
              <p className="text-xs opacity-75 mt-1">
                Error Code: {normalizedError.code}
              </p>
            )}
          </div>
          {(onRetry && normalizedError.retryable) || onDismiss ? (
            <div className="mt-4">
              <div className="flex space-x-3">
                {onRetry && normalizedError.retryable && (
                  <button
                    onClick={onRetry}
                    className={`text-sm ${styles.buttonColor} text-white px-3 py-2 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2`}
                  >
                    Try Again
                  </button>
                )}
                {onDismiss && (
                  <button
                    onClick={onDismiss}
                    className={`text-sm ${styles.textColor} hover:opacity-75 underline`}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}