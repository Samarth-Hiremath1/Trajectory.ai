# Error Handling and User Feedback System

This document describes the comprehensive error handling and user feedback system implemented for the Trajectory.AI application.

## Overview

The error handling system provides:
- **Error Boundaries**: React error boundaries to catch and handle component errors
- **Standardized Error Types**: Consistent error classification and handling
- **Retry Mechanisms**: Automatic and manual retry functionality with exponential backoff
- **User-Friendly Messages**: Clear, actionable error messages for users
- **Loading States**: Progress indicators and loading states for long operations
- **API Error Handling**: Enhanced error handling for all API routes

## Components

### Error Boundaries

#### `ErrorBoundary`
A React error boundary that catches JavaScript errors anywhere in the component tree.

```tsx
import { ErrorBoundary } from '@/components/error/ErrorBoundary'

<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

Features:
- Catches and displays errors with fallback UI
- Provides retry functionality
- Logs errors for debugging
- Supports custom fallback components

#### `ApiErrorBoundary`
Specialized error boundary for API operations with context-specific error messages.

```tsx
import { ApiErrorBoundary } from '@/components/error/ApiErrorBoundary'

<ApiErrorBoundary operation="chat" onRetry={retryFunction}>
  <ChatComponent />
</ApiErrorBoundary>
```

### Error Display Components

#### `ErrorDisplay`
Flexible component for displaying errors with different variants and styles.

```tsx
import { ErrorDisplay } from '@/components/ui/ErrorDisplay'

<ErrorDisplay
  error={error}
  onRetry={handleRetry}
  onDismiss={handleDismiss}
  variant="inline" // 'inline' | 'banner' | 'modal'
  showDetails={true}
/>
```

Variants:
- **inline**: Standard error display within content
- **banner**: Prominent banner-style error display
- **modal**: Modal overlay for critical errors

### Loading States

#### `LoadingState`
Comprehensive loading state component with multiple display types.

```tsx
import { LoadingState } from '@/components/ui/LoadingState'

<LoadingState
  type="spinner" // 'spinner' | 'progress' | 'skeleton'
  message="Loading your data..."
  progress={75}
/>
```

#### Specialized Loading Components
- `ChatLoadingState`: For chat initialization
- `RoadmapLoadingState`: For roadmap generation with progress
- `ResumeUploadLoadingState`: For file upload operations
- `ProfileLoadingState`: For profile data loading

#### `LoadingSpinner`
Simple, reusable spinner component.

```tsx
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

<LoadingSpinner size="md" color="primary" />
```

#### `ProgressIndicator`
Progress bar component for operations with measurable progress.

```tsx
import { ProgressIndicator } from '@/components/ui/ProgressIndicator'

<ProgressIndicator
  progress={65}
  label="Processing..."
  showPercentage={true}
/>
```

## Error Utilities

### Error Types
Standardized error classification:

```typescript
enum ErrorType {
  NETWORK = 'NETWORK',           // Connection issues
  AUTHENTICATION = 'AUTHENTICATION', // Auth failures
  VALIDATION = 'VALIDATION',     // Input validation errors
  SERVER = 'SERVER',            // Server-side errors
  TIMEOUT = 'TIMEOUT',          // Request timeouts
  UNKNOWN = 'UNKNOWN'           // Unclassified errors
}
```

### Error Normalization
The `normalizeError` function converts various error types into a standardized `AppError` format:

```typescript
interface AppError {
  type: ErrorType
  message: string
  code?: string
  details?: any
  retryable: boolean
}
```

### Retry Logic
Exponential backoff retry mechanism with configurable parameters:

```typescript
interface RetryConfig {
  maxAttempts: number    // Maximum retry attempts
  baseDelay: number      // Initial delay in milliseconds
  maxDelay: number       // Maximum delay cap
  backoffFactor: number  // Exponential backoff multiplier
}
```

## Hooks

### `useAsyncOperation`
Hook for managing async operations with built-in error handling and retry logic.

```tsx
import { useAsyncOperation } from '@/hooks/useAsyncOperation'

const { data, loading, error, execute, retry, reset } = useAsyncOperation(
  async () => {
    const response = await fetch('/api/data')
    return response.json()
  },
  {
    retryConfig: { maxAttempts: 3, baseDelay: 1000 },
    onSuccess: (data) => console.log('Success:', data),
    onError: (error) => console.error('Error:', error)
  }
)
```

### `useApiCall`
Specialized hook for API calls with automatic error handling.

```tsx
import { useApiCall } from '@/hooks/useAsyncOperation'

const { data, loading, error, execute } = useApiCall('/api/profile', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
})
```

### `useFileUpload`
Hook for file upload operations with progress tracking.

```tsx
import { useFileUpload } from '@/hooks/useAsyncOperation'

const { upload } = useFileUpload('/api/upload')
const { uploadProgress, execute } = upload(file, { userId: '123' })
```

## API Error Handling

All API routes have been enhanced with comprehensive error handling:

### Features
- **Timeout Protection**: Prevents hanging requests
- **Structured Error Responses**: Consistent error format across all endpoints
- **Retry Indicators**: Tells clients whether errors are retryable
- **Detailed Logging**: Comprehensive error logging for debugging

### Error Response Format
```typescript
{
  error: string,      // User-friendly error message
  code: string,       // HTTP status code or custom error code
  retryable: boolean  // Whether the operation can be retried
}
```

## Usage Examples

### Basic Error Boundary Usage
```tsx
function App() {
  return (
    <ErrorBoundary>
      <Header />
      <MainContent />
      <Footer />
    </ErrorBoundary>
  )
}
```

### API Operation with Error Handling
```tsx
function DataComponent() {
  const fetchData = useAsyncOperation(
    async () => {
      const response = await fetch('/api/data')
      if (!response.ok) throw new Error('Failed to fetch')
      return response.json()
    },
    {
      onError: (error) => {
        // Custom error handling
        console.error('Data fetch failed:', error)
      }
    }
  )

  if (fetchData.loading) {
    return <LoadingState message="Loading data..." />
  }

  if (fetchData.error) {
    return (
      <ErrorDisplay
        error={fetchData.error}
        onRetry={fetchData.retry}
        variant="inline"
      />
    )
  }

  return <div>{/* Render data */}</div>
}
```

### File Upload with Progress
```tsx
function FileUploadComponent() {
  const [file, setFile] = useState<File | null>(null)
  const { upload } = useFileUpload('/api/upload')

  const handleUpload = async () => {
    if (!file) return
    
    try {
      const { uploadProgress, execute } = upload(file)
      const result = await execute()
      console.log('Upload successful:', result)
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  return (
    <div>
      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  )
}
```

## Best Practices

1. **Always wrap components in error boundaries** at appropriate levels
2. **Use specific error types** for better user experience
3. **Provide retry mechanisms** for retryable errors
4. **Show loading states** for operations that take time
5. **Log errors appropriately** for debugging without exposing sensitive data
6. **Use consistent error messages** across the application
7. **Test error scenarios** to ensure proper handling

## Testing

The error handling system includes comprehensive tests covering:
- Error boundary functionality
- Error display variants
- Retry mechanisms
- Loading states
- API error handling

Run tests with:
```bash
npm test -- --testPathPattern=ErrorHandling
```

## Configuration

Error handling behavior can be configured through:
- Retry configuration objects
- Environment variables for API timeouts
- Custom error message mappings
- Logging levels and destinations

This system ensures a robust, user-friendly experience even when things go wrong, with clear feedback and recovery options for users.