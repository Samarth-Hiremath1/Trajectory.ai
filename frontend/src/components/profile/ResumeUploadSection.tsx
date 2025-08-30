'use client'

import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { ResumeUploadLoader } from '@/components/ui/WaveformLoader'

interface ResumeUploadSectionProps {
  onUploadSuccess?: () => void
  onUploadError?: (error: string) => void
}

export default function ResumeUploadSection({ 
  onUploadSuccess, 
  onUploadError 
}: ResumeUploadSectionProps = {}) {
  const { user } = useAuth()
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [storageNotification, setStorageNotification] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Get existing resume info from backend
  const [existingResume, setExistingResume] = useState<any>(null)
  const [loadingExistingResume, setLoadingExistingResume] = useState(true)

  // Load existing resume on component mount
  useEffect(() => {
    const loadExistingResume = async () => {
      if (!user) return
      
      try {
        setLoadingExistingResume(true)
        const response = await fetch(`/api/resume/user/${user.id}`)
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.resume) {
            setExistingResume(data.resume)
          }
        }
      } catch (error) {
        console.error('Error loading existing resume:', error)
      } finally {
        setLoadingExistingResume(false)
      }
    }

    loadExistingResume()
  }, [user])

  const existingResumeUrl = existingResume?.filename ? `/api/resume/download/${existingResume.id}` : null

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
    setUploadError(null)
    
    // Validate file type
    if (file.type !== 'application/pdf') {
      setUploadError('Please upload a PDF file only')
      return
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size must be less than 10MB')
      return
    }
    
    setSelectedFile(file)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !user) return

    setIsUploading(true)
    setUploadError(null)
    setUploadSuccess(false)

    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Upload to backend API
      const response = await fetch('/api/resume/upload', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type header - let browser set it with boundary for FormData
          'Authorization': `Bearer ${user.id}`, // TODO: Replace with proper auth token
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(errorData.detail || 'Upload failed')
      }

      const result = await response.json()
      
      // Handle storage notifications
      if (result.notification) {
        setStorageNotification(result.notification)
      }
      
      setUploadSuccess(true)
      setSelectedFile(null)
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Refresh existing resume data
      const refreshResponse = await fetch(`/api/resume/user/${user.id}`)
      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json()
        if (refreshData.success && refreshData.resume) {
          setExistingResume(refreshData.resume)
        }
      }

      // Call success callback if provided
      if (onUploadSuccess) {
        onUploadSuccess()
      }

      // Show success message briefly
      setTimeout(() => {
        setUploadSuccess(false)
      }, 3000)

    } catch (error) {
      console.error('Upload error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload resume. Please try again.'
      setUploadError(errorMessage)
      
      // Call error callback if provided
      if (onUploadError) {
        onUploadError(errorMessage)
      }
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    setUploadError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-4">
      {loadingExistingResume && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600 mr-2"></div>
            <p className="text-sm text-gray-600">Checking for existing resume...</p>
          </div>
        </div>
      )}

      {existingResume && !selectedFile && !loadingExistingResume && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <p className="text-sm text-blue-800">
                <strong>Current Resume:</strong> {existingResume.filename}
              </p>
              <p className="text-xs text-blue-600 mt-1">
                Uploaded on {new Date(existingResume.upload_date).toLocaleDateString()}
                {existingResume.file_size && ` • ${(existingResume.file_size / 1024 / 1024).toFixed(2)} MB`}
              </p>
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
              <label htmlFor="resume-upload" className="cursor-pointer">
                <span className="mt-2 block text-sm font-medium text-gray-900">
                  {existingResumeUrl ? 'Upload new resume to replace current one' : 'Drop your resume here, or'}{' '}
                  <span className="text-indigo-600 hover:text-indigo-500">browse</span>
                </span>
                <input
                  ref={fileInputRef}
                  id="resume-upload"
                  name="resume-upload"
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
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleUpload}
                disabled={isUploading}
                className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded disabled:opacity-50"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                type="button"
                onClick={removeFile}
                disabled={isUploading}
                className="text-sm text-red-600 hover:text-red-500 disabled:opacity-50"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {uploadSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">
                Resume uploaded successfully! Your AI context has been updated with the new resume content.
              </p>
            </div>
          </div>
        </div>
      )}

      {isUploading && (
        <ResumeUploadLoader />
      )}

      {storageNotification && (
        <div className={`mb-4 p-4 border rounded-md ${
          storageNotification.type === 'warning' 
            ? 'bg-yellow-50 border-yellow-200' 
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className={`h-5 w-5 ${
                storageNotification.type === 'warning' ? 'text-yellow-400' : 'text-blue-400'
              }`} viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${
                storageNotification.type === 'warning' ? 'text-yellow-800' : 'text-blue-800'
              }`}>
                {storageNotification.title}
              </h3>
              <p className={`mt-1 text-sm ${
                storageNotification.type === 'warning' ? 'text-yellow-700' : 'text-blue-700'
              }`}>
                {storageNotification.message}
              </p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setStorageNotification(null)}
                className={`inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  storageNotification.type === 'warning' 
                    ? 'text-yellow-500 hover:bg-yellow-100 focus:ring-yellow-600' 
                    : 'text-blue-500 hover:bg-blue-100 focus:ring-blue-600'
                }`}
              >
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {uploadError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{uploadError}</p>
            </div>
          </div>
        </div>
      )}


    </div>
  )
}