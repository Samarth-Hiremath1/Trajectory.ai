'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckIcon, ClockIcon, ExclamationTriangleIcon, PlusIcon, RocketLaunchIcon } from '@heroicons/react/24/outline'
import { Roadmap } from '@/types/roadmap'
import { useRouter } from 'next/navigation'

interface Task {
  id: string
  user_id: string
  roadmap_id?: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'high' | 'medium' | 'low'
  task_type: 'milestone' | 'learning' | 'practice' | 'skill' | 'manual'
  phase_number?: number
  milestone_index?: number
  skill_name?: string
  due_date?: string
  estimated_hours?: number
  actual_hours?: number
  tags: string[]
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  completed_at?: string
}

interface TaskStats {
  total_tasks: number
  pending_tasks: number
  in_progress_tasks: number
  completed_tasks: number
  overdue_tasks: number
  high_priority_tasks: number
  roadmap_generated_tasks: number
  manual_tasks: number
  completion_rate: number
  average_completion_time_hours?: number
}

interface TodoListProps {
  roadmaps: Roadmap[]
  onTodoComplete?: (todoId: string) => void
  onTodoUpdate?: (todoId: string, updates: any) => void
  onAddTodo?: (todo: any) => void
}

export function TodoList({ roadmaps, onTodoComplete, onTodoUpdate, onAddTodo }: TodoListProps) {
  const router = useRouter()
  const [tasks, setTasks] = useState<Task[]>([])
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'overdue'>('pending')
  const [sortBy, setSortBy] = useState<'priority' | 'dueDate' | 'type'>('priority')
  const [showAddForm, setShowAddForm] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskDescription, setNewTaskDescription] = useState('')
  const [newTaskPriority, setNewTaskPriority] = useState<'high' | 'medium' | 'low'>('medium')

  // Check if user has any roadmaps
  const hasRoadmaps = roadmaps && roadmaps.length > 0

  // Fetch tasks from the API
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('/api/tasks')
      if (!response.ok) {
        // If tasks API is not available, fall back to empty state
        if (response.status === 500) {
          console.warn('Tasks API not available, using empty state')
          setTasks([])
          return
        }
        throw new Error('Failed to fetch tasks')
      }

      const data = await response.json()
      if (data.success) {
        setTasks(data.tasks || [])
      } else {
        throw new Error(data.message || 'Failed to fetch tasks')
      }
    } catch (err) {
      console.error('Error fetching tasks:', err)
      // For now, just use empty state if API fails
      setTasks([])
      setError(null) // Don't show error to user, just use fallback
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch task statistics
  const fetchTaskStats = useCallback(async () => {
    try {
      const response = await fetch('/api/tasks/stats')
      if (response.ok) {
        const stats = await response.json()
        setTaskStats(stats)
      }
    } catch (err) {
      console.error('Error fetching task stats:', err)
    }
  }, [])

  // Generate tasks from roadmaps
  const generateTasksFromRoadmaps = useCallback(async () => {
    if (!hasRoadmaps) return

    try {
      for (const roadmap of roadmaps) {
        if (roadmap.status === 'active') {
          const response = await fetch(`/api/tasks/generate/roadmap/${roadmap.id}`, {
            method: 'POST'
          })
          
          if (response.ok) {
            console.log(`Generated tasks for roadmap: ${roadmap.title}`)
          }
        }
      }
      
      // Refresh tasks after generation
      await fetchTasks()
    } catch (err) {
      console.error('Error generating tasks from roadmaps:', err)
    }
  }, [roadmaps, hasRoadmaps, fetchTasks])

  useEffect(() => {
    fetchTasks()
    fetchTaskStats()
  }, [fetchTasks, fetchTaskStats])

  useEffect(() => {
    // Generate tasks from roadmaps if we have roadmaps but no tasks
    if (hasRoadmaps && tasks.length === 0 && !loading) {
      generateTasksFromRoadmaps()
    }
  }, [hasRoadmaps, tasks.length, loading, generateTasksFromRoadmaps])

  // Filter and sort tasks
  const filteredTasks = tasks.filter(task => {
    switch (filter) {
      case 'completed':
        return task.status === 'completed'
      case 'pending':
        return task.status === 'pending' || task.status === 'in_progress'
      case 'overdue':
        return task.status !== 'completed' && task.due_date && new Date(task.due_date) < new Date()
      default:
        return true
    }
  })

  const sortedTasks = [...filteredTasks].sort((a, b) => {
    switch (sortBy) {
      case 'priority':
        const priorityOrder = { high: 3, medium: 2, low: 1 }
        return priorityOrder[b.priority] - priorityOrder[a.priority]
      case 'dueDate':
        if (!a.due_date && !b.due_date) return 0
        if (!a.due_date) return 1
        if (!b.due_date) return -1
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
      case 'type':
        return a.task_type.localeCompare(b.task_type)
      default:
        return 0
    }
  })

  // Handle task completion
  const handleTaskComplete = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/complete`, {
        method: 'POST'
      })

      if (response.ok) {
        await fetchTasks()
        await fetchTaskStats()
        if (onTodoComplete) {
          onTodoComplete(taskId)
        }
      } else {
        throw new Error('Failed to complete task')
      }
    } catch (err) {
      console.error('Error completing task:', err)
      setError('Failed to complete task')
    }
  }

  // Handle manual task creation
  const handleAddManualTask = async () => {
    if (!newTaskTitle.trim()) return

    try {
      const taskData = {
        title: newTaskTitle.trim(),
        description: newTaskDescription.trim() || undefined,
        priority: newTaskPriority,
        task_type: 'manual',
        tags: ['Manual Task']
      }

      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      })

      if (response.ok) {
        await fetchTasks()
        await fetchTaskStats()
        
        // Reset form
        setNewTaskTitle('')
        setNewTaskDescription('')
        setNewTaskPriority('medium')
        setShowAddForm(false)

        if (onAddTodo) {
          onAddTodo(taskData)
        }
      } else {
        throw new Error('Failed to create task')
      }
    } catch (err) {
      console.error('Error creating task:', err)
      setError('Failed to create task')
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

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Career To-Do List</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium"
        >
          Add Task
        </button>
      </div>

      {/* Filters and Sorting */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Filter:</label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All Tasks</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
            <option value="overdue">Overdue</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="priority">Priority</option>
            <option value="dueDate">Due Date</option>
            <option value="type">Type</option>
          </select>
        </div>
      </div>

      {/* Task Statistics - Only show if there are tasks */}
      {taskStats && taskStats.total_tasks > 0 && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{taskStats.pending_tasks + taskStats.in_progress_tasks}</div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{taskStats.completed_tasks}</div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{taskStats.overdue_tasks}</div>
            <div className="text-sm text-gray-600">Overdue</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{taskStats.high_priority_tasks}</div>
            <div className="text-sm text-gray-600">High Priority</div>
          </div>
        </div>
      )}

      {/* Loading and Error States */}
      {loading && (
        <div className="text-center py-8">
          <div className="text-lg mb-2">⏳</div>
          <p className="text-gray-500">Loading tasks...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <div className="text-lg mb-2">❌</div>
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchTasks}
            className="mt-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {/* Task List */}
      {!loading && !error && (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {sortedTasks.map(task => (
            <div
              key={task.id}
              className={`border rounded-lg p-4 ${
                task.status === 'completed' ? 'bg-gray-50 opacity-75' : 'bg-white'
              } ${isOverdue(task) ? 'border-red-300' : 'border-gray-200'}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <button
                    onClick={() => handleTaskComplete(task.id)}
                    className={`mt-1 w-5 h-5 rounded border-2 flex items-center justify-center ${
                      task.status === 'completed'
                        ? 'bg-green-500 border-green-500 text-white'
                        : 'border-gray-300 hover:border-green-500'
                    }`}
                  >
                    {task.status === 'completed' && <CheckIcon className="w-3 h-3" />}
                  </button>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-lg">{getTypeIcon(task.task_type)}</span>
                      <h4 className={`font-medium ${
                        task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'
                      }`}>
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
                      
                      {task.estimated_hours && (
                        <span>{task.estimated_hours}h estimated</span>
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
          
          {/* Empty State with Meaningful Messages */}
          {sortedTasks.length === 0 && (
          <div className="text-center py-8">
            {filter === 'completed' ? (
              <div className="text-gray-500">
                <div className="text-lg mb-2">🎉</div>
                <p>No completed tasks yet.</p>
                <p className="text-sm mt-1">Complete some tasks to see them here!</p>
              </div>
            ) : filter === 'overdue' ? (
              <div className="text-gray-500">
                <div className="text-lg mb-2">✅</div>
                <p>No overdue tasks.</p>
                <p className="text-sm mt-1">Great job staying on track!</p>
              </div>
            ) : !hasRoadmaps ? (
              // No roadmaps exist - encourage roadmap generation
              <div className="text-gray-600">
                <RocketLaunchIcon className="w-16 h-16 mx-auto text-indigo-400 mb-4" />
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Ready to Launch Your Career Journey?
                </h4>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Generate your first career roadmap to get personalized tasks and milestones 
                  that will guide you toward your dream role.
                </p>
                <div className="space-y-3">
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="inline-flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                  >
                    <RocketLaunchIcon className="w-5 h-5 mr-2" />
                    Generate Your First Roadmap
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
            ) : (
              // Has roadmaps but no tasks
              <div className="text-gray-500">
                <div className="text-lg mb-2">📋</div>
                <p>No tasks found.</p>
                <p className="text-sm mt-1">
                  Tasks will be automatically generated from your active roadmaps.
                </p>
              </div>
            )}
          </div>
        )}
        </div>
      )}

      {/* Manual Task Creation Form */}
      {showAddForm && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
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