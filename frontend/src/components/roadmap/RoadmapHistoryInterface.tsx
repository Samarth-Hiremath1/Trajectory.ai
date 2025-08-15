'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { RoadmapGenerator } from './RoadmapGenerator'
import { RoadmapDisplay } from './RoadmapDisplay'
import { RoadmapChat } from './RoadmapChat'
import StrengthsAnalysis from './StrengthsAnalysis'
import { Roadmap, RoadmapGenerationResponse, RoadmapStatus } from '@/types/roadmap'

interface RoadmapSummary {
  id: string
  title: string
  current_role: string
  target_role: string
  status: RoadmapStatus
  total_estimated_weeks: number
  phase_count: number
  overall_progress_percentage: number
  created_date: Date
  updated_date: Date
  last_accessed_date?: Date
}

export function RoadmapHistoryInterface() {
  const { profile } = useAuth()
  const [selectedRoadmap, setSelectedRoadmap] = useState<Roadmap | null>(null)
  const [showGenerator, setShowGenerator] = useState(false)
  const [roadmapHistory, setRoadmapHistory] = useState<RoadmapSummary[]>([])
  const [strengthsAnalysis, setStrengthsAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [loadingRoadmap, setLoadingRoadmap] = useState(false)

  // Load roadmap history on component mount
  useEffect(() => {
    loadRoadmapHistory()
  }, [])

  // Restore selected roadmap from localStorage on component mount
  useEffect(() => {
    const restoreSelectedRoadmap = async () => {
      try {
        const storedRoadmapId = localStorage.getItem('selectedRoadmapId')
        if (storedRoadmapId && roadmapHistory.length > 0) {
          // Check if the stored roadmap ID exists in our history
          const roadmapExists = roadmapHistory.find(r => r.id === storedRoadmapId)
          if (roadmapExists) {
            await loadFullRoadmap(storedRoadmapId)
          } else {
            // Clear invalid stored ID
            localStorage.removeItem('selectedRoadmapId')
          }
        }
      } catch (error) {
        console.error('Error restoring selected roadmap:', error)
        localStorage.removeItem('selectedRoadmapId')
      }
    }

    if (roadmapHistory.length > 0 && !selectedRoadmap && !showGenerator) {
      restoreSelectedRoadmap()
    }
  }, [roadmapHistory, selectedRoadmap, showGenerator])

  const loadRoadmapHistory = async () => {
    try {
      setLoading(true)
      const userId = 'temp_user_123' // TODO: Get from auth context
      const response = await fetch(`/api/roadmap/user/${userId}`)
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          // Convert API response to RoadmapSummary objects and sort chronologically
          const roadmaps: RoadmapSummary[] = data.roadmaps
            .map((r: any) => ({
              id: r.id,
              title: r.title,
              current_role: r.current_role,
              target_role: r.target_role,
              status: r.status as RoadmapStatus,
              total_estimated_weeks: r.total_estimated_weeks,
              phase_count: r.phase_count,
              overall_progress_percentage: r.overall_progress_percentage,
              created_date: new Date(r.created_date),
              updated_date: new Date(r.updated_date),
              last_accessed_date: r.last_accessed_date ? new Date(r.last_accessed_date) : undefined
            }))
            .sort((a: RoadmapSummary, b: RoadmapSummary) => b.created_date.getTime() - a.created_date.getTime()) // Most recent first
          
          setRoadmapHistory(roadmaps)
          
          // Auto-select the most recent roadmap if available
          if (roadmaps.length > 0 && !selectedRoadmap) {
            await loadFullRoadmap(roadmaps[0].id)
          }
        }
      }
    } catch (error) {
      console.error('Error loading roadmap history:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadFullRoadmap = async (roadmapId: string) => {
    try {
      setLoadingRoadmap(true)
      const response = await fetch(`/api/roadmap/${roadmapId}`)
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          const fullRoadmap: Roadmap = {
            ...data.roadmap,
            created_date: new Date(data.roadmap.created_date),
            updated_date: new Date(data.roadmap.updated_date),
            last_accessed_date: data.roadmap.last_accessed_date ? new Date(data.roadmap.last_accessed_date) : undefined,
            status: data.roadmap.status as RoadmapStatus
          }
          setSelectedRoadmap(fullRoadmap)
          setStrengthsAnalysis(data.roadmap.strengths_analysis || null)
          setShowGenerator(false)
          
          // Store selected roadmap ID in localStorage for persistence
          localStorage.setItem('selectedRoadmapId', roadmapId)
        }
      } else {
        console.error('Failed to load roadmap details')
      }
    } catch (error) {
      console.error('Error loading roadmap details:', error)
    } finally {
      setLoadingRoadmap(false)
    }
  }

  const handleRoadmapGenerated = async (response: RoadmapGenerationResponse) => {
    console.log('Roadmap generation response:', response)
    
    if (!response || !response.roadmap) {
      console.error('Invalid roadmap response:', response)
      return
    }
    
    const roadmap = response.roadmap
    
    // Convert the API response to our Roadmap type
    const convertedRoadmap: Roadmap = {
      id: roadmap.id,
      user_id: roadmap.user_id || 'temp_user_123',
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
    setSelectedRoadmap(convertedRoadmap)
    setShowGenerator(false)
    
    // Refresh roadmap history to include the new roadmap
    await loadRoadmapHistory()
  }

  const handlePhaseUpdate = async (phaseNumber: number, updates: Record<string, unknown>) => {
    if (!selectedRoadmap) return

    // Update the roadmap locally
    const updatedRoadmap = { ...selectedRoadmap }
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

      setSelectedRoadmap(updatedRoadmap)

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
        } else {
          // Refresh roadmap history to update progress
          await loadRoadmapHistory()
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
    setSelectedRoadmap(null)
    setStrengthsAnalysis(null)
    setShowGenerator(true)
  }

  const handleSelectRoadmap = async (roadmapId: string) => {
    if (selectedRoadmap?.id === roadmapId) return // Already selected
    await loadFullRoadmap(roadmapId)
  }

  const handleRoadmapUpdate = async (roadmapId: string) => {
    // Reload the roadmap to get latest changes
    if (selectedRoadmap?.id === roadmapId) {
      await loadFullRoadmap(roadmapId)
    }
    // Also refresh the roadmap history to update progress
    await loadRoadmapHistory()
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusColor = (status: RoadmapStatus) => {
    switch (status) {
      case RoadmapStatus.ACTIVE:
        return 'bg-green-100 text-green-800'
      case RoadmapStatus.COMPLETED:
        return 'bg-blue-100 text-blue-800'
      case RoadmapStatus.ARCHIVED:
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading your roadmaps...</div>
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-[600px]">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Your Roadmaps</h2>
            <button
              onClick={handleNewRoadmap}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-md font-medium"
            >
              New
            </button>
          </div>
        </div>

        {/* Roadmap List */}
        <div className="flex-1 overflow-y-auto">
          {roadmapHistory.length === 0 ? (
            <div className="p-4 text-center">
              <div className="text-gray-400 mb-3">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">No roadmaps yet</h3>
              <p className="text-xs text-gray-500 mb-3">
                Create your first career roadmap to get started on your journey.
              </p>
              <button
                onClick={handleNewRoadmap}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-md font-medium"
              >
                Create Roadmap
              </button>
            </div>
          ) : (
            <div className="p-2">
              {roadmapHistory.map((roadmap) => (
                <button
                  key={roadmap.id}
                  onClick={() => handleSelectRoadmap(roadmap.id)}
                  className={`w-full p-3 mb-2 text-left rounded-lg border transition-colors ${
                    selectedRoadmap?.id === roadmap.id
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900 text-sm line-clamp-2">
                      {roadmap.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(roadmap.status)}`}>
                      {roadmap.status}
                    </span>
                  </div>
                  
                  <p className="text-xs text-gray-600 mb-2">
                    {roadmap.current_role} → {roadmap.target_role}
                  </p>
                  
                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>{roadmap.overall_progress_percentage}% complete</span>
                    <span>{formatDate(roadmap.created_date)}</span>
                  </div>
                  
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-1">
                      <div 
                        className="bg-indigo-600 h-1 rounded-full" 
                        style={{ width: `${roadmap.overall_progress_percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 bg-gray-50">
        {showGenerator ? (
          <div className="p-6">
            <div className="mb-4">
              <button
                onClick={() => setShowGenerator(false)}
                className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
              >
                ← Back to roadmaps
              </button>
            </div>
            <RoadmapGenerator
              onRoadmapGenerated={handleRoadmapGenerated}
              currentRole={profile?.current_role}
              targetRoles={profile?.target_roles}
            />
          </div>
        ) : selectedRoadmap ? (
          <div className="h-full">
            {loadingRoadmap ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-lg text-gray-600">Loading roadmap...</div>
              </div>
            ) : (
              <div className="p-6">
                {/* Roadmap Header */}
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">{selectedRoadmap.title}</h1>
                    <p className="text-gray-600 mt-1">
                      {selectedRoadmap.current_role} → {selectedRoadmap.target_role}
                    </p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <span>Created {formatDate(selectedRoadmap.created_date)}</span>
                      <span>•</span>
                      <span>{selectedRoadmap.total_estimated_weeks} weeks</span>
                      <span>•</span>
                      <span>{selectedRoadmap.overall_progress_percentage}% complete</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={handleEditRoadmap}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md font-medium"
                    >
                      Edit Parameters
                    </button>
                  </div>
                </div>

                {/* Show strengths analysis if available */}
                {strengthsAnalysis && (
                  <div className="mb-6">
                    <StrengthsAnalysis
                      analysis={strengthsAnalysis}
                      currentRole={selectedRoadmap.current_role}
                      targetRole={selectedRoadmap.target_role}
                    />
                  </div>
                )}
                
                {/* Main Content Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Roadmap Display - Takes up 2/3 of the space */}
                  <div className="lg:col-span-2">
                    <RoadmapDisplay
                      roadmap={selectedRoadmap}
                      userId={profile?.user_id}
                      onPhaseUpdate={handlePhaseUpdate}
                      onEdit={handleEditRoadmap}
                    />
                  </div>
                  
                  {/* Roadmap Chat - Takes up 1/3 of the space */}
                  <div className="lg:col-span-1">
                    <RoadmapChat
                      roadmap={selectedRoadmap}
                      onRoadmapUpdate={handleRoadmapUpdate}
                      className="sticky top-6"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">Select a roadmap to view</h3>
              <p className="text-gray-600 mb-4">
                Choose a roadmap from the sidebar to view its details and track your progress.
              </p>
              {roadmapHistory.length === 0 && (
                <button
                  onClick={handleNewRoadmap}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium"
                >
                  Create Your First Roadmap
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}