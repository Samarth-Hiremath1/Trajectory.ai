'use client'

import { useState } from 'react'
import { RoadmapRequest, CareerSuggestion, RoadmapGenerationResponse } from '@/types/roadmap'

interface RoadmapGeneratorProps {
  onRoadmapGenerated: (roadmap: RoadmapGenerationResponse['roadmap']) => void
  currentRole?: string
  targetRoles?: string[]
}

export function RoadmapGenerator({ 
  onRoadmapGenerated, 
  currentRole = '', 
  targetRoles = [] 
}: RoadmapGeneratorProps) {
  const [formData, setFormData] = useState<RoadmapRequest>({
    current_role: currentRole,
    target_role: targetRoles[0] || '',
    user_background: '',
    timeline_preference: '',
    focus_areas: [],
    constraints: []
  })
  
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)
  const [focusAreaInput, setFocusAreaInput] = useState('')
  const [constraintInput, setConstraintInput] = useState('')

  const handleGetSuggestions = async () => {
    if (!formData.current_role.trim()) return
    
    setIsLoadingSuggestions(true)
    try {
      const response = await fetch(
        `/api/roadmap/suggestions/${encodeURIComponent(formData.current_role)}?user_background=${encodeURIComponent(formData.user_background || '')}`
      )
      
      if (response.ok) {
        const data: CareerSuggestion = await response.json()
        setSuggestions(data.suggestions)
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error)
    } finally {
      setIsLoadingSuggestions(false)
    }
  }

  const handleAddFocusArea = () => {
    if (focusAreaInput.trim() && !formData.focus_areas.includes(focusAreaInput.trim())) {
      setFormData(prev => ({
        ...prev,
        focus_areas: [...prev.focus_areas, focusAreaInput.trim()]
      }))
      setFocusAreaInput('')
    }
  }

  const handleRemoveFocusArea = (area: string) => {
    setFormData(prev => ({
      ...prev,
      focus_areas: prev.focus_areas.filter(a => a !== area)
    }))
  }

  const handleAddConstraint = () => {
    if (constraintInput.trim() && !formData.constraints.includes(constraintInput.trim())) {
      setFormData(prev => ({
        ...prev,
        constraints: [...prev.constraints, constraintInput.trim()]
      }))
      setConstraintInput('')
    }
  }

  const handleRemoveConstraint = (constraint: string) => {
    setFormData(prev => ({
      ...prev,
      constraints: prev.constraints.filter(c => c !== constraint)
    }))
  }

  const handleGenerateRoadmap = async () => {
    if (!formData.current_role.trim() || !formData.target_role.trim()) {
      alert('Please fill in both current and target roles')
      return
    }

    setIsGenerating(true)
    try {
      const response = await fetch('/api/roadmap/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          onRoadmapGenerated(data.roadmap)
        } else {
          alert('Failed to generate roadmap. Please try again.')
        }
      } else {
        alert('Error generating roadmap. Please try again.')
      }
    } catch (error) {
      console.error('Error generating roadmap:', error)
      alert('Error generating roadmap. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Generate Career Roadmap</h2>
      
      <div className="space-y-6">
        {/* Current Role */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Current Role *
          </label>
          <input
            type="text"
            value={formData.current_role}
            onChange={(e) => setFormData(prev => ({ ...prev, current_role: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g., Junior Software Engineer"
          />
        </div>

        {/* Target Role */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Role *
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={formData.target_role}
              onChange={(e) => setFormData(prev => ({ ...prev, target_role: e.target.value }))}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Senior Software Engineer"
            />
            <button
              onClick={handleGetSuggestions}
              disabled={!formData.current_role.trim() || isLoadingSuggestions}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 text-gray-700 rounded-md text-sm font-medium"
            >
              {isLoadingSuggestions ? 'Loading...' : 'Get Suggestions'}
            </button>
          </div>
          
          {/* Career Suggestions */}
          {suggestions.length > 0 && (
            <div className="mt-3">
              <p className="text-sm text-gray-600 mb-2">Suggested career paths:</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setFormData(prev => ({ ...prev, target_role: suggestion }))}
                    className="px-3 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-full text-sm"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Background */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Background & Experience
          </label>
          <textarea
            value={formData.user_background}
            onChange={(e) => setFormData(prev => ({ ...prev, user_background: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Describe your current experience, skills, and relevant background..."
          />
        </div>

        {/* Timeline Preference */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Timeline Preference
          </label>
          <select
            value={formData.timeline_preference}
            onChange={(e) => setFormData(prev => ({ ...prev, timeline_preference: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select timeline...</option>
            <option value="3 months">3 months</option>
            <option value="6 months">6 months</option>
            <option value="1 year">1 year</option>
            <option value="2 years">2 years</option>
            <option value="flexible">Flexible</option>
          </select>
        </div>

        {/* Focus Areas */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Focus Areas
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={focusAreaInput}
              onChange={(e) => setFocusAreaInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddFocusArea()}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., system design, leadership skills"
            />
            <button
              onClick={handleAddFocusArea}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.focus_areas.map((area, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm"
              >
                {area}
                <button
                  onClick={() => handleRemoveFocusArea(area)}
                  className="ml-2 text-indigo-600 hover:text-indigo-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Constraints */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Constraints
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={constraintInput}
              onChange={(e) => setConstraintInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddConstraint()}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., limited time on weekends, budget constraints"
            />
            <button
              onClick={handleAddConstraint}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md text-sm font-medium"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.constraints.map((constraint, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm"
              >
                {constraint}
                <button
                  onClick={() => handleRemoveConstraint(constraint)}
                  className="ml-2 text-gray-600 hover:text-gray-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <div className="pt-4">
          <button
            onClick={handleGenerateRoadmap}
            disabled={isGenerating || !formData.current_role.trim() || !formData.target_role.trim()}
            className="w-full px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md font-medium text-lg"
          >
            {isGenerating ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Generating Roadmap...
              </div>
            ) : (
              'Generate Career Roadmap'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}