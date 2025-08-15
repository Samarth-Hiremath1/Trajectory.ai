'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { RoadmapGenerator } from './RoadmapGenerator'
import { RoadmapDisplay } from './RoadmapDisplay'
import StrengthsAnalysis from './StrengthsAnalysis'
import { Roadmap, RoadmapGenerationResponse, RoadmapStatus } from '@/types/roadmap'

export function RoadmapInterface() {
  const { profile } = useAuth()
  const [currentRoadmap, setCurrentRoadmap] = useState<Roadmap | null>(null)
  const [showGenerator, setShowGenerator] = useState(true)
  const [strengthsAnalysis, setStrengthsAnalysis] = useState<any>(null)

  // Load current roadmap from user-specific storage on component mount
  useEffect(() => {
    if (!profile?.user_id) return
    
    // Try to load current roadmap from user-specific localStorage
    try {
      const userStorageKey = `currentRoadmap_${profile.user_id}`
      const storedData = localStorage.getItem(userStorageKey)
      if (storedData) {
        const { roadmap, strengthsAnalysis } = JSON.parse(storedData)
        if (roadmap) {
          // Convert date strings back to Date objects
          const restoredRoadmap: Roadmap = {
            ...roadmap,
            created_date: new Date(roadmap.created_date),
            updated_date: new Date(roadmap.updated_date),
            last_accessed_date: roadmap.last_accessed_date ? new Date(roadmap.last_accessed_date) : undefined
          }
          setCurrentRoadmap(restoredRoadmap)
          setStrengthsAnalysis(strengthsAnalysis)
          setShowGenerator(false)
        }
      }
    } catch (error) {
      console.error('Error loading roadmap from localStorage:', error)
      // Clear invalid data
      const userStorageKey = `currentRoadmap_${profile.user_id}`
      localStorage.removeItem(userStorageKey)
    }
  }, [profile?.user_id])



  const handleRoadmapGenerated = (response: RoadmapGenerationResponse) => {
    console.log('Roadmap generation response:', response) // Debug log
    
    if (!response || !response.roadmap) {
      console.error('Invalid roadmap response:', response)
      return
    }
    
    const roadmap = response.roadmap
    
    // Convert the API response to our Roadmap type
    const convertedRoadmap: Roadmap = {
      id: roadmap.id,
      user_id: roadmap.user_id || profile?.user_id || 'unknown',
      title: roadmap.title,
      description: roadmap.description,
      current_role: roadmap.current_role,
      target_role: roadmap.target_role,
      status: RoadmapStatus.DRAFT,
      phases: roadmap.phases,
      total_estimated_weeks: roadmap.total_estimated_weeks,
      created_date: new Date(roadmap.created_date),
      updated_date: new Date(),
      overall_progress_percentage: 0,
      generated_with_model: roadmap.generation_metadata?.model_used,
      user_context_used: roadmap.generation_metadata?.user_context_used ? {} : undefined
    }
    
    // Store the strengths analysis
    setStrengthsAnalysis(roadmap.strengths_analysis)
    setCurrentRoadmap(convertedRoadmap)
    setShowGenerator(false)
    
    // Store in user-specific localStorage for persistence
    if (profile?.user_id) {
      const userStorageKey = `currentRoadmap_${profile.user_id}`
      localStorage.setItem(userStorageKey, JSON.stringify({
        roadmap: convertedRoadmap,
        strengthsAnalysis: roadmap.strengths_analysis
      }))
    }
  }

  const handlePhaseUpdate = async (phaseNumber: number, updates: Record<string, unknown>) => {
    if (!currentRoadmap) return

    // Update the roadmap locally
    const updatedRoadmap = { ...currentRoadmap }
    const phaseIndex = updatedRoadmap.phases.findIndex(p => p.phase_number === phaseNumber)
    
    if (phaseIndex !== -1) {
      updatedRoadmap.phases[phaseIndex] = {
        ...updatedRoadmap.phases[phaseIndex],
        ...updates
      }
      
      // Recalculate overall progress
      const totalMilestones = updatedRoadmap.phases.reduce((sum, phase) => sum + phase.milestones.length, 0)
      const completedMilestones = updatedRoadmap.phases.reduce(
        (sum, phase) => sum + phase.milestones.filter(m => m.is_completed).length, 
        0
      )
      updatedRoadmap.overall_progress_percentage = totalMilestones > 0 
        ? Math.round((completedMilestones / totalMilestones) * 100) 
        : 0

      setCurrentRoadmap(updatedRoadmap)

      // Save to user-specific localStorage for persistence
      if (profile?.user_id) {
        const userStorageKey = `currentRoadmap_${profile.user_id}`
        localStorage.setItem(userStorageKey, JSON.stringify({
          roadmap: updatedRoadmap,
          strengthsAnalysis: strengthsAnalysis
        }))
      }

      // Save updates to backend
      try {
        const response = await fetch(`/api/roadmap/${updatedRoadmap.id}/progress`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            overall_progress_percentage: updatedRoadmap.overall_progress_percentage,
            current_phase: updatedRoadmap.current_phase,
            phases: updatedRoadmap.phases.map(phase => ({
              phase_number: phase.phase_number,
              title: phase.title,
              description: phase.description,
              duration_weeks: phase.duration_weeks,
              is_completed: phase.is_completed,
              started_date: phase.started_date?.toISOString(),
              completed_date: phase.completed_date?.toISOString(),
              skills_to_develop: phase.skills_to_develop,
              learning_resources: phase.learning_resources,
              milestones: phase.milestones,
              prerequisites: phase.prerequisites,
              outcomes: phase.outcomes
            }))
          })
        })
        
        if (!response.ok) {
          console.error('Failed to save roadmap progress')
        }
      } catch (error) {
        console.error('Error saving roadmap updates:', error)
      }
    }
  }

  const handleEditRoadmap = () => {
    setShowGenerator(true)
  }

  const handleNewRoadmap = () => {
    setCurrentRoadmap(null)
    setShowGenerator(true)
  }



  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Career Roadmap</h1>
          <p className="text-gray-600 mt-1">
            Generate and track your personalized career development plan
          </p>
        </div>
        
        {currentRoadmap && !showGenerator && (
          <div className="flex space-x-3">
            <button
              onClick={handleEditRoadmap}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md font-medium"
            >
              Edit Parameters
            </button>
            <button
              onClick={handleNewRoadmap}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium"
            >
              New Roadmap
            </button>
          </div>
        )}
      </div>



      {/* Main Content */}
      {showGenerator ? (
        <RoadmapGenerator
          onRoadmapGenerated={handleRoadmapGenerated}
          currentRole={profile?.current_role}
          targetRoles={profile?.target_roles}
        />
      ) : currentRoadmap ? (
        <div>
          {/* Show strengths analysis if available */}
          {strengthsAnalysis && (
            <StrengthsAnalysis
              analysis={strengthsAnalysis}
              currentRole={currentRoadmap.current_role}
              targetRole={currentRoadmap.target_role}
            />
          )}
          
          <RoadmapDisplay
            roadmap={currentRoadmap}
            userId={profile?.user_id}
            onPhaseUpdate={handlePhaseUpdate}
            onEdit={handleEditRoadmap}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Roadmap Selected</h3>
          <p className="text-gray-600 mb-4">
            Generate a new career roadmap or select an existing one to get started.
          </p>
          <button
            onClick={handleNewRoadmap}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium"
          >
            Create New Roadmap
          </button>
        </div>
      )}
    </div>
  )
}