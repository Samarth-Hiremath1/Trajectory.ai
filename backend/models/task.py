"""
Task data model for career development tasks and to-do items.
Supports both roadmap-generated tasks and manually created tasks.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(str, Enum):
    """Types of career development tasks"""
    MILESTONE = "milestone"
    LEARNING = "learning"
    PRACTICE = "practice"
    SKILL = "skill"
    MANUAL = "manual"


class Task(BaseModel):
    """
    Task model for career development activities.
    Can be generated from roadmaps or created manually by users.
    """
    id: Optional[str] = None
    user_id: str
    roadmap_id: Optional[str] = None  # None for manually created tasks
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.MANUAL
    
    # Roadmap-specific fields
    phase_number: Optional[int] = None
    milestone_index: Optional[int] = None
    skill_name: Optional[str] = None
    
    # Scheduling and tracking
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0, le=1000)
    actual_hours: Optional[int] = Field(None, ge=0, le=1000)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskCreate(BaseModel):
    """Model for creating new tasks"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.MANUAL
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0, le=1000)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class TaskUpdate(BaseModel):
    """Model for updating existing tasks"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0, le=1000)
    actual_hours: Optional[int] = Field(None, ge=0, le=1000)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class TaskResponse(BaseModel):
    """Response model for task operations"""
    success: bool
    message: str
    task: Optional[Task] = None
    tasks: Optional[List[Task]] = None


class TaskFilter(BaseModel):
    """Model for filtering tasks"""
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    task_type: Optional[TaskType] = None
    roadmap_id: Optional[str] = None
    has_due_date: Optional[bool] = None
    is_overdue: Optional[bool] = None
    tags: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True


class TaskStats(BaseModel):
    """Statistics about user's tasks"""
    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    high_priority_tasks: int = 0
    roadmap_generated_tasks: int = 0
    manual_tasks: int = 0
    completion_rate: float = 0.0
    average_completion_time_hours: Optional[float] = None