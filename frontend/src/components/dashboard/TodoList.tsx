'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { Roadmap } from '@/types/roadmap'

interface TodoItem {
  id: string
  title: string
  description?: string
  priority: 'high' | 'medium' | 'low'
  dueDate?: Date
  completed: boolean
  type: 'milestone' | 'learning' | 'practice' | 'skill'
  roadmapId?: string
  phaseNumber?: number
  milestoneIndex?: number
  estimatedHours?: number
  tags?: string[]
}

interface TodoListProps {
  roadmaps: Roadmap[]
  onTodoComplete: (todoId: string) => void
  onTodoUpdate: (todoId: string, updates: Partial<TodoItem>) => void
  onAddTodo?: (todo: Omit<TodoItem, 'id'>) => void
}

export function TodoList({ roadmaps, onTodoComplete, onTodoUpdate, onAddTodo }: TodoListProps) {
  const [todos, setTodos] = useState<TodoItem[]>([])
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'overdue'>('pending')
  const [sortBy, setSortBy] = useState<'priority' | 'dueDate' | 'type'>('priority')
  const [showAddForm, setShowAddForm] = useState(false)

  const generateTodosFromRoadmaps = useCallback(() => {
    const generatedTodos: TodoItem[] = []

    roadmaps.forEach(roadmap => {
      if (roadmap.status === 'active') {
        roadmap.phases.forEach((phase, phaseIndex) => {
          // Add milestone todos
          phase.milestones.forEach((milestone, milestoneIndex) => {
            if (!milestone.is_completed) {
              generatedTodos.push({
                id: `milestone-${roadmap.id}-${phaseIndex}-${milestoneIndex}`,
                title: milestone.title,
                description: milestone.description,
                priority: phaseIndex === (roadmap.current_phase || 0) ? 'high' : 'medium',
                dueDate: milestone.estimated_completion_weeks ? 
                  new Date(Date.now() + milestone.estimated_completion_weeks * 7 * 24 * 60 * 60 * 1000) : 
                  undefined,
                completed: milestone.is_completed,
                type: 'milestone',
                roadmapId: roadmap.id,
                phaseNumber: phase.phase_number,
                milestoneIndex,
                tags: [roadmap.target_role, `Phase ${phase.phase_number}`]
              })
            }
          })

          // Add skill development todos
          phase.skills_to_develop.forEach((skill, skillIndex) => {
            if (skill.current_level !== skill.target_level) {
              generatedTodos.push({
                id: `skill-${roadmap.id}-${phaseIndex}-${skillIndex}`,
                title: `Develop ${skill.name} skill`,
                description: `Progress from ${skill.current_level} to ${skill.target_level}`,
                priority: skill.priority <= 2 ? 'high' : skill.priority <= 3 ? 'medium' : 'low',
                completed: false,
                type: 'skill',
                roadmapId: roadmap.id,
                phaseNumber: phase.phase_number,
                estimatedHours: skill.estimated_hours,
                tags: [roadmap.target_role, skill.name, `Phase ${phase.phase_number}`]
              })
            }
          })

          // Add learning resource todos
          phase.learning_resources.forEach((resource, resourceIndex) => {
            generatedTodos.push({
              id: `learning-${roadmap.id}-${phaseIndex}-${resourceIndex}`,
              title: `Complete: ${resource.title}`,
              description: resource.description,
              priority: 'medium',
              completed: false,
              type: 'learning',
              roadmapId: roadmap.id,
              phaseNumber: phase.phase_number,
              tags: [roadmap.target_role, resource.resource_type, `Phase ${phase.phase_number}`]
            })
          })
        })
      }
    })

    setTodos(generatedTodos)
  }, [roadmaps])

  useEffect(() => {
    generateTodosFromRoadmaps()
  }, [generateTodosFromRoadmaps])

  const filteredTodos = todos.filter(todo => {
    switch (filter) {
      case 'completed':
        return todo.completed
      case 'pending':
        return !todo.completed
      case 'overdue':
        return !todo.completed && todo.dueDate && todo.dueDate < new Date()
      default:
        return true
    }
  })

  const sortedTodos = [...filteredTodos].sort((a, b) => {
    switch (sortBy) {
      case 'priority':
        const priorityOrder = { high: 3, medium: 2, low: 1 }
        return priorityOrder[b.priority] - priorityOrder[a.priority]
      case 'dueDate':
        if (!a.dueDate && !b.dueDate) return 0
        if (!a.dueDate) return 1
        if (!b.dueDate) return -1
        return a.dueDate.getTime() - b.dueDate.getTime()
      case 'type':
        return a.type.localeCompare(b.type)
      default:
        return 0
    }
  })

  const handleTodoComplete = (todoId: string) => {
    setTodos(prev => prev.map(todo => 
      todo.id === todoId ? { ...todo, completed: !todo.completed } : todo
    ))
    onTodoComplete(todoId)
  }

  const getPriorityColor = (priority: TodoItem['priority']) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200'
    }
  }

  const getTypeIcon = (type: TodoItem['type']) => {
    switch (type) {
      case 'milestone':
        return '🎯'
      case 'learning':
        return '📚'
      case 'practice':
        return '💪'
      case 'skill':
        return '🔧'
      default:
        return '📝'
    }
  }

  const isOverdue = (todo: TodoItem) => {
    return !todo.completed && todo.dueDate && todo.dueDate < new Date()
  }

  const formatDueDate = (date: Date) => {
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

      {/* Todo Statistics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{todos.filter(t => !t.completed).length}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{todos.filter(t => t.completed).length}</div>
          <div className="text-sm text-gray-600">Completed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{todos.filter(t => isOverdue(t)).length}</div>
          <div className="text-sm text-gray-600">Overdue</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">{todos.filter(t => t.priority === 'high' && !t.completed).length}</div>
          <div className="text-sm text-gray-600">High Priority</div>
        </div>
      </div>

      {/* Todo List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {sortedTodos.map(todo => (
          <div
            key={todo.id}
            className={`border rounded-lg p-4 ${
              todo.completed ? 'bg-gray-50 opacity-75' : 'bg-white'
            } ${isOverdue(todo) ? 'border-red-300' : 'border-gray-200'}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <button
                  onClick={() => handleTodoComplete(todo.id)}
                  className={`mt-1 w-5 h-5 rounded border-2 flex items-center justify-center ${
                    todo.completed
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'border-gray-300 hover:border-green-500'
                  }`}
                >
                  {todo.completed && <CheckIcon className="w-3 h-3" />}
                </button>
                
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-lg">{getTypeIcon(todo.type)}</span>
                    <h4 className={`font-medium ${
                      todo.completed ? 'line-through text-gray-500' : 'text-gray-900'
                    }`}>
                      {todo.title}
                    </h4>
                    <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(todo.priority)}`}>
                      {todo.priority}
                    </span>
                  </div>
                  
                  {todo.description && (
                    <p className="text-sm text-gray-600 mb-2">{todo.description}</p>
                  )}
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    {todo.dueDate && (
                      <div className={`flex items-center space-x-1 ${
                        isOverdue(todo) ? 'text-red-600' : ''
                      }`}>
                        <ClockIcon className="w-4 h-4" />
                        <span>{formatDueDate(todo.dueDate)}</span>
                        {isOverdue(todo) && <ExclamationTriangleIcon className="w-4 h-4" />}
                      </div>
                    )}
                    
                    {todo.estimatedHours && (
                      <span>{todo.estimatedHours}h estimated</span>
                    )}
                  </div>
                  
                  {todo.tags && todo.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {todo.tags.map(tag => (
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
        
        {sortedTodos.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            {filter === 'completed' ? 'No completed tasks yet.' : 
             filter === 'overdue' ? 'No overdue tasks.' :
             'No tasks found. Tasks will be automatically generated from your active roadmaps.'}
          </div>
        )}
      </div>
    </div>
  )
}