'use client'

import { LoadingSpinner } from './LoadingSpinner'
import { ProgressIndicator } from './ProgressIndicator'

interface LoadingStateProps {
  type?: 'spinner' | 'progress' | 'skeleton'
  message?: string
  progress?: number
  size?: 'sm' | 'md' | 'lg'
  className?: string
  children?: React.ReactNode
}

export function LoadingState({
  type = 'spinner',
  message,
  progress,
  size = 'md',
  className = '',
  children
}: LoadingStateProps) {
  if (type === 'skeleton') {
    return (
      <div className={`animate-pulse ${className}`}>
        {children || (
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        )}
      </div>
    )
  }

  if (type === 'progress' && typeof progress === 'number') {
    return (
      <div className={`flex flex-col items-center justify-center p-6 ${className}`}>
        <ProgressIndicator
          progress={progress}
          label={message}
          showPercentage
          size={size}
          className="w-full max-w-xs mb-4"
        />
        {message && (
          <p className="text-sm text-gray-600 text-center">{message}</p>
        )}
      </div>
    )
  }

  // Default spinner type
  return (
    <div className={`flex flex-col items-center justify-center p-6 ${className}`}>
      <LoadingSpinner size={size} className="mb-4" />
      {message && (
        <p className="text-sm text-gray-600 text-center">{message}</p>
      )}
    </div>
  )
}

// Specific loading states for common operations
export function ChatLoadingState() {
  return (
    <LoadingState
      message="Connecting to AI mentor..."
      className="min-h-[200px]"
    />
  )
}

export function RoadmapLoadingState({ progress }: { progress?: number }) {
  return (
    <LoadingState
      type={typeof progress === 'number' ? 'progress' : 'spinner'}
      progress={progress}
      message={
        typeof progress === 'number'
          ? 'Generating your personalized roadmap...'
          : 'Analyzing your profile and generating roadmap...'
      }
      className="min-h-[300px]"
    />
  )
}

export function ResumeUploadLoadingState({ progress }: { progress?: number }) {
  return (
    <LoadingState
      type={typeof progress === 'number' ? 'progress' : 'spinner'}
      progress={progress}
      message={
        typeof progress === 'number'
          ? 'Processing your resume...'
          : 'Uploading and analyzing resume...'
      }
      className="min-h-[150px]"
    />
  )
}

export function ProfileLoadingState() {
  return (
    <LoadingState
      type="skeleton"
      className="space-y-4 p-4"
    >
      <div className="h-6 bg-gray-200 rounded w-1/4"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
      <div className="h-6 bg-gray-200 rounded w-1/3"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        <div className="h-4 bg-gray-200 rounded w-4/5"></div>
      </div>
    </LoadingState>
  )
}