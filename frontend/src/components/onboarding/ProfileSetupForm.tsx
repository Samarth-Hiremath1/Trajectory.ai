'use client'

import { useState } from 'react'

export interface ProfileFormData {
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

interface ProfileSetupFormProps {
  initialData: ProfileFormData
  onSubmit: (data: ProfileFormData) => void
  isSubmitting: boolean
}

export default function ProfileSetupForm({ initialData, onSubmit, isSubmitting }: ProfileSetupFormProps) {
  const [formData, setFormData] = useState<ProfileFormData>(initialData)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // Education validation
    if (!formData.education.degree.trim()) {
      newErrors['education.degree'] = 'Degree is required'
    }
    if (!formData.education.field.trim()) {
      newErrors['education.field'] = 'Field of study is required'
    }
    if (!formData.education.institution.trim()) {
      newErrors['education.institution'] = 'Institution is required'
    }
    if (!formData.education.graduationYear.trim()) {
      newErrors['education.graduationYear'] = 'Graduation year is required'
    } else {
      const year = parseInt(formData.education.graduationYear)
      const currentYear = new Date().getFullYear()
      if (isNaN(year) || year < 1950 || year > currentYear + 10) {
        newErrors['education.graduationYear'] = 'Please enter a valid graduation year'
      }
    }

    // Career background validation
    if (!formData.career_background.trim()) {
      newErrors.career_background = 'Career background is required'
    } else if (formData.career_background.trim().length < 10) {
      newErrors.career_background = 'Please provide more details about your career background (at least 10 characters)'
    }

    // Current role validation
    if (!formData.current_role.trim()) {
      newErrors.current_role = 'Current role is required'
    }

    // Target roles validation
    if (formData.target_roles.length === 0) {
      newErrors.target_roles = 'At least one target role is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      onSubmit(formData)
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
    // Clear error when user starts typing
    if (errors[`education.${field}`]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[`education.${field}`]
        return newErrors
      })
    }
  }

  const handleTargetRoleAdd = (role: string) => {
    if (role.trim() && !formData.target_roles.includes(role.trim())) {
      setFormData(prev => ({
        ...prev,
        target_roles: [...prev.target_roles, role.trim()]
      }))
      // Clear error when user adds a role
      if (errors.target_roles) {
        setErrors(prev => {
          const newErrors = { ...prev }
          delete newErrors.target_roles
          return newErrors
        })
      }
    }
  }

  const handleTargetRoleRemove = (roleToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      target_roles: prev.target_roles.filter(role => role !== roleToRemove)
    }))
  }

  const [newTargetRole, setNewTargetRole] = useState('')

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Education Background</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="degree" className="block text-sm font-medium text-gray-700">
              Degree *
            </label>
            <input
              type="text"
              id="degree"
              value={formData.education.degree}
              onChange={(e) => handleEducationChange('degree', e.target.value)}
              className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                errors['education.degree'] ? 'border-red-300' : ''
              }`}
              placeholder="e.g., Bachelor's, Master's, PhD"
            />
            {errors['education.degree'] && (
              <p className="mt-1 text-sm text-red-600">{errors['education.degree']}</p>
            )}
          </div>

          <div>
            <label htmlFor="field" className="block text-sm font-medium text-gray-700">
              Field of Study *
            </label>
            <input
              type="text"
              id="field"
              value={formData.education.field}
              onChange={(e) => handleEducationChange('field', e.target.value)}
              className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                errors['education.field'] ? 'border-red-300' : ''
              }`}
              placeholder="e.g., Computer Science, Business, Engineering"
            />
            {errors['education.field'] && (
              <p className="mt-1 text-sm text-red-600">{errors['education.field']}</p>
            )}
          </div>

          <div>
            <label htmlFor="institution" className="block text-sm font-medium text-gray-700">
              Institution *
            </label>
            <input
              type="text"
              id="institution"
              value={formData.education.institution}
              onChange={(e) => handleEducationChange('institution', e.target.value)}
              className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                errors['education.institution'] ? 'border-red-300' : ''
              }`}
              placeholder="e.g., Stanford University, MIT"
            />
            {errors['education.institution'] && (
              <p className="mt-1 text-sm text-red-600">{errors['education.institution']}</p>
            )}
          </div>

          <div>
            <label htmlFor="graduationYear" className="block text-sm font-medium text-gray-700">
              Graduation Year *
            </label>
            <input
              type="number"
              id="graduationYear"
              value={formData.education.graduationYear}
              onChange={(e) => handleEducationChange('graduationYear', e.target.value)}
              className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                errors['education.graduationYear'] ? 'border-red-300' : ''
              }`}
              placeholder="e.g., 2023"
              min="1950"
              max={new Date().getFullYear() + 10}
            />
            {errors['education.graduationYear'] && (
              <p className="mt-1 text-sm text-red-600">{errors['education.graduationYear']}</p>
            )}
          </div>
        </div>
      </div>

      <div>
        <label htmlFor="career_background" className="block text-sm font-medium text-gray-700">
          Career Background *
        </label>
        <textarea
          id="career_background"
          rows={4}
          value={formData.career_background}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, career_background: e.target.value }))
            if (errors.career_background) {
              setErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors.career_background
                return newErrors
              })
            }
          }}
          className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
            errors.career_background ? 'border-red-300' : ''
          }`}
          placeholder="Tell us about your work experience, internships, projects, and any relevant background..."
        />
        {errors.career_background && (
          <p className="mt-1 text-sm text-red-600">{errors.career_background}</p>
        )}
      </div>

      <div>
        <label htmlFor="current_role" className="block text-sm font-medium text-gray-700">
          Current Role *
        </label>
        <input
          type="text"
          id="current_role"
          value={formData.current_role}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, current_role: e.target.value }))
            if (errors.current_role) {
              setErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors.current_role
                return newErrors
              })
            }
          }}
          className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
            errors.current_role ? 'border-red-300' : ''
          }`}
          placeholder="e.g., Software Engineer, Student, Product Manager"
        />
        {errors.current_role && (
          <p className="mt-1 text-sm text-red-600">{errors.current_role}</p>
        )}
      </div>

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
        {errors.target_roles && (
          <p className="mt-1 text-sm text-red-600">{errors.target_roles}</p>
        )}
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

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Processing...' : 'Continue to Resume Upload'}
        </button>
      </div>
    </form>
  )
}