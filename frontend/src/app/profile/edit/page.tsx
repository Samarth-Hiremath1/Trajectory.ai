'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { updateProfile } from '@/lib/profile'
import ResumeUploadSection from '@/components/profile/ResumeUploadSection'
interface ProfileFormData {
  education: {
    degree: string
    field: string
    institution: string
    graduationYear: string
  }
  career_background: string
  current_role: string
  target_roles: string[]
  additional_details: string
}

export default function EditProfilePage() {
  const { user, profile, loading, profileLoading, refreshProfile } = useAuth()
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [formData, setFormData] = useState<ProfileFormData>({
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
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
      return
    }
    if (!loading && user && !profile) {
      router.push('/onboarding')
      return
    }
    
    // Populate form with existing profile data only once
    if (profile && !isInitialized) {
      const educationData = typeof profile.education === 'object' && profile.education !== null 
        ? profile.education as Record<string, string>
        : {}
      
      setFormData({
        education: {
          degree: educationData.degree || '',
          field: educationData.field || '',
          institution: educationData.institution || '',
          graduationYear: educationData.graduationYear || ''
        },
        career_background: profile.career_background || '',
        current_role: profile.current_role || '',
        target_roles: Array.isArray(profile.target_roles) ? profile.target_roles : [],
        additional_details: profile.additional_details || ''
      })
      setIsInitialized(true)
    }
  }, [user, profile, loading, router, isInitialized])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) return

    setIsSubmitting(true)
    setError(null)
    setSuccess(false)

    try {
      const updatedProfile = await updateProfile(user.id, {
        education: formData.education,
        career_background: formData.career_background,
        current_role: formData.current_role,
        target_roles: formData.target_roles,
        additional_details: formData.additional_details
      })

      if (!updatedProfile) {
        throw new Error('Failed to update profile')
      }

      await refreshProfile()
      setSuccess(true)
      
      // Redirect to dashboard after successful update
      setTimeout(() => {
        router.push('/dashboard')
      }, 2000)
    } catch (err) {
      console.error('Error updating profile:', err)
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEducationChange = (field: keyof ProfileFormData['education'], value: string) => {
    setFormData(prev => ({
      ...prev,
      education: {
        ...prev.education,
        [field]: value
      }
    }))
  }

  const handleTargetRoleAdd = (role: string) => {
    if (role.trim() && !formData.target_roles.includes(role.trim())) {
      setFormData(prev => ({
        ...prev,
        target_roles: [...prev.target_roles, role.trim()]
      }))
    }
  }

  const handleTargetRoleRemove = (roleToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      target_roles: prev.target_roles.filter(role => role !== roleToRemove)
    }))
  }

  const [newTargetRole, setNewTargetRole] = useState('')

  if (loading || profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!user || !profile) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-indigo-600 hover:text-indigo-500 mr-4"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">
                Edit Profile
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">{error}</div>
                  </div>
                </div>
              </div>
            )}

            {success && (
              <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-green-800">Success</h3>
                    <div className="mt-2 text-sm text-green-700">
                      Profile updated successfully! Redirecting to dashboard...
                    </div>
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Education Background</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="degree" className="block text-sm font-medium text-gray-700">
                      Degree
                    </label>
                    <input
                      type="text"
                      id="degree"
                      value={formData.education.degree}
                      onChange={(e) => handleEducationChange('degree', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="e.g., Bachelor's, Master's, PhD"
                    />
                  </div>

                  <div>
                    <label htmlFor="field" className="block text-sm font-medium text-gray-700">
                      Field of Study
                    </label>
                    <input
                      type="text"
                      id="field"
                      value={formData.education.field}
                      onChange={(e) => handleEducationChange('field', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="e.g., Computer Science, Business, Engineering"
                    />
                  </div>

                  <div>
                    <label htmlFor="institution" className="block text-sm font-medium text-gray-700">
                      Institution
                    </label>
                    <input
                      type="text"
                      id="institution"
                      value={formData.education.institution}
                      onChange={(e) => handleEducationChange('institution', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="e.g., Stanford University, MIT"
                    />
                  </div>

                  <div>
                    <label htmlFor="graduationYear" className="block text-sm font-medium text-gray-700">
                      Graduation Year
                    </label>
                    <input
                      type="number"
                      id="graduationYear"
                      value={formData.education.graduationYear}
                      onChange={(e) => handleEducationChange('graduationYear', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="e.g., 2023"
                      min="1950"
                      max={new Date().getFullYear() + 10}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label htmlFor="career_background" className="block text-sm font-medium text-gray-700">
                  Career Background
                </label>
                <textarea
                  id="career_background"
                  rows={4}
                  value={formData.career_background}
                  onChange={(e) => setFormData(prev => ({ ...prev, career_background: e.target.value }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Tell us about your work experience, internships, projects, and any relevant background..."
                />
              </div>

              <div>
                <label htmlFor="current_role" className="block text-sm font-medium text-gray-700">
                  Current Role
                </label>
                <input
                  type="text"
                  id="current_role"
                  value={formData.current_role}
                  onChange={(e) => setFormData(prev => ({ ...prev, current_role: e.target.value }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., Software Engineer, Student, Product Manager"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Target Roles
                </label>
                <div className="mt-1">
                  <div className="flex flex-wrap gap-2 mb-2">
                    {formData.target_roles.map((role, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800"
                      >
                        {role}
                        <button
                          type="button"
                          onClick={() => handleTargetRoleRemove(role)}
                          className="ml-2 inline-flex items-center justify-center w-4 h-4 rounded-full text-indigo-400 hover:bg-indigo-200 hover:text-indigo-600"
                        >
                          <span className="sr-only">Remove {role}</span>
                          <svg className="w-2 h-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">
                            <path strokeLinecap="round" strokeWidth="1.5" d="m1 1 6 6m0-6L1 7" />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex">
                    <input
                      type="text"
                      value={newTargetRole}
                      onChange={(e) => setNewTargetRole(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          handleTargetRoleAdd(newTargetRole)
                          setNewTargetRole('')
                        }
                      }}
                      className="flex-1 border-gray-300 rounded-l-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="e.g., Software Engineer at FAANG, Product Manager at Meta"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        handleTargetRoleAdd(newTargetRole)
                        setNewTargetRole('')
                      }}
                      className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 text-sm hover:bg-gray-100"
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label htmlFor="additional_details" className="block text-sm font-medium text-gray-700">
                  Additional Details
                </label>
                <textarea
                  id="additional_details"
                  rows={3}
                  value={formData.additional_details}
                  onChange={(e) => setFormData(prev => ({ ...prev, additional_details: e.target.value }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Any additional information that might help us provide better career guidance..."
                />
              </div>

              {/* Resume Upload Section */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Resume
                </label>
                <ResumeUploadSection />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => router.push('/dashboard')}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}