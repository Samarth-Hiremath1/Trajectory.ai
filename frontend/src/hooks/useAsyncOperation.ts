'use client'

import { useState, useCallback, useRef } from 'react'
import { AppError, normalizeError, withRetry, RetryConfig, DEFAULT_RETRY_CONFIG } from '@/lib/error-utils'

interface AsyncOperationState<T> {
  data: T | null
  loading: boolean
  error: AppError | null
  progress?: number
}

interface UseAsyncOperationOptions {
  retryConfig?: RetryConfig
  onSuccess?: (data: any) => void
  onError?: (error: AppError) => void
  onRetry?: (attempt: number, error: AppError) => void
}

export function useAsyncOperation<T>(
  operation: () => Promise<T>,
  options: UseAsyncOperationOptions = {}
) {
  const [state, setState] = useState<AsyncOperationState<T>>({
    data: null,
    loading: false,
    error: null
  })

  const abortControllerRef = useRef<AbortController | null>(null)
  const retryConfig = options.retryConfig || DEFAULT_RETRY_CONFIG

  const execute = useCallback(async () => {
    // Cancel any ongoing operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController()

    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
      progress: 0
    }))

    try {
      const result = await withRetry(
        operation,
        retryConfig,
        (attempt, error) => {
          // Update progress during retries
          const progress = (attempt / retryConfig.maxAttempts) * 50 // 50% for retries
          setState(prev => ({ ...prev, progress }))
          
          if (options.onRetry) {
            options.onRetry(attempt, error)
          }
        }
      )

      // Check if operation was aborted
      if (abortControllerRef.current?.signal.aborted) {
        return
      }

      setState({
        data: result,
        loading: false,
        error: null,
        progress: 100
      })

      if (options.onSuccess) {
        options.onSuccess(result)
      }

      return result
    } catch (error) {
      // Check if operation was aborted
      if (abortControllerRef.current?.signal.aborted) {
        return
      }

      const normalizedError = normalizeError(error)
      
      setState({
        data: null,
        loading: false,
        error: normalizedError,
        progress: undefined
      })

      if (options.onError) {
        try {
          options.onError(normalizedError)
        } catch (callbackError) {
          console.error('Error in onError callback:', callbackError)
        }
      }

      // Don't re-throw the error to prevent unhandled rejections
      // The error is already stored in state for components to handle
      return undefined
    }
  }, [operation, retryConfig, options])

  const retry = useCallback(() => {
    return execute()
  }, [execute])

  const reset = useCallback(() => {
    // Cancel any ongoing operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    setState({
      data: null,
      loading: false,
      error: null,
      progress: undefined
    })
  }, [])

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    setState(prev => ({
      ...prev,
      loading: false,
      progress: undefined
    }))
  }, [])

  return {
    ...state,
    execute,
    retry,
    reset,
    cancel,
    isRetryable: state.error?.retryable ?? false
  }
}

// Specialized hook for API calls
export function useApiCall<T>(
  url: string,
  options: RequestInit = {},
  hookOptions: UseAsyncOperationOptions = {}
) {
  const operation = useCallback(async (): Promise<T> => {
    const response = await fetch(url, {
      ...options,
      signal: AbortSignal.timeout(30000) // 30 second timeout
    })

    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`)
      ;(error as any).status = response.status
      
      // Try to get error details from response
      try {
        const errorData = await response.json()
        if (errorData.error || errorData.message) {
          error.message = errorData.error || errorData.message
        }
      } catch {
        // Ignore JSON parsing errors
      }
      
      throw error
    }

    return response.json()
  }, [url, options])

  return useAsyncOperation<T>(operation, hookOptions)
}

// Hook for file upload operations
export function useFileUpload(
  url: string,
  options: UseAsyncOperationOptions = {}
) {
  const [uploadProgress, setUploadProgress] = useState(0)

  const operation = useCallback(async (file: File, additionalData?: Record<string, string>) => {
    const formData = new FormData()
    formData.append('file', file)
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value)
      })
    }

    return new Promise<any>((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100
          setUploadProgress(progress)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText)
            resolve(response)
          } catch {
            resolve(xhr.responseText)
          }
        } else {
          const error = new Error(`HTTP ${xhr.status}: ${xhr.statusText}`)
          ;(error as any).status = xhr.status
          reject(error)
        }
      })

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'))
      })

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'))
      })

      xhr.open('POST', url)
      xhr.send(formData)
    })
  }, [url])

  const asyncOp = useAsyncOperation(
    () => Promise.resolve(null), // Placeholder operation
    {
      ...options,
      onSuccess: (data) => {
        if (options.onSuccess) {
          options.onSuccess(data)
        }
      }
    }
  )

  const upload = useCallback(async (file: File, additionalData?: Record<string, string>) => {
    setUploadProgress(0)
    
    // Create a new operation for this specific upload
    const uploadOperation = () => operation(file, additionalData)
    
    return withRetry(uploadOperation, options.retryConfig || DEFAULT_RETRY_CONFIG)
  }, [operation, options.retryConfig])

  return {
    ...asyncOp,
    uploadProgress,
    upload
  }
}