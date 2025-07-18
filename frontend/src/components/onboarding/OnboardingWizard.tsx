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
        education: profileData.education,
        career_background: profileData.career_background,
        current_role: profileData.current_role,
        target_roles: profileData.target_roles,
        additional_details: profileData.additional_details
      })

      if (!profile) {
        throw new Error('Failed to create profile')
      }

      // TODO: Handle resume file upload to storage
      // For now, we'll just store the file reference
      if (file) {
        console.log('Resume file selected:', file.name, file.size)
        // In a future implementation, upload to Supabase Storage:
        // const resumeUrl = await uploadResumeToStorage(user.id, file)
        // await updateProfile(user.id, { resume_url: resumeUrl })
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