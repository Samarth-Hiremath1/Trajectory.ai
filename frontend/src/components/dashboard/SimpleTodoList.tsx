'use client'

import { useState, useEffect, useCallback } from 'react'
import { ClockIcon, ExclamationTriangleIcon, PlusIcon, RocketLaunchIcon } from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import { taskSyncManager, Task } from '@/lib/taskSync'

interface SimpleTodoListProps {
  onTaskStatusUpdate?: (taskId: string, status: string) => void
  onClearAll?: () => void
  userId?: string
}

export function SimpleTodoList({ onTaskStatusUpdate, onClearAll, userId }: SimpleTodoListProps) {
  const router = useRouter()
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [filter, setFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed' | 'cancelled'>('all')
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskDescription, setNewTaskDescription] = useState('')
  const [newTaskPriority, setNewTaskPriority] = useState<'high' | 'medium' | 'low'>('medium')

  // Load tasks from localStorage
  const loadTasks = useCallback(() => {
    if (!userId) return
    const localTasks = taskSyncManager.getLocalTasks(userId)
    setTasks(localTasks)
  }, [userId])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  // Listen for task updates
  useEffect(() => {
    const unsubscribe = taskSyncManager.subscribe(() => {
      loadTasks()
    })

    const handleTasksUpdated = () => {
      loadTasks()
    }

    const handleTasksExported = () => {
      loadTasks()
    }

    window.addEventListener('tasksUpdated', handleTasksUpdated)
    window.addEventListener('tasksExported', handleTasksExported)
    
    return () => {
      unsubscribe()
      window.removeEventListener('tasksUpdated', handleTasksUpdated)
      window.removeEventListener('tasksExported', handleTasksExported)
    }
  }, [loadTasks])

  // Handle task status update
  const handleTaskStatusUpdate = (taskId: string, newStatus: Task['status']) => {
    if (!userId) return
    
    // Find the task to get its roadmap info
    const task = tasks.find(t => t.id === taskId)
    if (task) {
      // Update the task using the task sync manager
      taskSyncManager.updateTask(userId, taskId, { status: newStatus })
      
      // If this task is associated with a roadmap, also update via updateTaskStatus for roadmap sync
      if (task.roadmapId && task.phaseNumber !== undefined && task.milestoneIndex !== undefined) {
        // Map status values correctly for roadmap sync
        const roadmapStatus = newStatus === 'cancelled' ? 'skipped' : newStatus
        taskSyncManager.updateTaskStatus(userId, {
          id: taskId,
          roadmapId: task.roadmapId,
          phaseNumber: task.phaseNumber,
          milestoneIndex: task.milestoneIndex,
          status: roadmapStatus as 'pending' | 'in_progress' | 'completed' | 'skipped',
          title: task.title
        })
      }
    }
    
    if (onTaskStatusUpdate) {
      onTaskStatusUpdate(taskId, newStatus)
    }
  }

  // Handle manual task creation
  const handleAddManualTask = () => {
    if (!newTaskTitle.trim() || !userId) return

    taskSyncManager.addTask(userId, {
      title: newTaskTitle.trim(),
      description: newTaskDescription.trim() || undefined,
      status: 'pending',
      priority: newTaskPriority,
      task_type: 'manual',
      tags: ['Manual Task'],
      metadata: {}
    })
    
    // Reset form
    setNewTaskTitle('')
    setNewTaskDescription('')
    setNewTaskPriority('medium')
    setShowAddForm(false)
  }

  // Handle clear all tasks
  const handleClearAllTasks = () => {
    if (!userId) return
    
    const confirmClear = window.confirm(
      `Are you sure you want to delete all ${tasks.length} tasks? This action cannot be undone.`
    )
    
    if (!confirmClear) return

    taskSyncManager.clearAllTasks(userId)
    
    if (onClearAll) {
      onClearAll()
    }
  }

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200'
    }
  }

  const getTypeIcon = (type: Task['task_type']) => {
    switch (type) {
      case 'milestone':
        return '🎯'
      case 'learning':
        return '📚'
      case 'practice':
        return '💪'
      case 'skill':
        return '🔧'
      case 'manual':
        return '📝'
      default:
        return '📝'
    }
  }

  const isOverdue = (task: Task) => {
    return task.status !== 'completed' && task.due_date && new Date(task.due_date) < new Date()
  }

  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`
    if (diffDays === 0) return 'Due today'
    if (diffDays === 1) return 'Due tomorrow'
    if (diffDays <= 7) return `Due in ${diffDays} days`
    return date.toLocaleDateString()
  }

  // Filter tasks based on selected filter
  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true
    return task.status === filter
  }).sort((a, b) => {
    // Sort by priority, then by due date
    const priorityOrder = { high: 3, medium: 2, low: 1 }
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority]
    if (priorityDiff !== 0) return priorityDiff
    
    if (!a.due_date && !b.due_date) return 0
    if (!a.due_date) return 1
    if (!b.due_date) return -1
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
  })

  return (
    <div className="bg-white rounded-lg shadow p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Career To-Do List</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium"
        >
          Add Task
        </button>
      </div>

      {/* Filter Dropdown */}
      {tasks.length > 0 && (
        <div className="mb-4 flex-shrink-0">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter Tasks
          </label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as typeof filter)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Tasks</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="text-lg mb-2">⏳</div>
          <p className="text-gray-500">Loading tasks...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredTasks.length === 0 && (
        <div className="text-center py-12">
          <RocketLaunchIcon className="w-16 h-16 mx-auto text-indigo-400 mb-4" />
          <h4 className="text-lg font-semibold text-gray-900 mb-2">
            Ready to Get Started?
          </h4>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Your to-do list is empty. Export tasks from your roadmaps or add manual tasks to get started.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => router.push('/roadmaps')}
              className="inline-flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
            >
              <RocketLaunchIcon className="w-5 h-5 mr-2" />
              Export Tasks From Your Roadmap
            </button>
            <div className="text-sm text-gray-500">or</div>
            <button
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add a Manual Task
            </button>
          </div>
        </div>
      )}

      {/* Task List */}
      {!loading && filteredTasks.length > 0 && (
        <div className="space-y-3 max-h-[800px] overflow-y-auto">
          {filteredTasks.map(task => (
            <div
              key={task.id}
              className={`border rounded-lg p-4 bg-white ${
                isOverdue(task) ? 'border-red-300' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="relative mt-1">
                    <select
                      value={task.status}
                      onChange={(e) => handleTaskStatusUpdate(task.id, e.target.value as Task['status'])}
                      className="appearance-none bg-white border border-gray-300 rounded-md px-2 py-1 pr-6 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Complete</option>
                      <option value="cancelled">Skip</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-1 pointer-events-none">
                      <div className={`w-2 h-2 rounded-full ${
                        task.status === 'pending' ? 'bg-gray-400' :
                        task.status === 'in_progress' ? 'bg-yellow-400' :
                        task.status === 'completed' ? 'bg-green-400' :
                        'bg-black'
                      }`} />
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-lg">{getTypeIcon(task.task_type)}</span>
                      <h4 className="font-medium text-gray-900">
                        {task.title}
                      </h4>
                      <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(task.priority)}`}>
                        {task.priority}
                      </span>
                    </div>
                    
                    {task.description && (
                      <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      {task.due_date && (
                        <div className={`flex items-center space-x-1 ${
                          isOverdue(task) ? 'text-red-600' : ''
                        }`}>
                          <ClockIcon className="w-4 h-4" />
                          <span>{formatDueDate(task.due_date)}</span>
                          {isOverdue(task) && <ExclamationTriangleIcon className="w-4 h-4" />}
                        </div>
                      )}
                    </div>
                    
                    {task.tags && task.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {task.tags.map(tag => (
                          <span
                            key={tag}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Manual Task Creation Form */}
      {showAddForm && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border flex-shrink-0">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Add Manual Task</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task Title *
              </label>
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter task title..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                value={newTaskDescription}
                onChange={(e) => setNewTaskDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Add task description..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={newTaskPriority}
                onChange={(e) => setNewTaskPriority(e.target.value as 'high' | 'medium' | 'low')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
              </select>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowAddForm(false)
                  setNewTaskTitle('')
                  setNewTaskDescription('')
                  setNewTaskPriority('medium')
                }}
                className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleAddManualTask}
                disabled={!newTaskTitle.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md text-sm font-medium"
              >
                Add Task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}