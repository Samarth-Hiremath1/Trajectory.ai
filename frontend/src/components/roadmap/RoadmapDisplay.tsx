'use client'

import { useState, useEffect } from 'react'
import { Roadmap, RoadmapPhase, SkillLevel, ResourceType } from '@/types/roadmap'
import { RoadmapExport } from './RoadmapExport'
import { StatusDropdown } from '@/components/ui/StatusDropdown'
import { taskSyncManager, TaskSyncData } from '@/lib/taskSync'
import { 
  XMarkIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  ClockIcon,
  BookOpenIcon,
  AcademicCapIcon,
  WrenchScrewdriverIcon,
  VideoCameraIcon,
  DocumentTextIcon,
  TrophyIcon,
  FireIcon,
  ArrowRightIcon,
  CalendarIcon,
  LinkIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline'

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'skipped'

interface RoadmapDisplayProps {
  roadmap: Roadmap
  userId?: string
  onPhaseUpdate?: (phaseNumber: number, updates: Record<string, unknown>) => void
  onEdit?: () => void
}

interface SlideOutPanel {
  type: 'phase' | 'milestone'
  phaseNumber?: number
  milestoneIndex?: number
}

export function RoadmapDisplay({ roadmap, userId, onPhaseUpdate, onEdit }: RoadmapDisplayProps) {
  const [activePanel, setActivePanel] = useState<SlideOutPanel | null>(null)
  const [milestoneStatuses, setMilestoneStatuses] = useState<Record<string, TaskStatus>>({})

  // Initialize milestone statuses from existing tasks
  useEffect(() => {
    if (!userId) return
    
    const tasks = taskSyncManager.getLocalTasks(userId)
    const roadmapTasks = tasks.filter(t => t.roadmapId === roadmap.id)
    
    const initialStatuses: Record<string, TaskStatus> = {}
    roadmapTasks.forEach(task => {
      if (task.phaseNumber !== undefined && task.milestoneIndex !== undefined) {
        const key = `${task.phaseNumber}-${task.milestoneIndex}`
        // Map task status to milestone status
        const milestoneStatus = task.status === 'cancelled' ? 'skipped' : task.status
        initialStatuses[key] = milestoneStatus as TaskStatus
      }
    })
    
    setMilestoneStatuses(initialStatuses)
  }, [roadmap.id, userId])



  const getMilestoneStatus = (phaseNumber: number, milestoneIndex: number): TaskStatus => {
    const key = `${phaseNumber}-${milestoneIndex}`
    if (milestoneStatuses[key]) {
      return milestoneStatuses[key]
    }
    const phase = roadmap.phases.find(p => p.phase_number === phaseNumber)
    const milestone = phase?.milestones[milestoneIndex]
    if (milestone?.is_completed) {
      return 'completed'
    }
    return 'pending'
  }

  const updateMilestoneStatus = (phaseNumber: number, milestoneIndex: number, status: TaskStatus) => {
    console.log('RoadmapDisplay: updateMilestoneStatus called', { phaseNumber, milestoneIndex, status })
    
    const key = `${phaseNumber}-${milestoneIndex}`
    setMilestoneStatuses(prev => ({ ...prev, [key]: status }))
    
    // Update the roadmap data
    if (onPhaseUpdate) {
      const phase = roadmap.phases.find(p => p.phase_number === phaseNumber)
      if (phase) {
        const updatedMilestones = [...phase.milestones]
        updatedMilestones[milestoneIndex] = {
          ...updatedMilestones[milestoneIndex],
          is_completed: status === 'completed',
          completed_date: status === 'completed' ? new Date() : undefined
        }
        onPhaseUpdate(phaseNumber, { milestones: updatedMilestones })
      }
    }

    // Sync with other components
    const milestone = roadmap.phases.find(p => p.phase_number === phaseNumber)?.milestones[milestoneIndex]
    if (milestone && userId) {
      console.log('RoadmapDisplay: Syncing milestone status to task system')
      taskSyncManager.updateTaskStatus(userId, {
        id: `milestone-${roadmap.id}-${phaseNumber}-${milestoneIndex}`,
        roadmapId: roadmap.id,
        phaseNumber,
        milestoneIndex,
        status,
        title: milestone.title
      })
    }
  }

  // Listen for task status changes from other components
  useEffect(() => {
    const unsubscribe = taskSyncManager.subscribe((data: TaskSyncData) => {
      if (data.roadmapId === roadmap.id && data.phaseNumber !== undefined && data.milestoneIndex !== undefined) {
        const key = `${data.phaseNumber}-${data.milestoneIndex}`
        setMilestoneStatuses(prev => ({ ...prev, [key]: data.status }))
        
        // Also update the roadmap data to keep it in sync
        if (onPhaseUpdate) {
          const phase = roadmap.phases.find(p => p.phase_number === data.phaseNumber)
          if (phase && data.milestoneIndex < phase.milestones.length) {
            const updatedMilestones = [...phase.milestones]
            updatedMilestones[data.milestoneIndex] = {
              ...updatedMilestones[data.milestoneIndex],
              is_completed: data.status === 'completed',
              completed_date: data.status === 'completed' ? new Date() : undefined
            }
            onPhaseUpdate(data.phaseNumber, { milestones: updatedMilestones })
          }
        }
      }
    })

    return () => {
      unsubscribe()
    }
  }, [roadmap.id, onPhaseUpdate])

  const getResourceTypeIcon = (type: ResourceType) => {
    switch (type) {
      case ResourceType.COURSE:
        return <BookOpenIcon className="w-4 h-4" />
      case ResourceType.CERTIFICATION:
        return <TrophyIcon className="w-4 h-4" />
      case ResourceType.PROJECT:
        return <WrenchScrewdriverIcon className="w-4 h-4" />
      case ResourceType.BOOK:
        return <BookOpenIcon className="w-4 h-4" />
      case ResourceType.ARTICLE:
        return <DocumentTextIcon className="w-4 h-4" />
      case ResourceType.VIDEO:
        return <VideoCameraIcon className="w-4 h-4" />
      case ResourceType.PRACTICE:
        return <FireIcon className="w-4 h-4" />
      default:
        return <DocumentTextIcon className="w-4 h-4" />
    }
  }

  const generateResourceUrl = (resource: any) => {
    // If resource already has a URL, use it
    if (resource.url && resource.url.startsWith('http')) {
      return resource.url
    }

    // Generate search URLs based on resource type, provider, and title
    const searchQuery = encodeURIComponent(resource.title)
    const provider = resource.provider?.toLowerCase() || ''
    
    switch (resource.resource_type) {
      case ResourceType.COURSE:
        // Check for specific providers first
        if (provider.includes('wall street prep')) {
          return `https://www.wallstreetprep.com/search/?q=${searchQuery}`
        } else if (provider.includes('coursera')) {
          return `https://www.coursera.org/search?query=${searchQuery}`
        } else if (provider.includes('udemy')) {
          return `https://www.udemy.com/courses/search/?q=${searchQuery}`
        } else if (provider.includes('edx')) {
          return `https://www.edx.org/search?q=${searchQuery}`
        } else if (provider.includes('linkedin learning')) {
          return `https://www.linkedin.com/learning/search?keywords=${searchQuery}`
        } else if (provider.includes('pluralsight')) {
          return `https://www.pluralsight.com/search?q=${searchQuery}`
        } else if (provider.includes('udacity')) {
          return `https://www.udacity.com/courses/all?search=${searchQuery}`
        } else if (provider.includes('khan academy')) {
          return `https://www.khanacademy.org/search?page_search_query=${searchQuery}`
        } else if (provider.includes('skillshare')) {
          return `https://www.skillshare.com/search?query=${searchQuery}`
        } else if (provider.includes('masterclass')) {
          return `https://www.masterclass.com/search?query=${searchQuery}`
        } else {
          // Default to Google search for unknown providers
          return `https://www.google.com/search?q=${searchQuery}+course+${provider}`
        }
      
      case ResourceType.CERTIFICATION:
        if (provider.includes('aws')) {
          return `https://aws.amazon.com/certification/`
        } else if (provider.includes('google')) {
          return `https://cloud.google.com/certification`
        } else if (provider.includes('microsoft')) {
          return `https://docs.microsoft.com/en-us/learn/certifications/`
        } else if (provider.includes('cisco')) {
          return `https://www.cisco.com/c/en/us/training-events/training-certifications/certifications.html`
        } else {
          return `https://www.google.com/search?q=${searchQuery}+certification`
        }
      
      case ResourceType.BOOK:
        return `https://www.amazon.com/s?k=${searchQuery}`
      
      case ResourceType.ARTICLE:
        if (provider.includes('medium')) {
          return `https://medium.com/search?q=${searchQuery}`
        } else if (provider.includes('dev.to')) {
          return `https://dev.to/search?q=${searchQuery}`
        } else if (provider.includes('hackernoon')) {
          return `https://hackernoon.com/search?query=${searchQuery}`
        } else {
          return `https://www.google.com/search?q=${searchQuery}`
        }
      
      case ResourceType.VIDEO:
        if (provider.includes('youtube')) {
          return `https://www.youtube.com/results?search_query=${searchQuery}`
        } else if (provider.includes('vimeo')) {
          return `https://vimeo.com/search?q=${searchQuery}`
        } else {
          return `https://www.youtube.com/results?search_query=${searchQuery}`
        }
      
      case ResourceType.PROJECT:
        if (provider.includes('github')) {
          return `https://github.com/search?q=${searchQuery}`
        } else if (provider.includes('gitlab')) {
          return `https://gitlab.com/search?search=${searchQuery}`
        } else {
          return `https://github.com/search?q=${searchQuery}`
        }
      
      default:
        return `https://www.google.com/search?q=${searchQuery}`
    }
  }

  const getResourceInstructions = (resource: any) => {
    const url = generateResourceUrl(resource)
    
    switch (resource.resource_type) {
      case ResourceType.COURSE:
        if (resource.provider?.toLowerCase().includes('coursera')) {
          return `Go to Coursera and search for "${resource.title}"`
        } else if (resource.provider?.toLowerCase().includes('udemy')) {
          return `Go to Udemy and search for "${resource.title}"`
        } else {
          return `Search for "${resource.title}" on online learning platforms`
        }
      
      case ResourceType.BOOK:
        return `Search for "${resource.title}" on Amazon or your preferred bookstore`
      
      case ResourceType.VIDEO:
        return `Search for "${resource.title}" on YouTube`
      
      case ResourceType.PROJECT:
        return `Search for "${resource.title}" on GitHub or coding platforms`
      
      default:
        return `Search for "${resource.title}" online`
    }
  }

  const getSkillLevelColor = (level: SkillLevel) => {
    switch (level) {
      case SkillLevel.BEGINNER:
        return 'bg-rose-100 text-rose-700 border-rose-200'
      case SkillLevel.INTERMEDIATE:
        return 'bg-amber-100 text-amber-700 border-amber-200'
      case SkillLevel.ADVANCED:
        return 'bg-sky-100 text-sky-700 border-sky-200'
      case SkillLevel.EXPERT:
        return 'bg-emerald-100 text-emerald-700 border-emerald-200'
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200'
    }
  }

  const calculatePhaseProgress = (phase: RoadmapPhase) => {
    if (phase.milestones.length === 0) return 0
    
    // Get current status for each milestone, prioritizing milestoneStatuses over roadmap data
    const milestoneCurrentStatuses = phase.milestones.map((milestone, index) => {
      const key = `${phase.phase_number}-${index}`
      if (milestoneStatuses[key]) {
        return milestoneStatuses[key]
      }
      // Fallback to roadmap data
      return milestone.is_completed ? 'completed' : 'pending'
    })
    
    const completedCount = milestoneCurrentStatuses.filter(status => status === 'completed').length
    const skippedCount = milestoneCurrentStatuses.filter(status => status === 'skipped').length
    
    // Count both completed and skipped as "done" for progress calculation
    const doneCount = completedCount + skippedCount
    return Math.round((doneCount / phase.milestones.length) * 100)
  }

  const getPhaseStatus = (phase: RoadmapPhase) => {
    if (phase.milestones.length === 0) return 'pending'
    
    // Get current status for each milestone, prioritizing milestoneStatuses over roadmap data
    const milestoneCurrentStatuses = phase.milestones.map((milestone, index) => {
      const key = `${phase.phase_number}-${index}`
      if (milestoneStatuses[key]) {
        return milestoneStatuses[key]
      }
      // Fallback to roadmap data
      return milestone.is_completed ? 'completed' : 'pending'
    })
    
    const completedCount = milestoneCurrentStatuses.filter(status => status === 'completed').length
    const skippedCount = milestoneCurrentStatuses.filter(status => status === 'skipped').length
    const inProgressCount = milestoneCurrentStatuses.filter(status => status === 'in_progress').length
    const totalMilestones = phase.milestones.length
    
    // If all milestones are either completed or skipped, phase is completed (green)
    if (completedCount + skippedCount === totalMilestones) return 'completed'
    
    // If at least one milestone is completed or in progress, phase is in progress (yellow)
    if (completedCount > 0 || inProgressCount > 0) return 'in_progress'
    
    // Otherwise, phase is pending (gray)
    return 'pending'
  }

  const getPhaseStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'border-emerald-200 bg-emerald-50'
      case 'in_progress':
        return 'border-yellow-200 bg-yellow-50'
      default:
        return 'border-gray-200 hover:border-gray-300'
    }
  }

  const getPhaseProgressColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500'
      case 'in_progress':
        return 'bg-yellow-500'
      default:
        return 'bg-blue-500'
    }
  }

  const getMilestoneStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'completed':
        return 'border-emerald-200 bg-emerald-50'
      case 'in_progress':
        return 'border-yellow-200 bg-yellow-50'
      case 'skipped':
        return 'border-gray-400 bg-gray-100'
      default:
        return 'border-gray-200 hover:border-gray-300'
    }
  }

  const getMilestoneCircleColor = (status: TaskStatus) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500 border-emerald-500'
      case 'in_progress':
        return 'bg-yellow-500 border-yellow-500'
      case 'skipped':
        return 'bg-gray-800 border-gray-800'
      default:
        return 'border-gray-300'
    }
  }

  const handleMilestoneToggle = (phaseNumber: number, milestoneIndex: number) => {
    if (onPhaseUpdate) {
      const phase = roadmap.phases.find(p => p.phase_number === phaseNumber)
      if (phase) {
        const milestone = phase.milestones[milestoneIndex]
        const newCompletionStatus = !milestone.is_completed
        
        const updatedMilestones = [...phase.milestones]
        updatedMilestones[milestoneIndex] = {
          ...updatedMilestones[milestoneIndex],
          is_completed: newCompletionStatus,
          completed_date: newCompletionStatus ? new Date() : undefined
        }
        
        // Update local milestone status
        const key = `${phaseNumber}-${milestoneIndex}`
        setMilestoneStatuses(prev => ({ 
          ...prev, 
          [key]: newCompletionStatus ? 'completed' : 'pending' 
        }))
        
        // Update the roadmap
        onPhaseUpdate(phaseNumber, { milestones: updatedMilestones })
        
        // Sync with task system
        if (userId) {
          taskSyncManager.updateTaskStatus(userId, {
            id: `milestone-${roadmap.id}-${phaseNumber}-${milestoneIndex}`,
            roadmapId: roadmap.id,
            phaseNumber: phaseNumber,
            milestoneIndex: milestoneIndex,
            status: newCompletionStatus ? 'completed' : 'pending',
            title: milestone.title
          })
        }
      }
    }
  }

  const openPhasePanel = (phaseNumber: number) => {
    setActivePanel({ type: 'phase', phaseNumber })
    document.body.style.overflow = 'hidden'
  }

  const openMilestonePanel = (phaseNumber: number, milestoneIndex: number) => {
    setActivePanel({ type: 'milestone', phaseNumber, milestoneIndex })
    document.body.style.overflow = 'hidden'
  }

  const closePanel = () => {
    setActivePanel(null)
    document.body.style.overflow = 'unset'
  }

  const renderPhasePanel = () => {
    if (!activePanel || activePanel.type !== 'phase' || !activePanel.phaseNumber) return null
    
    const phase = roadmap.phases.find(p => p.phase_number === activePanel.phaseNumber)
    if (!phase) return null

    return (
      <div className="fixed inset-y-0 right-0 w-full sm:w-3/5 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out">
        <div className="h-full flex flex-col">
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{phase.title.replace(/\*\*/g, '')}</h3>
                <p className="text-base text-gray-600">{phase.duration_weeks} weeks</p>
              </div>
              <button
                onClick={closePanel}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Description</h4>
              <p className="text-base text-gray-700 leading-relaxed">{phase.description}</p>
            </div>

            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Why This Phase</h4>
              <p className="text-base text-gray-700 leading-relaxed">
                This phase is designed to build foundational skills and knowledge required for your transition. 
                It focuses on {phase.skills_to_develop.slice(0, 3).map(s => s.name).join(', ')} 
                {phase.skills_to_develop.length > 3 && ` and ${phase.skills_to_develop.length - 3} more skills`}.
              </p>
            </div>

            {phase.prerequisites.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Prerequisites</h4>
                <ul className="space-y-2">
                  {phase.prerequisites.map((prereq, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-base text-gray-700">{prereq}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {phase.outcomes.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Expected Outcomes</h4>
                <ul className="space-y-2">
                  {phase.outcomes.map((outcome, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <CheckCircleIcon className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span className="text-base text-gray-700">{outcome}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {phase.skills_to_develop.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Skills to Develop</h4>
                <div className="space-y-3">
                  {phase.skills_to_develop.map((skill, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900 text-base">{skill.name}</h5>
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                          skill.priority <= 2 ? 'bg-rose-100 text-rose-700' :
                          skill.priority <= 3 ? 'bg-amber-100 text-amber-700' :
                          'bg-emerald-100 text-emerald-700'
                        }`}>
                          {skill.priority <= 2 ? 'High' : skill.priority <= 3 ? 'Medium' : 'Low'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm">
                        <span className={`px-2 py-1 rounded border ${getSkillLevelColor(skill.current_level)}`}>
                          {skill.current_level}
                        </span>
                        <ArrowRightIcon className="w-3 h-3 text-gray-400" />
                        <span className={`px-2 py-1 rounded border ${getSkillLevelColor(skill.target_level)}`}>
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

            {phase.learning_resources.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Learning Resources</h4>
                <p className="text-base text-gray-600 mb-3">Learn more from the following resources:</p>
                <div className="space-y-3">
                  {phase.learning_resources.map((resource, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-start space-x-3">
                        <div className="p-1.5 bg-white rounded border border-gray-200">
                          {getResourceTypeIcon(resource.resource_type)}
                        </div>
                        <div className="flex-1">
                          <h5 className="font-medium text-gray-900 text-lg mb-1">
                            {resource.url ? (
                              <a 
                                href={resource.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800 flex items-center space-x-1 hover:underline"
                              >
                                <span>{resource.title}</span>
                                <LinkIcon className="w-3 h-3" />
                              </a>
                            ) : (
                              resource.title
                            )}
                          </h5>
                          {resource.provider && (
                            <p className="text-base text-gray-500 mb-1">by {resource.provider}</p>
                          )}
                          {resource.description && (
                            <p className="text-base text-gray-600 mb-2">{resource.description}</p>
                          )}
                          <div className="flex items-center space-x-3 text-base text-gray-600">
                            {resource.duration && (
                              <span className="flex items-center space-x-1">
                                <ClockIcon className="w-3 h-3" />
                                <span>{resource.duration}</span>
                              </span>
                            )}
                            {resource.cost && <span>{resource.cost}</span>}
                            {resource.difficulty && (
                              <span className={`px-2 py-1 rounded text-sm ${getSkillLevelColor(resource.difficulty)}`}>
                                {resource.difficulty}
                              </span>
                            )}
                          </div>
                          {resource.skills_covered && resource.skills_covered.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {resource.skills_covered.map(skill => (
                                <span
                                  key={skill}
                                  className="px-2 py-1 text-sm bg-blue-100 text-blue-700 rounded"
                                >
                                  {skill}
                                </span>
                              ))}
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
        </div>
      </div>
    )
  }

  const renderMilestonePanel = () => {
    if (!activePanel || activePanel.type !== 'milestone' || !activePanel.phaseNumber || activePanel.milestoneIndex === undefined) return null
    
    const phase = roadmap.phases.find(p => p.phase_number === activePanel.phaseNumber)
    const milestone = phase?.milestones[activePanel.milestoneIndex]
    if (!phase || !milestone) return null

    const relevantResources = phase.learning_resources.filter(resource => 
      milestone.title.toLowerCase().includes(resource.title.toLowerCase().split(' ')[0]) ||
      resource.skills_covered.some(skill => 
        milestone.title.toLowerCase().includes(skill.toLowerCase())
      )
    ).slice(0, 3)

    return (
      <div className="fixed inset-y-0 right-0 w-full sm:w-3/5 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out">
        <div className="h-full flex flex-col">
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{milestone.title}</h3>
                <p className="text-base text-gray-600">Week {milestone.estimated_completion_weeks}</p>
              </div>
              <button
                onClick={closePanel}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <div className="flex items-center space-x-3">
              <StatusDropdown
                value={getMilestoneStatus(phase.phase_number, activePanel.milestoneIndex!)}
                onChange={(status) => updateMilestoneStatus(phase.phase_number, activePanel.milestoneIndex!, status)}
              />
            </div>

            {milestone.description && (
              <div>
                <p className="text-base text-gray-700 leading-relaxed">{milestone.description}</p>
              </div>
            )}

            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Timeline</h4>
              <div className="flex items-center space-x-2 text-base text-gray-700">
                <CalendarIcon className="w-4 h-4 text-gray-500" />
                <span>Week {milestone.estimated_completion_weeks}</span>
                {milestone.completed_date && (
                  <span className="text-emerald-600 font-medium">
                    • Completed {new Date(milestone.completed_date).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>

            {milestone.success_criteria.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Success Criteria</h4>
                <ul className="space-y-2">
                  {milestone.success_criteria.map((criteria, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-base text-gray-700">{criteria}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {relevantResources.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Resources</h4>
                <p className="text-base text-gray-600 mb-3">Learn more from the following resources:</p>
                <div className="space-y-3">
                  {relevantResources.map((resource, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-start space-x-3">
                        <div className="p-1.5 bg-white rounded border border-gray-200">
                          {getResourceTypeIcon(resource.resource_type)}
                        </div>
                        <div className="flex-1">
                          <h5 className="font-medium text-gray-900 text-lg mb-1">
                            <a 
                              href={generateResourceUrl(resource)} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 flex items-center space-x-1 hover:underline"
                              title={getResourceInstructions(resource)}
                            >
                              <span>{resource.title}</span>
                              <LinkIcon className="w-3 h-3" />
                            </a>
                          </h5>
                          <p className="text-base text-gray-500 mb-1">{getResourceInstructions(resource)}</p>
                          {resource.provider && (
                            <p className="text-base text-gray-500 mb-1">by {resource.provider}</p>
                          )}
                          {resource.description && (
                            <p className="text-base text-gray-600 mb-2">{resource.description}</p>
                          )}
                          <div className="flex items-center space-x-3 text-base text-gray-600">
                            {resource.duration && (
                              <span className="flex items-center space-x-1">
                                <ClockIcon className="w-3 h-3" />
                                <span>{resource.duration}</span>
                              </span>
                            )}
                            {resource.cost && <span>{resource.cost}</span>}
                            {resource.difficulty && (
                              <span className={`px-2 py-1 rounded text-sm ${getSkillLevelColor(resource.difficulty)}`}>
                                {resource.difficulty}
                              </span>
                            )}
                          </div>
                          {resource.skills_covered && resource.skills_covered.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {resource.skills_covered.map(skill => (
                                <span
                                  key={skill}
                                  className="px-2 py-1 text-sm bg-blue-100 text-blue-700 rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional relevant resources from the phase */}
            {phase.learning_resources.length > relevantResources.length && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Additional Phase Resources</h4>
                <p className="text-sm text-gray-600 mb-3">More resources available for this phase:</p>
                <div className="space-y-2">
                  {phase.learning_resources.slice(relevantResources.length, relevantResources.length + 3).map((resource, index) => (
                    <div key={index} className="flex items-center space-x-2 text-sm">
                      <div className="p-1 bg-gray-100 rounded">
                        {getResourceTypeIcon(resource.resource_type)}
                      </div>
                      <a 
                        href={generateResourceUrl(resource)} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline flex items-center space-x-1"
                        title={getResourceInstructions(resource)}
                      >
                        <span>{resource.title}</span>
                        <LinkIcon className="w-3 h-3" />
                      </a>
                    </div>
                  ))}
                  {phase.learning_resources.length > relevantResources.length + 3 && (
                    <p className="text-xs text-gray-500 ml-6">
                      +{phase.learning_resources.length - relevantResources.length - 3} more resources in phase details
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Clean the title by removing markdown formatting
  const cleanTitle = (title: string) => {
    return title.replace(/\*\*/g, '').trim()
  }

  return (
    <div className="max-w-6xl mx-auto relative bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white p-8 mb-8">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-3">{cleanTitle(roadmap.title)}</h1>
            <p className="text-gray-600 mb-6 text-base leading-relaxed max-w-4xl">{roadmap.description}</p>
            
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <div className="flex items-center space-x-3">
                <div className="px-4 py-2 bg-gray-100 text-gray-700 rounded-full font-medium">
                  {roadmap.current_role}
                </div>
                <ArrowRightIcon className="w-4 h-4 text-gray-400" />
                <div className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full font-medium">
                  {roadmap.target_role}
                </div>
              </div>
              <div className="flex items-center space-x-4 text-gray-600">
                <span className="flex items-center space-x-1">
                  <ClockIcon className="w-4 h-4" />
                  <span>{roadmap.total_estimated_weeks} weeks</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span>{roadmap.phases.length} phases</span>
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-3 ml-6">
            <RoadmapExport roadmap={roadmap} />
            {onEdit && (
              <button
                onClick={onEdit}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
              >
                Edit Roadmap
              </button>
            )}
          </div>
        </div>

        <div className="mt-6">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-medium text-gray-700">Overall Progress</span>
            <span className="text-sm text-gray-600 font-semibold">{roadmap.overall_progress_percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${roadmap.overall_progress_percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="px-8 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="relative">
            {/* Main vertical timeline line */}
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-300 transform -translate-x-1/2" />
            
            <div className="space-y-16">
              {roadmap.phases.map((phase, phaseIndex) => {
                const phaseProgress = calculatePhaseProgress(phase)
                const isLastPhase = phaseIndex === roadmap.phases.length - 1
                // Use phase number instead of index for alternating - odd phases go left, even phases go right
                const isOddPhase = phase.phase_number % 2 === 1
                
                return (
                  <div key={phase.phase_number} className="relative">
                    {/* Phase connector dot on main timeline */}
                    <div className="absolute left-1/2 top-8 w-4 h-4 bg-white border-4 border-blue-500 rounded-full transform -translate-x-1/2 z-10" />
                    
                    {/* Phase Box - Centered on timeline */}
                    <div className="flex justify-center mb-8">
                      <button
                        onClick={() => openPhasePanel(phase.phase_number)}
                        className={`relative bg-white border-2 rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 w-96 z-10 ${
                          getPhaseStatusColor(getPhaseStatus(phase))
                        }`}
                      >
                        <div className="flex items-center space-x-3 mb-3">
                          <div className="text-left flex-1">
                            <h3 className="font-semibold text-gray-900 text-base">{cleanTitle(phase.title)}</h3>
                            <p className="text-sm text-gray-600">{phase.duration_weeks} weeks</p>
                          </div>
                          <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                        </div>
                        
                        <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
                          <span>
                            {phaseProgress > 0 ? `${phaseProgress}% complete` : 'Ready to start'}
                          </span>
                          <span>{phase.milestones.length} milestones</span>
                        </div>
                        
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-300 ${
                              getPhaseProgressColor(getPhaseStatus(phase))
                            }`}
                            style={{ width: `${phaseProgress}%` }}
                          />
                        </div>
                      </button>
                    </div>

                    {/* Milestones - Connected to main timeline */}
                    <div className="relative">
                      <div className="flex items-start justify-center">
                        {/* Left side container */}
                        <div className="flex flex-col space-y-6 w-80 mr-4">
                          {!isOddPhase ? (
                            // Show milestones on left for even phases
                            phase.milestones.map((milestone, milestoneIndex) => (
                              <div key={milestoneIndex} className="relative">
                                {/* Connection line from milestone to main timeline */}
                                <div className="absolute top-1/2 right-0 w-8 h-0.5 bg-gray-300 transform translate-x-full -translate-y-1/2" />
                                {/* Milestone connector dot */}
                                <div className="absolute top-1/2 right-0 w-2 h-2 bg-gray-400 rounded-full transform translate-x-full -translate-y-1/2 translate-x-8" />
                                
                                <button
                                  onClick={() => openMilestonePanel(phase.phase_number, milestoneIndex)}
                                  className={`w-full text-left bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-all duration-200 ${
                                    getMilestoneStatusColor(getMilestoneStatus(phase.phase_number, milestoneIndex))
                                  }`}
                                >
                                  <div className="flex items-center space-x-3">
                                    <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                                      getMilestoneCircleColor(getMilestoneStatus(phase.phase_number, milestoneIndex))
                                    }`}>
                                      {getMilestoneStatus(phase.phase_number, milestoneIndex) === 'completed' && (
                                        <CheckCircleIcon className="w-3 h-3 text-white" />
                                      )}
                                    </div>
                                    <div className="flex-1">
                                      <h4 className="font-medium text-gray-900 text-sm">{milestone.title}</h4>
                                      <p className="text-xs text-gray-500">Week {milestone.estimated_completion_weeks}</p>
                                    </div>
                                  </div>
                                </button>
                              </div>
                            ))
                          ) : (
                            // Empty space for odd phases
                            <div></div>
                          )}
                        </div>

                        {/* Center spacer for main timeline */}
                        <div className="w-8 flex justify-center">
                          {/* This space is for the main timeline */}
                        </div>

                        {/* Right side container */}
                        <div className="flex flex-col space-y-6 w-80 ml-4">
                          {isOddPhase ? (
                            // Show milestones on right for odd phases
                            phase.milestones.map((milestone, milestoneIndex) => (
                              <div key={milestoneIndex} className="relative">
                                {/* Connection line from main timeline to milestone */}
                                <div className="absolute top-1/2 left-0 w-8 h-0.5 bg-gray-300 transform -translate-x-full -translate-y-1/2" />
                                {/* Milestone connector dot */}
                                <div className="absolute top-1/2 left-0 w-2 h-2 bg-gray-400 rounded-full transform -translate-x-full -translate-y-1/2 -translate-x-8" />
                                
                                <button
                                  onClick={() => openMilestonePanel(phase.phase_number, milestoneIndex)}
                                  className={`w-full text-left bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-all duration-200 ${
                                    getMilestoneStatusColor(getMilestoneStatus(phase.phase_number, milestoneIndex))
                                  }`}
                                >
                                  <div className="flex items-center space-x-3">
                                    <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                                      getMilestoneCircleColor(getMilestoneStatus(phase.phase_number, milestoneIndex))
                                    }`}>
                                      {getMilestoneStatus(phase.phase_number, milestoneIndex) === 'completed' && (
                                        <CheckCircleIcon className="w-3 h-3 text-white" />
                                      )}
                                    </div>
                                    <div className="flex-1">
                                      <h4 className="font-medium text-gray-900 text-sm">{milestone.title}</h4>
                                      <p className="text-xs text-gray-500">Week {milestone.estimated_completion_weeks}</p>
                                    </div>
                                  </div>
                                </button>
                              </div>
                            ))
                          ) : (
                            // Empty space for even phases
                            <div></div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Phase completion indicator on main timeline */}
                    {!isLastPhase && (
                      <div className="flex justify-center mt-8">
                        <div className="absolute left-1/2 w-10 h-10 bg-white border-2 border-gray-300 rounded-full transform -translate-x-1/2 flex items-center justify-center z-10">
                          <ArrowDownIcon className="w-5 h-5 text-gray-500" />
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Slide-out Panels */}
      {activePanel && (
        <>
          <div 
            className="fixed inset-0 z-40 transition-opacity duration-300"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              backdropFilter: 'blur(4px)',
              WebkitBackdropFilter: 'blur(4px)'
            }}
            onClick={closePanel}
          />
          
          {activePanel.type === 'phase' && renderPhasePanel()}
          {activePanel.type === 'milestone' && renderMilestonePanel()}
        </>
      )}
    </div>
  )
}