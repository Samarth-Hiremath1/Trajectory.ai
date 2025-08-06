import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ErrorBoundary } from '../ErrorBoundary'
import { ErrorDisplay } from '../../ui/ErrorDisplay'
import { AppError, ErrorType } from '../../../lib/error-utils'

// Mock component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>No error</div>
}

describe('Error Handling Components', () => {
  describe('ErrorBoundary', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )
      
      expect(screen.getByText('No error')).toBeInTheDocument()
    })

    it('should render error UI when error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByText('Test error message')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
      expect(screen.getByText('Reload Page')).toBeInTheDocument()
    })

    it('should call retry handler when Try Again is clicked', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      
      fireEvent.click(screen.getByText('Try Again'))
      
      // After retry, the component should attempt to render children again
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )
      
      expect(screen.getByText('No error')).toBeInTheDocument()
    })
  })

  describe('ErrorDisplay', () => {
    it('should render network error with appropriate styling', () => {
      const networkError: AppError = {
        type: ErrorType.NETWORK,
        message: 'Network connection failed',
        retryable: true
      }

      const mockRetry = jest.fn()

      render(
        <ErrorDisplay
          error={networkError}
          onRetry={mockRetry}
          variant="inline"
        />
      )

      expect(screen.getByText('Connection Error')).toBeInTheDocument()
      expect(screen.getByText('Connection problem. Please check your internet and try again.')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })

    it('should render validation error without retry button', () => {
      const validationError: AppError = {
        type: ErrorType.VALIDATION,
        message: 'Invalid input provided',
        retryable: false
      }

      render(
        <ErrorDisplay
          error={validationError}
          variant="inline"
        />
      )

      expect(screen.getByText('Invalid input provided')).toBeInTheDocument()
      expect(screen.queryByText('Try Again')).not.toBeInTheDocument()
    })

    it('should call retry handler when retry button is clicked', () => {
      const retryableError: AppError = {
        type: ErrorType.SERVER,
        message: 'Server error occurred',
        retryable: true
      }

      const mockRetry = jest.fn()

      render(
        <ErrorDisplay
          error={retryableError}
          onRetry={mockRetry}
          variant="inline"
        />
      )

      fireEvent.click(screen.getByText('Try Again'))
      expect(mockRetry).toHaveBeenCalledTimes(1)
    })

    it('should render banner variant correctly', () => {
      const error: AppError = {
        type: ErrorType.UNKNOWN,
        message: 'Something went wrong',
        retryable: true
      }

      render(
        <ErrorDisplay
          error={error}
          variant="banner"
        />
      )

      // Banner variant should have different styling
      const container = screen.getByText('Something went wrong').closest('div')
      expect(container).toHaveClass('border-l-4')
    })

    it('should show error details when requested', () => {
      const errorWithCode: AppError = {
        type: ErrorType.SERVER,
        message: 'Server error',
        code: '500',
        retryable: true
      }

      render(
        <ErrorDisplay
          error={errorWithCode}
          showDetails={true}
          variant="inline"
        />
      )

      expect(screen.getByText('Error Code: 500')).toBeInTheDocument()
    })
  })
})