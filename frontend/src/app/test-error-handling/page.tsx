'use client'

import { useState } from 'react'
import { ErrorBoundary } from '@/components/error/ErrorBoundary'
import { ErrorDisplay } from '@/components/ui/ErrorDisplay'
import { LoadingState } from '@/components/ui/LoadingState'
import { useAsyncOperation } from '@/hooks/useAsyncOperation'
import { ErrorType } from '@/lib/error-utils'

// Component that throws different types of errors for testing
function ErrorThrower({ errorType }: { errorType: string }) {
  if (errorType === 'string') {
    throw 'This is a string error'
  }
  if (errorType === 'object') {
    throw { message: 'This is an object error', code: 500 }
  }
  if (errorType === 'error') {
    throw new Error('This is a proper Error object')
  }
  return <div>No error thrown</div>
}

export default function TestErrorHandlingPage() {
  const [errorType, setErrorType] = useState<string>('')
  const [showAsyncError, setShowAsyncError] = useState(false)

  // Test async operation with different error types
  const asyncOp = useAsyncOperation(
    async () => {
      await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate delay
      
      if (showAsyncError) {
        throw new Error('Async operation failed')
      }
      
      return { message: 'Success!' }
    }
  )

  const testError = {
    type: ErrorType.NETWORK,
    message: 'Test network error message',
    retryable: true
  }

  return (
    <div className="container mx-auto p-8 space-y-8">
      <h1 className="text-3xl font-bold mb-8">Error Handling Test Page</h1>
      
      {/* Error Boundary Tests */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Error Boundary Tests</h2>
        
        <div className="flex space-x-4">
          <button
            onClick={() => setErrorType('string')}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Throw String Error
          </button>
          <button
            onClick={() => setErrorType('object')}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Throw Object Error
          </button>
          <button
            onClick={() => setErrorType('error')}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Throw Error Object
          </button>
          <button
            onClick={() => setErrorType('')}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Clear Error
          </button>
        </div>

        <ErrorBoundary>
          <div className="p-4 border rounded">
            <ErrorThrower errorType={errorType} />
          </div>
        </ErrorBoundary>
      </section>

      {/* Error Display Tests */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Error Display Tests</h2>
        
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Inline Variant</h3>
          <ErrorDisplay
            error={testError}
            onRetry={() => console.log('Retry clicked')}
            onDismiss={() => console.log('Dismiss clicked')}
            variant="inline"
          />
          
          <h3 className="text-lg font-medium">Banner Variant</h3>
          <ErrorDisplay
            error={testError}
            onRetry={() => console.log('Retry clicked')}
            variant="banner"
          />
        </div>
      </section>

      {/* Loading State Tests */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Loading State Tests</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="text-lg font-medium mb-2">Spinner</h3>
            <LoadingState type="spinner" message="Loading..." />
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Progress</h3>
            <LoadingState type="progress" progress={65} message="Processing..." />
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Skeleton</h3>
            <LoadingState type="skeleton" />
          </div>
        </div>
      </section>

      {/* Async Operation Tests */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Async Operation Tests</h2>
        
        <div className="flex space-x-4">
          <button
            onClick={() => {
              setShowAsyncError(false)
              asyncOp.execute()
            }}
            disabled={asyncOp.loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            Test Success
          </button>
          <button
            onClick={() => {
              setShowAsyncError(true)
              asyncOp.execute()
            }}
            disabled={asyncOp.loading}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            Test Error
          </button>
          <button
            onClick={asyncOp.reset}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Reset
          </button>
        </div>

        <div className="p-4 border rounded">
          {asyncOp.loading && <LoadingState message="Running async operation..." />}
          
          {asyncOp.error && (
            <ErrorDisplay
              error={asyncOp.error}
              onRetry={asyncOp.retry}
              variant="inline"
            />
          )}
          
          {asyncOp.data && (
            <div className="text-green-600">
              Success: {JSON.stringify(asyncOp.data)}
            </div>
          )}
          
          {!asyncOp.loading && !asyncOp.error && !asyncOp.data && (
            <div className="text-gray-500">
              Click a button to test async operations
            </div>
          )}
        </div>
      </section>
    </div>
  )
}