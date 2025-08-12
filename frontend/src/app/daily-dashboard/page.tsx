'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState, useCallback } from 'react'
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

export default function DailyDashboardPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([])
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([])

  const loadRoadmaps = useCallback(async () => {
    if (!user?.id) return
    
    try {
      const response = await fetch(`/api/roadmap/user/${user.id}`)
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
  }, [user?.id])

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

    // Load exported events from localStorage
    try {
      const storedTasks = localStorage.getItem('tasks')
      if (storedTasks) {
        const parsedTasks = JSON.parse(storedTasks)
        const exportedEvents: CalendarEvent[] = parsedTasks.map((task: any, index: number) => ({
          id: `exported-event-${index}-${Date.now()}`,
          title: task.title,
          date: new Date(task.dueDate),
          type: 'milestone' as const,
          description: task.description,
          completed: task.completed || false
        }))
        events.push(...exportedEvents)
      }
    } catch (error) {
      console.error('Error loading exported calendar events:', error)
    }

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
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-semibold text-gray-900">
                Trajectory.AI
              </h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/daily-dashboard')}
                  className="bg-indigo-100 text-indigo-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Daily Dashboard
                </button>
                <button
                  onClick={() => router.push('/ai-mentor')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  AI Mentor
                </button>
                <button
                  onClick={() => router.push('/roadmaps')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Roadmaps
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {profile?.name || user.email}
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
          <div className="bg-white rounded-lg shadow p-6">
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
                <ProgressTracker roadmaps={roadmaps} userId={user?.id || ''} />
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
                <NotesComponent userId={user?.id || ''} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}