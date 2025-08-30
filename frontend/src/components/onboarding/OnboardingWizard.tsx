'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { createProfile } from '@/lib/profile'
import ProfileSetupForm, { ProfileFormData } from './ProfileSetupForm'
import ResumeUploadForm from './ResumeUploadForm'
import ProgressIndicator from './ProgressIndicator'

const STEPS = [
  { id: 1, name: 'Profile Setup', description: 'Tell us about your background' },
  { id: 2, name: 'Resume Upload', description: 'Upload your resume for AI analysis' },
  { id: 3, name: 'Complete', description: 'Finish setup and start your journey' }
]

export default function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(1)
  const [profileData, setProfileData] = useState<ProfileFormData>({
    name: '',
    education: {
      degree: '',
      field: '',
      institution: '',
      graduationYear: ''
    },
    career_background: '',
    current_role: '',
    target_roles: [],
    additional_details: ''
  })
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [storageNotification, setStorageNotification] = useState<any>(null)
  
  const { user, refreshProfile } = useAuth()
  const router = useRouter()

  const handleProfileSubmit = (data: ProfileFormData) => {
    setProfileData(data)
    setCurrentStep(2)
  }

  const handleResumeSubmit = async (file: File | null) => {
    if (!user) {
      setError('User not authenticated')
      return
    }

    setIsSubmitting(true)
    setError(null)
    setResumeFile(file)

    try {
      // Create profile in Supabase
      const profile = await createProfile(user.id, {
        name: profileData.name,
        education: profileData.education,
        career_background: profileData.career_background,
        current_role: profileData.current_role,
        target_roles: profileData.target_roles,
        additional_details: profileData.additional_details
      })

      if (!profile) {
        throw new Error('Failed to create profile')
      }

      // Upload resume file to backend if provided
      if (file) {
        console.log('Uploading resume file:', file.name, file.size)
        
        const formData = new FormData()
        formData.append('file', file)
        formData.append('user_id', user.id)
        
        const resumeResponse = await fetch('/api/resume/upload', {
          method: 'POST',
          body: formData
        })
        
        if (!resumeResponse.ok) {
          const errorData = await resumeResponse.json().catch(() => ({}))
          throw new Error(errorData.detail || 'Failed to upload resume')
        }
        
        const resumeResult = await resumeResponse.json()
        console.log('Resume upload result:', resumeResult)
        
        // Check if there's an error message in the response
        if (resumeResult.error_message) {
          throw new Error(resumeResult.error_message)
        }
        
        // Handle storage notifications
        if (resumeResult.notification) {
          setStorageNotification(resumeResult.notification)
        }
        
        // If we got here and the response was 200 OK, the upload was successful
      }

      // Refresh chat service context to include both profile and resume data
      try {
        const contextResponse = await fetch(`/api/chat/users/${user.id}/refresh-context`, {
          method: 'POST'
        })
        
        if (contextResponse.ok) {
          const contextResult = await contextResponse.json()
          console.log('Chat context refresh result:', contextResult)
        } else {
          console.warn('Failed to refresh chat context, but continuing with onboarding')
        }
      } catch (contextError) {
        console.warn('Error refreshing chat context:', contextError)
        // Don't fail onboarding for this
      }

      // Refresh the profile in auth context
      await refreshProfile()
      
      setCurrentStep(3)
    } catch (err) {
      console.error('Error creating profile:', err)
      setError(err instanceof Error ? err.message : 'Failed to create profile')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleComplete = () => {
    router.push('/dashboard')
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">
            Welcome to Trajectory.AI
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Let&apos;s set up your profile to get personalized career guidance
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-2xl">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <ProgressIndicator steps={STEPS} currentStep={currentStep} />
          
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    {error}
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {storageNotification && (
            <div className={`mb-6 p-4 border rounded-md ${
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

          <div className="mt-8">
            {currentStep === 1 && (
              <ProfileSetupForm
                initialData={profileData}
                onSubmit={handleProfileSubmit}
                isSubmitting={isSubmitting}
              />
            )}
            
            {currentStep === 2 && (
              <ResumeUploadForm
                onSubmit={handleResumeSubmit}
                onBack={handleBack}
                isSubmitting={isSubmitting}
              />
            )}
            
            {currentStep === 3 && (
              <div className="text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Setup Complete!
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  Your profile has been created successfully. You&apos;re ready to start your career journey with AI-powered guidance.
                </p>
                {resumeFile && (
                  <p className="mt-2 text-sm text-green-600">
                    ✓ Resume uploaded: {resumeFile.name}
                  </p>
                )}
                <button
                  onClick={handleComplete}
                  className="mt-6 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Go to Dashboard
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}