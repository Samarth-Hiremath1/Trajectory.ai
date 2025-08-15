// Simplified task synchronization utility

export interface Task {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'high' | 'medium' | 'low'
  task_type: 'milestone' | 'learning' | 'practice' | 'skill' | 'manual'
  due_date?: string
  tags: string[]
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  roadmapId?: string
  phaseNumber?: number
  milestoneIndex?: number
}

export interface TaskSyncData {
  id: string
  roadmapId?: string
  phaseNumber?: number
  milestoneIndex?: number
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  title: string
}

class TaskSyncManager {
  private listeners: Set<() => void> = new Set()
  private dataListeners: Set<(data: TaskSyncData) => void> = new Set()

  // Subscribe to task updates (simple callback)
  subscribe(callback: () => void): () => void
  // Subscribe to task updates (with data callback)
  subscribe(callback: (data: TaskSyncData) => void): () => void
  subscribe(callback: (() => void) | ((data: TaskSyncData) => void)) {
    if (callback.length === 0) {
      // Simple callback
      this.listeners.add(callback as () => void)
      return () => this.listeners.delete(callback as () => void)
    } else {
      // Data callback
      this.dataListeners.add(callback as (data: TaskSyncData) => void)
      return () => this.dataListeners.delete(callback as (data: TaskSyncData) => void)
    }
  }

  // Notify all listeners of task changes
  notifyListeners(data?: TaskSyncData) {
    this.listeners.forEach(callback => callback())
    if (data) {
      this.dataListeners.forEach(callback => callback(data))
    }
    // Also dispatch a global event
    window.dispatchEvent(new CustomEvent('tasksUpdated'))
  }

  // Update task status and notify with data
  updateTaskStatus(userId: string, data: TaskSyncData) {
    console.log('TaskSyncManager: updateTaskStatus called with:', data)
    
    const tasks = this.getLocalTasks(userId)
    console.log('TaskSyncManager: Found tasks:', tasks.length)
    
    // Try to find task by roadmap metadata first (more reliable)
    let taskIndex = -1
    if (data.roadmapId && data.phaseNumber !== undefined && data.milestoneIndex !== undefined) {
      taskIndex = tasks.findIndex(t => 
        t.roadmapId === data.roadmapId &&
        t.phaseNumber === data.phaseNumber &&
        t.milestoneIndex === data.milestoneIndex
      )
      console.log('TaskSyncManager: Found task by metadata at index:', taskIndex)
    }
    
    // If not found by metadata, try by ID (but be more flexible with ID matching)
    if (taskIndex === -1) {
      // Try exact ID match first
      taskIndex = tasks.findIndex(t => t.id === data.id)
      
      // If still not found, try to find by ID pattern (for milestone tasks)
      if (taskIndex === -1 && data.roadmapId && data.phaseNumber !== undefined && data.milestoneIndex !== undefined) {
        taskIndex = tasks.findIndex(t => 
          t.id.includes(`milestone-${data.roadmapId}-${data.phaseNumber}-${data.milestoneIndex}`)
        )
      }
      
      console.log('TaskSyncManager: Found task by ID at index:', taskIndex)
    }
    
    if (taskIndex !== -1) {
      const oldStatus = tasks[taskIndex].status
      // Map status values correctly
      const newStatus = data.status === 'skipped' ? 'cancelled' : data.status
      tasks[taskIndex].status = newStatus
      tasks[taskIndex].updated_at = new Date().toISOString()
      
      console.log(`TaskSyncManager: Updated task ${tasks[taskIndex].title} from ${oldStatus} to ${newStatus}`)
      
      this.saveLocalTasks(userId, tasks, data)
    } else {
      console.warn('TaskSyncManager: Task not found for update:', data)
      console.warn('TaskSyncManager: Available tasks:', tasks.map(t => ({
        id: t.id,
        title: t.title,
        roadmapId: t.roadmapId,
        phaseNumber: t.phaseNumber,
        milestoneIndex: t.milestoneIndex
      })))
    }
  }

  private getCurrentUserId(): string | null {
    // Try to get user ID from various sources
    if (typeof window !== 'undefined') {
      // Try to get from localStorage first
      const storedUserId = window.localStorage.getItem('user_id')
      if (storedUserId) return storedUserId
      
      // Try to get from session storage
      const sessionUserId = window.sessionStorage.getItem('user_id')
      if (sessionUserId) return sessionUserId
      
      // Try to extract from other localStorage keys that might contain user info
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('tasks_')) {
          const userId = key.replace('tasks_', '')
          if (userId && userId !== 'undefined' && userId !== 'null') {
            return userId
          }
        }
      }
    }
    return null
  }

  // Get tasks from localStorage for a user
  getLocalTasks(userId: string): Task[] {
    try {
      const stored = localStorage.getItem(`tasks_${userId}`)
      return stored ? JSON.parse(stored) : []
    } catch (error) {
      console.error('Error getting local tasks:', error)
      return []
    }
  }

  // Save tasks to localStorage for a user
  saveLocalTasks(userId: string, tasks: Task[], data?: TaskSyncData) {
    try {
      localStorage.setItem(`tasks_${userId}`, JSON.stringify(tasks))
      this.notifyListeners(data)
    } catch (error) {
      console.error('Error saving local tasks:', error)
    }
  }

  // Add a task
  addTask(userId: string, task: Omit<Task, 'id' | 'created_at' | 'updated_at'>): Task {
    const newTask: Task = {
      ...task,
      id: Date.now().toString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    const tasks = this.getLocalTasks(userId)
    tasks.push(newTask)
    this.saveLocalTasks(userId, tasks)

    // Try to sync to API
    this.syncTaskToAPI(newTask).catch(console.error)

    return newTask
  }

  // Update a task
  updateTask(userId: string, taskId: string, updates: Partial<Task>): Task | null {
    const tasks = this.getLocalTasks(userId)
    const taskIndex = tasks.findIndex(t => t.id === taskId)
    
    if (taskIndex === -1) return null

    const originalTask = tasks[taskIndex]
    const updatedTask = {
      ...originalTask,
      ...updates,
      updated_at: new Date().toISOString()
    }

    tasks[taskIndex] = updatedTask

    // Create TaskSyncData if status was updated and task has roadmap info
    let syncData: TaskSyncData | undefined
    if (updates.status && originalTask.roadmapId) {
      // Map task status to roadmap status
      const roadmapStatus = updates.status === 'cancelled' ? 'skipped' : updates.status
      syncData = {
        id: taskId,
        roadmapId: originalTask.roadmapId,
        phaseNumber: originalTask.phaseNumber,
        milestoneIndex: originalTask.milestoneIndex,
        status: roadmapStatus as 'pending' | 'in_progress' | 'completed' | 'skipped',
        title: originalTask.title
      }
    }

    this.saveLocalTasks(userId, tasks, syncData)

    // Try to sync to API
    this.syncTaskUpdateToAPI(taskId, updates).catch(console.error)

    return updatedTask
  }

  // Delete a task
  deleteTask(userId: string, taskId: string): boolean {
    const tasks = this.getLocalTasks(userId)
    const taskIndex = tasks.findIndex(t => t.id === taskId)
    
    if (taskIndex === -1) return false

    tasks.splice(taskIndex, 1)
    this.saveLocalTasks(userId, tasks)

    // Try to sync to API
    this.deleteTaskFromAPI(taskId).catch(console.error)

    return true
  }

  // Clear all tasks
  clearAllTasks(userId: string) {
    this.saveLocalTasks(userId, [])
    
    // Try to sync to API
    this.clearAllTasksFromAPI().catch(console.error)
  }

  // Export tasks from roadmap
  exportTasksFromRoadmap(userId: string, roadmap: any): Task[] {
    console.log('TaskSyncManager: Exporting tasks from roadmap:', roadmap.id, 'for user:', userId)
    
    const existingTasks = this.getLocalTasks(userId)
    const newTasks: Task[] = []

    // Check for existing tasks from this roadmap
    const existingRoadmapTasks = existingTasks.filter(task => task.roadmapId === roadmap.id)
    if (existingRoadmapTasks.length > 0) {
      const shouldProceed = confirm(`This roadmap has already been exported (${existingRoadmapTasks.length} tasks). Do you want to export again? This will create duplicate tasks.`)
      if (!shouldProceed) return []
    }

    let currentWeek = 1

    for (const phase of roadmap.phases) {
      // Add milestones as tasks
      for (let i = 0; i < phase.milestones.length; i++) {
        const milestone = phase.milestones[i]
        const milestoneWeek = currentWeek + (milestone.estimated_completion_weeks || 1) - 1
        
        const task: Task = {
          id: `milestone-${roadmap.id}-${phase.phase_number}-${i}-${Date.now()}`,
          title: milestone.title,
          description: milestone.description || `Milestone for ${phase.title.replace(/\*\*/g, '')}`,
          status: milestone.is_completed ? 'completed' : 'pending',
          priority: milestone.estimated_completion_weeks <= 2 ? 'high' : 'medium',
          task_type: 'milestone',
          due_date: new Date(Date.now() + (milestoneWeek - 1) * 7 * 24 * 60 * 60 * 1000).toISOString(),
          tags: ['Career Development', 'Exported from Roadmap'],
          metadata: {
            roadmap_id: roadmap.id,
            phase_number: phase.phase_number,
            milestone_index: i,
            source: 'roadmap'
          },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          roadmapId: roadmap.id,
          phaseNumber: phase.phase_number,
          milestoneIndex: i
        }
        
        newTasks.push(task)
      }
      
      currentWeek += phase.duration_weeks || 4
    }

    // Add new tasks to existing tasks and save without triggering data listeners
    const allTasks = [...existingTasks, ...newTasks]
    try {
      localStorage.setItem(`tasks_${userId}`, JSON.stringify(allTasks))
      // Only notify simple listeners for UI refresh, not data listeners
      this.listeners.forEach(callback => callback())
      window.dispatchEvent(new CustomEvent('tasksUpdated'))
    } catch (error) {
      console.error('Error saving local tasks:', error)
    }

    // Try to sync to API
    newTasks.forEach(task => {
      this.syncTaskToAPI(task).catch(console.error)
    })

    return newTasks
  }

  // Sync task to API (best effort)
  private async syncTaskToAPI(task: Task) {
    try {
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task)
      })
    } catch (error) {
      console.warn('Failed to sync task to API:', error)
    }
  }

  // Sync task update to API (best effort)
  private async syncTaskUpdateToAPI(taskId: string, updates: Partial<Task>) {
    try {
      await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
    } catch (error) {
      console.warn('Failed to sync task update to API:', error)
    }
  }

  // Delete task from API (best effort)
  private async deleteTaskFromAPI(taskId: string) {
    try {
      await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
      })
    } catch (error) {
      console.warn('Failed to delete task from API:', error)
    }
  }

  // Clear all tasks from API (best effort)
  private async clearAllTasksFromAPI() {
    try {
      await fetch('/api/tasks', {
        method: 'DELETE'
      })
    } catch (error) {
      console.warn('Failed to clear tasks from API:', error)
    }
  }

  // Debug method to help troubleshoot synchronization issues
  debugTaskSync(userId: string, roadmapId: string) {
    const tasks = this.getLocalTasks(userId)
    const roadmapTasks = tasks.filter(t => t.roadmapId === roadmapId)
    
    console.log('=== Task Sync Debug ===')
    console.log('User ID:', userId)
    console.log('Roadmap ID:', roadmapId)
    console.log('Total tasks:', tasks.length)
    console.log('Roadmap tasks:', roadmapTasks.length)
    console.log('Roadmap tasks details:', roadmapTasks.map(t => ({
      id: t.id,
      title: t.title,
      status: t.status,
      phaseNumber: t.phaseNumber,
      milestoneIndex: t.milestoneIndex
    })))
    console.log('======================')
    
    return roadmapTasks
  }
}

export const taskSyncManager = new TaskSyncManager()