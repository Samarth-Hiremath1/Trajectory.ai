'use client'

import { useState, useRef } from 'react'
import { ApiErrorBoundary } from '@/components/error/ApiErrorBoundary'
import { ErrorDisplay } from '@/components/ui/ErrorDisplay'
import { ResumeUploadLoader } from '@/components/ui/WaveformLoader'
import { AppError } from '@/lib/error-utils'

interface ResumeUploadFormProps {
  onSubmit: (resumeFile: File | null) => void
  onBack: () => void
  isSubmitting: boolean
  existingResumeUrl?: string | null
}

export default function ResumeUploadForm({ onSubmit, onBack, isSubmitting, existingResumeUrl }: ResumeUploadFormProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState<AppError | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (file: File) => {
    setValidationError(null)
    
    // Validate file type
    if (file.type !== 'application/pdf') {
      setValidationError({
        type: 'VALIDATION' as any,
        message: 'Please upload a PDF file only',
        retryable: false
      })
      return
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setValidationError({
        type: 'VALIDATION' as any,
        message: 'File size must be less than 10MB',
        retryable: false
      })
      return
    }
    
    setSelectedFile(file)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(selectedFile)
  }

  const handleSkip = () => {
    onSubmit(null)
  }

  const removeFile = () => {
    setSelectedFile(null)
    setValidationError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <ApiErrorBoundary operation="resume upload">
      {isSubmitting ? (
        <ResumeUploadLoader />
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Your Resume</h3>
        <p className="text-sm text-gray-600 mb-4">
          Upload your resume to help our AI understand your background and provide personalized career guidance.
        </p>
      </div>

      <div className="space-y-4">
        {existingResumeUrl && !selectedFile && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <p className="text-sm text-blue-800">
                  <strong>Current Resume:</strong> You have a resume on file.
                </p>
                <a 
                  href={existingResumeUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-500 underline"
                >
                  View current resume
                </a>
              </div>
            </div>
          </div>
        )}

        {!selectedFile ? (
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 ${
              dragActive
                ? 'border-indigo-400 bg-indigo-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    {existingResumeUrl ? 'Upload new resume to replace current one' : 'Drop your resume here, or'}{' '}
                    <span className="text-indigo-600 hover:text-indigo-500">browse</span>
                  </span>
                  <input
                    ref={fileInputRef}
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".pdf"
                    onChange={handleFileInputChange}
                  />
                </label>
                <p className="mt-1 text-xs text-gray-500">PDF up to 10MB</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="border border-gray-300 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="h-8 w-8 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="ml-4 text-sm text-red-600 hover:text-red-500"
              >
                Remove
              </button>
            </div>
          </div>
        )}

        {validationError && (
          <ErrorDisplay
            error={validationError}
            onDismiss={() => setValidationError(null)}
            variant="inline"
          />
        )}
      </div>

      <div className="flex justify-between">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Back
        </button>
        
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={handleSkip}
            disabled={isSubmitting}
            className="flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {existingResumeUrl ? 'Keep Current Resume' : 'Skip for Now'}
          </button>
          
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Creating Profile...' : 'Complete Setup'}
          </button>
        </div>
      </div>
    </form>
      )}
    </ApiErrorBoundary>
  )
}