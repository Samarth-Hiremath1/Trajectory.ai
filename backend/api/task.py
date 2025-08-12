"""
FastAPI endpoints for task management.
Provides CRUD operations and task analytics for career development tasks.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta

from backend.models.task import (
    Task, TaskCreate, TaskUpdate, TaskFilter, TaskStats, TaskResponse,
    TaskStatus, TaskPriority, TaskType
)
from backend.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
task_service = TaskService()


@router.post("/", response_model=TaskResponse)
async def create_task(user_id: str, task_data: TaskCreate):
    """Create a new task for the user"""
    try:
        task = await task_service.create_task(user_id, task_data)
        return TaskResponse(
            success=True,
            message="Task created successfully",
            task=task
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/", response_model=TaskResponse)
async def get_user_tasks(
    user_id: str,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    task_type: Optional[TaskType] = None,
    roadmap_id: Optional[str] = None,
    has_due_date: Optional[bool] = None,
    is_overdue: Optional[bool] = None,
    tags: Optional[List[str]] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get tasks for a user with optional filtering"""
    try:
        task_filter = TaskFilter(
            status=status,
            priority=priority,
            task_type=task_type,
            roadmap_id=roadmap_id,
            has_due_date=has_due_date,
            is_overdue=is_overdue,
            tags=tags
        )
        
        tasks = await task_service.get_user_tasks(user_id, task_filter, limit, offset)
        return TaskResponse(
            success=True,
            message=f"Retrieved {len(tasks)} tasks",
            tasks=tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user_id: str):
    """Get a specific task by ID"""
    try:
        task = await task_service.get_task_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            success=True,
            message="Task retrieved successfully",
            task=task
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, user_id: str, updates: TaskUpdate):
    """Update an existing task"""
    try:
        task = await task_service.update_task(task_id, user_id, updates)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            success=True,
            message="Task updated successfully",
            task=task
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(task_id: str, user_id: str):
    """Delete a task"""
    try:
        success = await task_service.delete_task(task_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            success=True,
            message="Task deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, user_id: str, actual_hours: Optional[int] = None):
    """Mark a task as completed"""
    try:
        task = await task_service.complete_task(task_id, user_id, actual_hours)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            success=True,
            message="Task completed successfully",
            task=task
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")


@router.get("/stats/summary")
async def get_task_stats(user_id: str) -> TaskStats:
    """Get task statistics for a user"""
    try:
        return await task_service.get_task_stats(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task stats: {str(e)}")


@router.post("/generate/roadmap/{roadmap_id}", response_model=TaskResponse)
async def generate_tasks_from_roadmap(roadmap_id: str, user_id: str):
    """Generate tasks from a roadmap's phases and milestones"""
    try:
        tasks = await task_service.generate_tasks_from_roadmap(roadmap_id, user_id)
        return TaskResponse(
            success=True,
            message=f"Generated {len(tasks)} tasks from roadmap",
            tasks=tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tasks from roadmap: {str(e)}")


@router.get("/overdue/count")
async def get_overdue_count(user_id: str) -> dict:
    """Get count of overdue tasks for a user"""
    try:
        task_filter = TaskFilter(is_overdue=True)
        tasks = await task_service.get_user_tasks(user_id, task_filter)
        return {"overdue_count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overdue count: {str(e)}")


@router.get("/upcoming/week")
async def get_upcoming_tasks(user_id: str) -> TaskResponse:
    """Get tasks due in the next week"""
    try:
        # Get all tasks with due dates
        task_filter = TaskFilter(has_due_date=True, status=TaskStatus.PENDING)
        all_tasks = await task_service.get_user_tasks(user_id, task_filter)
        
        # Filter for tasks due in the next 7 days
        now = datetime.utcnow()
        week_from_now = now + timedelta(days=7)
        
        upcoming_tasks = [
            task for task in all_tasks 
            if task.due_date and now <= task.due_date <= week_from_now
        ]
        
        return TaskResponse(
            success=True,
            message=f"Found {len(upcoming_tasks)} tasks due in the next week",
            tasks=upcoming_tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get upcoming tasks: {str(e)}")


@router.post("/bulk/update", response_model=TaskResponse)
async def bulk_update_tasks(user_id: str, task_ids: List[str], updates: TaskUpdate):
    """Update multiple tasks at once"""
    try:
        updated_tasks = []
        for task_id in task_ids:
            task = await task_service.update_task(task_id, user_id, updates)
            if task:
                updated_tasks.append(task)
        
        return TaskResponse(
            success=True,
            message=f"Updated {len(updated_tasks)} tasks",
            tasks=updated_tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update tasks: {str(e)}")


@router.post("/bulk/complete", response_model=TaskResponse)
async def bulk_complete_tasks(user_id: str, task_ids: List[str]):
    """Mark multiple tasks as completed"""
    try:
        completed_tasks = []
        for task_id in task_ids:
            task = await task_service.complete_task(task_id, user_id)
            if task:
                completed_tasks.append(task)
        
        return TaskResponse(
            success=True,
            message=f"Completed {len(completed_tasks)} tasks",
            tasks=completed_tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk complete tasks: {str(e)}")