'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { createProfile } from '@/lib/profile'

interface FormData {
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

export default function SimpleOnboardingForm() {
  const [formData, setFormData] = useState<FormData>({
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
  
  const [newTargetRole, setNewTargetRole] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { user, refreshProfile } = useAuth()
  const router = useRouter()

  const handleEducationChange = (field: keyof FormData['education'], value: string) => {
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
      setNewTargetRole('')
    }
  }

  const handleTargetRoleRemove = (roleToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      target_roles: prev.target_roles.filter(role => role !== roleToRemove)
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) {
      setError('User not authenticated')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const profile = await createProfile(user.id, {
        education: formData.education,
        career_background: formData.career_background,
        current_role: formData.current_role,
        target_roles: formData.target_roles,
        additional_details: formData.additional_details
      })

      if (!profile) {
        throw new Error('Failed to create profile')
      }

      // Refresh the profile in auth context
      await refreshProfile()
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (err) {
      console.error('Error creating profile:', err)
      setError(err instanceof Error ? err.message : 'Failed to create profile')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">
            Complete Your Profile
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Tell us about yourself to get personalized career guidance
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-2xl">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
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

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Education Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Education</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="degree" className="block text-sm font-medium text-gray-700">
                    Degree *
                  </label>
                  <input
                    type="text"
                    id="degree"
                    required
                    value={formData.education.degree}
                    onChange={(e) => handleEducationChange('degree', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., Bachelor's, Master's, PhD"
                  />
                </div>

                <div>
                  <label htmlFor="field" className="block text-sm font-medium text-gray-700">
                    Field of Study *
                  </label>
                  <input
                    type="text"
                    id="field"
                    required
                    value={formData.education.field}
                    onChange={(e) => handleEducationChange('field', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., Computer Science, Business"
                  />
                </div>

                <div>
                  <label htmlFor="institution" className="block text-sm font-medium text-gray-700">
                    Institution *
                  </label>
                  <input
                    type="text"
                    id="institution"
                    required
                    value={formData.education.institution}
                    onChange={(e) => handleEducationChange('institution', e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., Stanford University"
                  />
                </div>

                <div>
                  <label htmlFor="graduationYear" className="block text-sm font-medium text-gray-700">
                    Graduation Year *
                  </label>
                  <input
                    type="number"
                    id="graduationYear"
                    required
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

            {/* Career Background */}
            <div>
              <label htmlFor="career_background" className="block text-sm font-medium text-gray-700">
                Career Background *
              </label>
              <textarea
                id="career_background"
                rows={4}
                required
                value={formData.career_background}
                onChange={(e) => setFormData(prev => ({ ...prev, career_background: e.target.value }))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Tell us about your work experience, internships, projects..."
              />
            </div>

            {/* Current Role */}
            <div>
              <label htmlFor="current_role" className="block text-sm font-medium text-gray-700">
                Current Role *
              </label>
              <input
                type="text"
                id="current_role"
                required
                value={formData.current_role}
                onChange={(e) => setFormData(prev => ({ ...prev, current_role: e.target.value }))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="e.g., Software Engineer, Student, Product Manager"
              />
            </div>

            {/* Target Roles */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Target Roles *
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
                      }
                    }}
                    className="flex-1 border-gray-300 rounded-l-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., Software Engineer at FAANG"
                  />
                  <button
                    type="button"
                    onClick={() => handleTargetRoleAdd(newTargetRole)}
                    className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 text-sm hover:bg-gray-100"
                  >
                    Add
                  </button>
                </div>
                {formData.target_roles.length === 0 && (
                  <p className="mt-1 text-sm text-red-600">Please add at least one target role</p>
                )}
              </div>
            </div>

            {/* Additional Details */}
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

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={isSubmitting || formData.target_roles.length === 0}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating Profile...' : 'Complete Setup'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}