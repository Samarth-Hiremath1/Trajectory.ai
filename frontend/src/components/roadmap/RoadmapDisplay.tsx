'use client'

import { useState } from 'react'
import { Roadmap, RoadmapPhase, SkillLevel, ResourceType } from '@/types/roadmap'
import { RoadmapExport } from './RoadmapExport'

interface RoadmapDisplayProps {
  roadmap: Roadmap
  onPhaseUpdate?: (phaseNumber: number, updates: Record<string, unknown>) => void
  onEdit?: () => void
}

export function RoadmapDisplay({ roadmap, onPhaseUpdate, onEdit }: RoadmapDisplayProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set([1]))


  const togglePhaseExpansion = (phaseNumber: number) => {
    const newExpanded = new Set(expandedPhases)
    if (newExpanded.has(phaseNumber)) {
      newExpanded.delete(phaseNumber)
    } else {
      newExpanded.add(phaseNumber)
    }
    setExpandedPhases(newExpanded)
  }

  const getSkillLevelColor = (level: SkillLevel) => {
    switch (level) {
      case SkillLevel.BEGINNER:
        return 'bg-red-100 text-red-800'
      case SkillLevel.INTERMEDIATE:
        return 'bg-yellow-100 text-yellow-800'
      case SkillLevel.ADVANCED:
        return 'bg-blue-100 text-blue-800'
      case SkillLevel.EXPERT:
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getResourceTypeIcon = (type: ResourceType) => {
    switch (type) {
      case ResourceType.COURSE:
        return '📚'
      case ResourceType.CERTIFICATION:
        return '🏆'
      case ResourceType.PROJECT:
        return '🛠️'
      case ResourceType.BOOK:
        return '📖'
      case ResourceType.ARTICLE:
        return '📄'
      case ResourceType.VIDEO:
        return '🎥'
      case ResourceType.PRACTICE:
        return '💪'
      default:
        return '📋'
    }
  }

  const getPriorityColor = (priority: number) => {
    if (priority <= 2) return 'bg-red-100 text-red-800'
    if (priority <= 3) return 'bg-yellow-100 text-yellow-800'
    return 'bg-green-100 text-green-800'
  }

  const getPriorityLabel = (priority: number) => {
    if (priority === 1) return 'Critical'
    if (priority === 2) return 'High'
    if (priority === 3) return 'Medium'
    if (priority === 4) return 'Low'
    return 'Optional'
  }

  const calculatePhaseProgress = (phase: RoadmapPhase) => {
    if (phase.milestones.length === 0) return 0
    const completedMilestones = phase.milestones.filter(m => m.is_completed).length
    return Math.round((completedMilestones / phase.milestones.length) * 100)
  }

  const handleMilestoneToggle = (phaseNumber: number, milestoneIndex: number) => {
    if (onPhaseUpdate) {
      const phase = roadmap.phases.find(p => p.phase_number === phaseNumber)
      if (phase) {
        const updatedMilestones = [...phase.milestones]
        updatedMilestones[milestoneIndex] = {
          ...updatedMilestones[milestoneIndex],
          is_completed: !updatedMilestones[milestoneIndex].is_completed,
          completed_date: !updatedMilestones[milestoneIndex].is_completed ? new Date() : undefined
        }
        onPhaseUpdate(phaseNumber, { milestones: updatedMilestones })
      }
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{roadmap.title}</h2>
            <p className="text-gray-600 mb-4">{roadmap.description}</p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <span className="font-medium">From:</span>
                <span className="ml-1 px-2 py-1 bg-gray-100 rounded">{roadmap.current_role}</span>
              </span>
              <span>→</span>
              <span className="flex items-center">
                <span className="font-medium">To:</span>
                <span className="ml-1 px-2 py-1 bg-indigo-100 text-indigo-800 rounded">{roadmap.target_role}</span>
              </span>
              <span>•</span>
              <span>{roadmap.total_estimated_weeks} weeks</span>
              <span>•</span>
              <span>{roadmap.phases.length} phases</span>
            </div>
          </div>
          <div className="flex space-x-3">
            <RoadmapExport roadmap={roadmap} />
            {onEdit && (
              <button
                onClick={onEdit}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium"
              >
                Edit Roadmap
              </button>
            )}
          </div>
        </div>

        {/* Overall Progress */}
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Overall Progress</span>
            <span className="text-sm text-gray-500">{roadmap.overall_progress_percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${roadmap.overall_progress_percentage}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Phases */}
      <div className="divide-y divide-gray-200">
        {roadmap.phases.map((phase) => {
          const isExpanded = expandedPhases.has(phase.phase_number)
          const phaseProgress = calculatePhaseProgress(phase)
          
          return (
            <div key={phase.phase_number} className="p-6">
              {/* Phase Header */}
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => togglePhaseExpansion(phase.phase_number)}
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    phase.is_completed 
                      ? 'bg-green-500 text-white' 
                      : phaseProgress > 0 
                        ? 'bg-indigo-500 text-white' 
                        : 'bg-gray-200 text-gray-600'
                  }`}>
                    {phase.is_completed ? '✓' : phase.phase_number}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{phase.title}</h3>
                    <p className="text-sm text-gray-600">{phase.duration_weeks} weeks • {phaseProgress}% complete</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${phaseProgress}%` }}
                    ></div>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">
                    {isExpanded ? '▼' : '▶'}
                  </button>
                </div>
              </div>

              {/* Phase Content */}
              {isExpanded && (
                <div className="mt-6 space-y-6">
                  {/* Description */}
                  <div>
                    <p className="text-gray-700">{phase.description}</p>
                  </div>

                  {/* Prerequisites & Outcomes */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {phase.prerequisites.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Prerequisites</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {phase.prerequisites.map((prereq, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-gray-400 mr-2">•</span>
                              {prereq}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {phase.outcomes.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Expected Outcomes</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {phase.outcomes.map((outcome, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-green-500 mr-2">✓</span>
                              {outcome}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Skills to Develop */}
                  {phase.skills_to_develop.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Skills to Develop</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {phase.skills_to_develop.map((skill, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium text-gray-900">{skill.name}</h5>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(skill.priority)}`}>
                                {getPriorityLabel(skill.priority)}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm">
                              <span className={`px-2 py-1 rounded ${getSkillLevelColor(skill.current_level)}`}>
                                {skill.current_level}
                              </span>
                              <span className="text-gray-400">→</span>
                              <span className={`px-2 py-1 rounded ${getSkillLevelColor(skill.target_level)}`}>
                                {skill.target_level}
                              </span>
                            </div>
                            {skill.description && (
                              <p className="text-sm text-gray-600 mt-2">{skill.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Learning Resources */}
                  {phase.learning_resources.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Learning Resources</h4>
                      <div className="space-y-3">
                        {phase.learning_resources.map((resource, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex items-start space-x-3">
                                <span className="text-2xl">{getResourceTypeIcon(resource.resource_type)}</span>
                                <div>
                                  <h5 className="font-medium text-gray-900">
                                    {resource.url ? (
                                      <a 
                                        href={resource.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-indigo-600 hover:text-indigo-800"
                                      >
                                        {resource.title}
                                      </a>
                                    ) : (
                                      resource.title
                                    )}
                                  </h5>
                                  {resource.provider && (
                                    <p className="text-sm text-gray-500">by {resource.provider}</p>
                                  )}
                                  {resource.description && (
                                    <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                                  )}
                                  {resource.skills_covered.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-2">
                                      {resource.skills_covered.map((skill, skillIndex) => (
                                        <span 
                                          key={skillIndex}
                                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                                        >
                                          {skill}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="text-right text-sm text-gray-500">
                                {resource.duration && <div>{resource.duration}</div>}
                                {resource.cost && <div>{resource.cost}</div>}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Milestones */}
                  {phase.milestones.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Milestones</h4>
                      <div className="space-y-3">
                        {phase.milestones.map((milestone, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-start space-x-3">
                              <button
                                onClick={() => handleMilestoneToggle(phase.phase_number, index)}
                                className={`mt-1 w-5 h-5 rounded border-2 flex items-center justify-center ${
                                  milestone.is_completed
                                    ? 'bg-green-500 border-green-500 text-white'
                                    : 'border-gray-300 hover:border-gray-400'
                                }`}
                              >
                                {milestone.is_completed && '✓'}
                              </button>
                              <div className="flex-1">
                                <h5 className={`font-medium ${milestone.is_completed ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                                  {milestone.title}
                                </h5>
                                {milestone.description && (
                                  <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                                )}
                                <div className="text-sm text-gray-500 mt-2">
                                  Week {milestone.estimated_completion_weeks}
                                  {milestone.completed_date && (
                                    <span className="ml-2 text-green-600">
                                      • Completed {new Date(milestone.completed_date).toLocaleDateString()}
                                    </span>
                                  )}
                                </div>
                                {milestone.success_criteria.length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-xs font-medium text-gray-700">Success Criteria:</p>
                                    <ul className="text-xs text-gray-600 mt-1 space-y-1">
                                      {milestone.success_criteria.map((criteria, criteriaIndex) => (
                                        <li key={criteriaIndex} className="flex items-start">
                                          <span className="text-gray-400 mr-1">•</span>
                                          {criteria}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}