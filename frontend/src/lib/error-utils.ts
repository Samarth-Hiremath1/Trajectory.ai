// Error types for better error handling
export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION',
  VALIDATION = 'VALIDATION',
  SERVER = 'SERVER',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}

export interface AppError {
  type: ErrorType
  message: string
  code?: string
  details?: any
  retryable: boolean
}

// Convert various error types to AppError
export function normalizeError(error: any): AppError {
  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      type: ErrorType.NETWORK,
      message: 'Network connection failed. Please check your internet connection.',
      retryable: true
    }
  }

  // HTTP errors
  if (error.status) {
    switch (error.status) {
      case 401:
        return {
          type: ErrorType.AUTHENTICATION,
          message: 'Your session has expired. Please log in again.',
          code: '401',
          retryable: false
        }
      case 403:
        return {
          type: ErrorType.AUTHENTICATION,
          message: 'You don\'t have permission to perform this action.',
          code: '403',
          retryable: false
        }
      case 400:
        return {
          type: ErrorType.VALIDATION,
          message: error.message || 'Invalid request. Please check your input.',
          code: '400',
          retryable: false
        }
      case 408:
        return {
          type: ErrorType.TIMEOUT,
          message: 'Request timed out. Please try again.',
          code: '408',
          retryable: true
        }
      case 429:
        return {
          type: ErrorType.SERVER,
          message: 'Too many requests. Please wait a moment and try again.',
          code: '429',
          retryable: true
        }
      case 500:
      case 502:
      case 503:
      case 504:
        return {
          type: ErrorType.SERVER,
          message: 'Server error. Please try again in a few moments.',
          code: error.status.toString(),
          retryable: true
        }
      default:
        return {
          type: ErrorType.UNKNOWN,
          message: error.message || 'An unexpected error occurred.',
          code: error.status.toString(),
          retryable: true
        }
    }
  }

  // Generic errors
  if (error instanceof Error) {
    return {
      type: ErrorType.UNKNOWN,
      message: error.message || 'An unexpected error occurred.',
      retryable: true
    }
  }

  // Fallback
  return {
    type: ErrorType.UNKNOWN,
    message: 'An unexpected error occurred.',
    retryable: true
  }
}

// Retry configuration
export interface RetryConfig {
  maxAttempts: number
  baseDelay: number
  maxDelay: number
  backoffFactor: number
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffFactor: 2
}

// Exponential backoff delay calculation
export function calculateDelay(attempt: number, config: RetryConfig): number {
  const delay = config.baseDelay * Math.pow(config.backoffFactor, attempt - 1)
  return Math.min(delay, config.maxDelay)
}

// Sleep utility for delays
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// Retry wrapper for async functions
export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  onRetry?: (attempt: number, error: AppError) => void
): Promise<T> {
  let lastError: AppError

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = normalizeError(error)
      
      // Don't retry if error is not retryable
      if (!lastError.retryable) {
        throw lastError
      }

      // Don't retry on last attempt
      if (attempt === config.maxAttempts) {
        throw lastError
      }

      // Call retry callback if provided
      if (onRetry) {
        onRetry(attempt, lastError)
      }

      // Wait before retrying
      const delay = calculateDelay(attempt, config)
      await sleep(delay)
    }
  }

  throw lastError!
}

// Fetch wrapper with retry logic
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<Response> {
  return withRetry(async () => {
    const response = await fetch(url, {
      ...options,
      // Add timeout to prevent hanging requests
      signal: AbortSignal.timeout(30000) // 30 seconds
    })

    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`)
      ;(error as any).status = response.status
      throw error
    }

    return response
  }, config)
}

// User-friendly error messages
export function getErrorMessage(error: AppError): string {
  switch (error.type) {
    case ErrorType.NETWORK:
      return 'Connection problem. Please check your internet and try again.'
    case ErrorType.AUTHENTICATION:
      return error.message
    case ErrorType.VALIDATION:
      return error.message
    case ErrorType.TIMEOUT:
      return 'Request timed out. Please try again.'
    case ErrorType.SERVER:
      return 'Server is temporarily unavailable. Please try again in a few moments.'
    default:
      return error.message || 'Something went wrong. Please try again.'
  }
}

// Error logging utility
export function logError(error: AppError, context?: string) {
  const logData = {
    type: error.type,
    message: error.message,
    code: error.code,
    context,
    timestamp: new Date().toISOString(),
    userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'server',
    url: typeof window !== 'undefined' ? window.location.href : 'server'
  }

  console.error('Application Error:', logData)

  // In production, you might want to send this to an error tracking service
  // like Sentry, LogRocket, etc.
}