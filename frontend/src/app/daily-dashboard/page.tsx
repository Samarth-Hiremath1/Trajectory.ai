'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState, useCallback } from 'react'
import { SimpleCalendarComponent } from '@/components/dashboard/SimpleCalendarComponent'
import { SimpleTodoList } from '@/components/dashboard/SimpleTodoList'
import { NotesComponent } from '@/components/dashboard/NotesComponent'
import { taskSyncManager } from '@/lib/taskSync'

interface CalendarEvent {
  id: string
  title: string
  date: Date
  type: 'milestone' | 'learning' | 'practice' | 'review'
  description?: string
  completed?: boolean
  skipped?: boolean
  roadmapId?: string
  phaseNumber?: number
}

export default function DailyDashboardPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)

  const generateCalendarEvents = useCallback(() => {
    if (!user?.id) return
    
    // Load exported events from localStorage (user-specific)
    const events: CalendarEvent[] = []
    try {
      const tasks = taskSyncManager.getLocalTasks(user.id)
      const exportedEvents: CalendarEvent[] = tasks.map((task) => ({
        id: task.id,
        title: task.title,
        date: task.due_date ? new Date(task.due_date) : new Date(),
        type: 'milestone' as const,
        description: task.description,
        completed: task.status === 'completed',
        skipped: task.status === 'cancelled',
        roadmapId: task.roadmapId,
        phaseNumber: task.phaseNumber
      }))
      events.push(...exportedEvents)
    } catch (error) {
      console.error('Error loading exported calendar events:', error)
    }

    setCalendarEvents(events)
  }, [user?.id])

  // Load calendar events on mount and when user changes
  useEffect(() => {
    generateCalendarEvents()
  }, [generateCalendarEvents])

  // Listen for task updates and refresh calendar events
  useEffect(() => {
    const handleTasksUpdated = () => {
      generateCalendarEvents()
    }

    const handleTasksExported = () => {
      generateCalendarEvents()
    }

    // Listen for task status changes from roadmap
    const unsubscribe = taskSyncManager.subscribe(() => {
      generateCalendarEvents()
    })

    window.addEventListener('tasksUpdated', handleTasksUpdated)
    window.addEventListener('tasksExported', handleTasksExported)
    
    return () => {
      unsubscribe()
      window.removeEventListener('tasksUpdated', handleTasksUpdated)
      window.removeEventListener('tasksExported', handleTasksExported)
    }
  }, [generateCalendarEvents])

  const handleTodoUpdate = (taskId: string, status: string) => {
    console.log('Todo updated:', taskId, status)
    // Trigger calendar events refresh when todo status changes
    generateCalendarEvents()
  }

  const handleClearAllCalendarEvents = async () => {
    if (!user?.id) return
    
    const confirmClear = window.confirm(
      `Are you sure you want to clear all calendar events? This will remove all exported tasks from your calendar.`
    )
    
    if (!confirmClear) return

    try {
      // Clear all tasks using task sync manager
      taskSyncManager.clearAllTasks(user.id)
      
      // Regenerate calendar events (will be empty after clearing)
      generateCalendarEvents()
      
      // Notify other components
      window.dispatchEvent(new CustomEvent('tasksUpdated'))
      
    } catch (error) {
      console.error('Error clearing calendar events:', error)
    }
  }

  const handleEventComplete = async (eventId: string) => {
    if (!user?.id) return
    
    // Find the event to get its details
    const event = calendarEvents.find(e => e.id === eventId)
    if (!event) return

    // Get the task details first to ensure we have all the metadata
    const tasks = taskSyncManager.getLocalTasks(user.id)
    const task = tasks.find(t => t.id === eventId)
    
    // Update the task status using task sync manager
    taskSyncManager.updateTask(user.id, eventId, { status: 'completed' })
    
    // If this event is associated with a roadmap, also update via updateTaskStatus for roadmap sync
    if (task && task.roadmapId && task.phaseNumber !== undefined && task.milestoneIndex !== undefined) {
      taskSyncManager.updateTaskStatus(user.id, {
        id: eventId,
        roadmapId: task.roadmapId,
        phaseNumber: task.phaseNumber,
        milestoneIndex: task.milestoneIndex,
        status: 'completed',
        title: task.title
      })
    }
  }

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(event)
    document.body.style.overflow = 'hidden'
  }

  const closeEventModal = () => {
    setSelectedEvent(null)
    document.body.style.overflow = 'unset'
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
                  onClick={() => router.push('/roadmaps')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium relative"
                >
                  Roadmaps
                </button>
                <button
                  onClick={() => router.push('/ai-mentor')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  AI Mentor
                </button>
                <button
                  onClick={() => router.push('/daily-dashboard')}
                  className="bg-indigo-100 text-indigo-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Daily Dashboard
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {profile?.name || user?.email?.split('@')[0] || 'User'}
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
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-2xl font-bold text-gray-900">
                Daily Dashboard
              </h2>
              {calendarEvents.length > 0 && (
                <button
                  onClick={handleClearAllCalendarEvents}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Clear All Tasks
                </button>
              )}
            </div>
            <p className="text-gray-600 mb-6">
              Track your progress, manage tasks, and stay organized in your career development journey.
            </p>
            
            {/* Daily Dashboard Grid */}
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[900px]">
                {/* Calendar Component */}
                <div className="h-full overflow-hidden">
                  <SimpleCalendarComponent 
                    events={calendarEvents}
                    onEventComplete={handleEventComplete}
                    onEventClick={handleEventClick}
                    onDateClick={(date) => console.log('Date clicked:', date)}
                  />
                </div>
                
                {/* Todo List */}
                <div className="h-full overflow-hidden">
                  <SimpleTodoList 
                    onTaskStatusUpdate={handleTodoUpdate}
                    onClearAll={handleClearAllCalendarEvents}
                    userId={user?.id}
                  />
                </div>
              </div>
              
              {/* Notes Component */}
              <div className="min-h-[400px] max-h-[600px] flex flex-col">
                <NotesComponent userId={user?.id || ''} />
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Event Details Modal */}
      {selectedEvent && (
        <>
          <div 
            className="fixed inset-0 z-40 transition-opacity duration-300"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              backdropFilter: 'blur(4px)',
              WebkitBackdropFilter: 'blur(4px)'
            }}
            onClick={closeEventModal}
          />
          
          <div className="fixed inset-y-0 right-0 w-full sm:w-3/5 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out">
            <div className="h-full flex flex-col">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{selectedEvent.title}</h3>
                    <p className="text-base text-gray-600">{selectedEvent.date.toLocaleDateString()}</p>
                  </div>
                  <button
                    onClick={closeEventModal}
                    className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Task Details</h4>
                  <p className="text-base text-gray-700 leading-relaxed">
                    {selectedEvent.description || 'No additional description available for this task.'}
                  </p>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Status</h4>
                  <div className="flex items-center space-x-2">
                    {selectedEvent.completed && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                        ✓ Completed
                      </span>
                    )}
                    {selectedEvent.skipped && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                        ⊘ Skipped
                      </span>
                    )}
                    {!selectedEvent.completed && !selectedEvent.skipped && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                        ⏳ Pending
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Task Type</h4>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    🎯 {selectedEvent.type.charAt(0).toUpperCase() + selectedEvent.type.slice(1)}
                  </span>
                </div>

                {selectedEvent.roadmapId && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-2">Source</h4>
                    <p className="text-base text-gray-700">
                      This task was exported from your career roadmap and is part of your structured learning path.
                    </p>
                  </div>
                )}


              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}