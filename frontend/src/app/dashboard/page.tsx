'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState, useCallback } from 'react'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { RoadmapInterface } from '@/components/roadmap/RoadmapInterface'
import { DashboardStats } from '@/components/dashboard/DashboardStats'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { CalendarComponent } from '@/components/dashboard/CalendarComponent'
import { TodoList } from '@/components/dashboard/TodoList'
import { NotesComponent } from '@/components/dashboard/NotesComponent'
import { ProgressTracker } from '@/components/dashboard/ProgressTracker'
import { Roadmap } from '@/types/roadmap'

interface CalendarEvent {
  id: string
  title: string
  date: Date
  type: 'milestone' | 'learning' | 'practice' | 'review'
  description?: string
  completed?: boolean
  roadmapId?: string
  phaseNumber?: number
}

export default function DashboardPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'chat' | 'roadmap' | 'daily'>('daily')
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([])
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([])

  const loadRoadmaps = useCallback(async () => {
    try {
      const userId = 'temp_user_123' // TODO: Get from auth context
      const response = await fetch(`/api/roadmap/user/${userId}`)
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setRoadmaps(data.roadmaps)
          generateCalendarEvents(data.roadmaps)
        }
      }
    } catch (error) {
      console.error('Error loading roadmaps:', error)
    }
  }, [])

  // Load roadmaps for dashboard components
  useEffect(() => {
    if (user) {
      loadRoadmaps()
    }
  }, [user, loadRoadmaps])

  const generateCalendarEvents = (roadmaps: Roadmap[]) => {
    const events: CalendarEvent[] = []
    const today = new Date()

    roadmaps.forEach(roadmap => {
      if (roadmap.status === 'active') {
        roadmap.phases.forEach((phase, phaseIndex: number) => {
          phase.milestones.forEach((milestone, milestoneIndex: number) => {
            if (!milestone.is_completed) {
              // Generate due dates based on phase timeline
              const dueDate = new Date(today)
              dueDate.setDate(today.getDate() + (phaseIndex * 14) + (milestoneIndex * 3))

              events.push({
                id: `milestone-${roadmap.id}-${phaseIndex}-${milestoneIndex}`,
                title: milestone.title,
                date: dueDate,
                type: 'milestone',
                description: `${roadmap.title} - ${phase.title}`,
                roadmapId: roadmap.id,
                phaseNumber: phase.phase_number
              })
            }
          })

          // Add learning activities
          phase.learning_resources.forEach((resource, resourceIndex: number) => {
            const startDate = new Date(today)
            startDate.setDate(today.getDate() + (phaseIndex * 14) + (resourceIndex * 2))

            events.push({
              id: `learning-${roadmap.id}-${phaseIndex}-${resourceIndex}`,
              title: `Study: ${resource.title}`,
              date: startDate,
              type: 'learning',
              description: resource.description,
              roadmapId: roadmap.id,
              phaseNumber: phase.phase_number
            })
          })
        })
      }
    })

    setCalendarEvents(events)
  }

  const handleTodoComplete = (todoId: string) => {
    console.log('Todo completed:', todoId)
    // In a real app, this would update the backend
  }

  const handleTodoUpdate = (todoId: string, updates: any) => {
    console.log('Todo updated:', todoId, updates)
    // In a real app, this would update the backend
  }

  const handleEventComplete = (eventId: string) => {
    setCalendarEvents(prev => 
      prev.map((event: CalendarEvent) => 
        event.id === eventId ? { ...event, completed: true } : event
      )
    )
  }

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
      return
    }
    // If user is authenticated but doesn't have a profile, redirect to onboarding
    // Wait for both auth loading and profile loading to complete
    if (!loading && !profileLoading && user && !profile) {
      router.push('/onboarding')
      return
    }
  }, [user, profile, loading, profileLoading, router])

  if (loading || profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Trajectory.AI
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {user.email}
              </span>
              <button
                onClick={signOut}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <DashboardStats user={user} profile={profile} />
            
            <QuickActions 
              profile={profile} 
              onEditProfile={() => router.push('/profile/edit')}
              onStartOnboarding={() => router.push('/onboarding')}
            />
          </div>
          
          {/* Main AI Features */}
          <div className="bg-white rounded-lg shadow">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6" aria-label="Tabs">
                <button
                  data-tab="daily"
                  onClick={() => setActiveTab('daily')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'daily'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Daily Dashboard
                </button>
                <button
                  data-tab="chat"
                  onClick={() => setActiveTab('chat')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'chat'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  AI Career Mentor
                </button>
                <button
                  data-tab="roadmap"
                  onClick={() => setActiveTab('roadmap')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'roadmap'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Career Roadmap
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'daily' ? (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Daily Dashboard
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Track your progress, manage tasks, and stay organized in your career development journey.
                  </p>
                  
                  {/* Daily Dashboard Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Progress Tracker */}
                    <div className="lg:col-span-2">
                      <ProgressTracker roadmaps={roadmaps} userId={user?.id || 'temp_user_123'} />
                    </div>
                    
                    {/* Calendar Component */}
                    <CalendarComponent 
                      events={calendarEvents}
                      onEventComplete={handleEventComplete}
                      onEventClick={(event) => console.log('Event clicked:', event)}
                      onDateClick={(date) => console.log('Date clicked:', date)}
                    />
                    
                    {/* Todo List */}
                    <TodoList 
                      roadmaps={roadmaps}
                      onTodoComplete={handleTodoComplete}
                      onTodoUpdate={handleTodoUpdate}
                    />
                    
                    {/* Notes Component */}
                    <div className="lg:col-span-2">
                      <NotesComponent userId={user?.id || 'temp_user_123'} />
                    </div>
                  </div>
                </div>
              ) : activeTab === 'chat' ? (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    AI Career Mentor
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Get personalized career advice based on your profile and resume.
                  </p>
                  <div className="h-96">
                    <ChatInterface />
                  </div>
                </div>
              ) : (
                <RoadmapInterface />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}