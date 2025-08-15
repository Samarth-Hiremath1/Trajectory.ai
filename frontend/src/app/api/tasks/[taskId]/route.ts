import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth-options'

// Simple in-memory storage for tasks (in production, this would be a database)
const tasks: Record<string, any[]> = {}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ taskId: string }> }
) {
  try {
    const params = await context.params
    const session = await getServerSession(authOptions)
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    const userTasks = tasks[session.user.id] || []
    
    const taskIndex = userTasks.findIndex(task => task.id === params.taskId)
    if (taskIndex === -1) {
      return NextResponse.json({ error: 'Task not found' }, { status: 404 })
    }

    // Update the task
    const updatedTask = {
      ...userTasks[taskIndex],
      ...body,
      updated_at: new Date().toISOString()
    }
    
    userTasks[taskIndex] = updatedTask
    tasks[session.user.id] = userTasks
    
    return NextResponse.json({
      success: true,
      task: updatedTask
    })
  } catch (error) {
    console.error('Error updating task:', error)
    return NextResponse.json(
      { error: 'Failed to update task' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ taskId: string }> }
) {
  try {
    const params = await context.params
    const session = await getServerSession(authOptions)
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const userTasks = tasks[session.user.id] || []
    const taskIndex = userTasks.findIndex(task => task.id === params.taskId)
    
    if (taskIndex === -1) {
      return NextResponse.json({ error: 'Task not found' }, { status: 404 })
    }

    // Remove the task
    userTasks.splice(taskIndex, 1)
    tasks[session.user.id] = userTasks
    
    return NextResponse.json({
      success: true,
      message: 'Task deleted'
    })
  } catch (error) {
    console.error('Error deleting task:', error)
    return NextResponse.json(
      { error: 'Failed to delete task' },
      { status: 500 }
    )
  }
}