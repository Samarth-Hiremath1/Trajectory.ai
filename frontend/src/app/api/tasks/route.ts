import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth-options'

// Simple in-memory storage for tasks (in production, this would be a database)
const tasks: Record<string, any[]> = {}

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const userTasks = tasks[session.user.id] || []
    
    return NextResponse.json({
      success: true,
      tasks: userTasks
    })
  } catch (error) {
    console.error('Error fetching tasks:', error)
    return NextResponse.json({
      success: false,
      tasks: []
    })
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    
    const newTask = {
      id: Date.now().toString(),
      user_id: session.user.id,
      title: body.title,
      description: body.description || '',
      status: body.status || 'pending',
      priority: body.priority || 'medium',
      task_type: body.task_type || 'manual',
      due_date: body.due_date || null,
      tags: body.tags || [],
      metadata: body.metadata || {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    if (!tasks[session.user.id]) {
      tasks[session.user.id] = []
    }
    
    tasks[session.user.id].push(newTask)
    
    return NextResponse.json({
      success: true,
      task: newTask
    })
  } catch (error) {
    console.error('Error creating task:', error)
    return NextResponse.json(
      { error: 'Failed to create task' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Clear all tasks for the user
    tasks[session.user.id] = []
    
    return NextResponse.json({
      success: true,
      message: 'All tasks cleared'
    })
  } catch (error) {
    console.error('Error clearing tasks:', error)
    return NextResponse.json(
      { error: 'Failed to clear tasks' },
      { status: 500 }
    )
  }
}