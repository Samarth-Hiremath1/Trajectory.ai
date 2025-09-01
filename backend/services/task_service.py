"""
Task management service for career development tasks.
Handles CRUD operations, roadmap integration, and task analytics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import logging
from services.database_service import DatabaseService
from models.task import (
    Task, TaskCreate, TaskUpdate, TaskFilter, TaskStats,
    TaskStatus, TaskPriority, TaskType
)

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing career development tasks"""
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    async def create_task(self, user_id: str, task_data: TaskCreate) -> Task:
        """Create a new task for the user"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            # Prepare task data for database
            db_data = {
                "user_id": converted_user_id,
                "title": task_data.title,
                "description": task_data.description,
                "status": task_data.status.value if hasattr(task_data.status, 'value') else str(task_data.status),
                "priority": task_data.priority.value if hasattr(task_data.priority, 'value') else str(task_data.priority),
                "task_type": task_data.task_type.value if hasattr(task_data.task_type, 'value') else str(task_data.task_type),
                "due_date": task_data.due_date.isoformat() if task_data.due_date else None,
                "estimated_hours": task_data.estimated_hours,
                "tags": task_data.tags or [],
                "metadata": task_data.metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db_service.supabase.table("tasks").insert(db_data).execute()
            
            if result.data:
                task_data = result.data[0]
                logger.info(f"Created task {task_data['id']} for user {user_id}")
                return self._convert_db_to_task(task_data)
            
            raise Exception("No data returned from task creation")
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise
    
    async def get_user_tasks(
        self, 
        user_id: str, 
        task_filter: Optional[TaskFilter] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """Get tasks for a user with optional filtering"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            # Start with base query
            query = self.db_service.supabase.table("tasks").select("*").eq("user_id", converted_user_id)
            
            # Apply filters
            if task_filter:
                if task_filter.status:
                    query = query.eq("status", task_filter.status.value if hasattr(task_filter.status, 'value') else task_filter.status)
                
                if task_filter.priority:
                    query = query.eq("priority", task_filter.priority.value if hasattr(task_filter.priority, 'value') else task_filter.priority)
                
                if task_filter.task_type:
                    query = query.eq("task_type", task_filter.task_type.value if hasattr(task_filter.task_type, 'value') else task_filter.task_type)
                
                if task_filter.roadmap_id:
                    query = query.eq("roadmap_id", task_filter.roadmap_id)
                
                if task_filter.has_due_date is not None:
                    if task_filter.has_due_date:
                        query = query.not_.is_("due_date", "null")
                    else:
                        query = query.is_("due_date", "null")
                
                if task_filter.is_overdue:
                    # For overdue tasks, we need to filter on the client side since Supabase
                    # doesn't support complex date comparisons in the query builder
                    pass  # Will handle this after fetching
            
            # Apply ordering
            query = query.order("created_at", desc=True)
            
            # Apply pagination
            if limit:
                query = query.limit(limit)
            if offset > 0:
                query = query.range(offset, offset + (limit or 1000) - 1)
            
            result = query.execute()
            
            tasks = []
            if result.data:
                for task_data in result.data:
                    task = self._convert_db_to_task(task_data)
                    if task:
                        # Apply overdue filter if needed
                        if task_filter and task_filter.is_overdue:
                            if self._is_task_overdue(task):
                                tasks.append(task)
                        else:
                            tasks.append(task)
            
            # Sort tasks by priority and due date
            tasks.sort(key=lambda t: (
                {'high': 0, 'medium': 1, 'low': 2}.get(t.priority.value, 3),
                t.due_date or datetime.max,
                t.created_at
            ))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting user tasks: {str(e)}")
            raise
    
    async def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get a specific task by ID (with user ownership check)"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            result = self.db_service.supabase.table("tasks").select("*").eq("id", task_id).eq("user_id", converted_user_id).execute()
            
            if result.data:
                return self._convert_db_to_task(result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            raise
    
    async def update_task(self, task_id: str, user_id: str, updates: TaskUpdate) -> Optional[Task]:
        """Update an existing task"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            # Build update data
            update_data = {}
            updates_dict = updates.model_dump(exclude_unset=True)
            
            for field, value in updates_dict.items():
                if value is not None:
                    # Handle enum values
                    if hasattr(value, 'value'):
                        update_data[field] = value.value
                    elif field == 'due_date' and isinstance(value, datetime):
                        update_data[field] = value.isoformat()
                    else:
                        update_data[field] = value
            
            # Always update the updated_at timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.db_service.supabase.table("tasks").update(update_data).eq("id", task_id).eq("user_id", converted_user_id).execute()
            
            if result.data:
                logger.info(f"Updated task {task_id}")
                return self._convert_db_to_task(result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            raise
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            result = self.db_service.supabase.table("tasks").delete().eq("id", task_id).eq("user_id", converted_user_id).execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"Deleted task {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {str(e)}")
            raise
    
    async def complete_task(self, task_id: str, user_id: str, actual_hours: Optional[int] = None) -> Optional[Task]:
        """Mark a task as completed"""
        updates = TaskUpdate(
            status=TaskStatus.COMPLETED,
            actual_hours=actual_hours
        )
        return await self.update_task(task_id, user_id, updates)
    
    async def get_task_stats(self, user_id: str) -> TaskStats:
        """Get task statistics for a user"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            # Get all tasks for the user
            result = self.db_service.supabase.table("tasks").select("*").eq("user_id", converted_user_id).execute()
            
            tasks = []
            if result.data:
                tasks = [self._convert_db_to_task(task_data) for task_data in result.data]
                tasks = [task for task in tasks if task]  # Filter out None values
            
            # Calculate statistics
            total_tasks = len(tasks)
            pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
            in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            overdue_tasks = len([t for t in tasks if self._is_task_overdue(t)])
            high_priority_tasks = len([t for t in tasks if t.priority == TaskPriority.HIGH and t.status != TaskStatus.COMPLETED])
            roadmap_generated_tasks = len([t for t in tasks if t.roadmap_id])
            manual_tasks = len([t for t in tasks if not t.roadmap_id])
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            
            # Calculate average completion time
            completed_with_hours = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.actual_hours]
            avg_completion_time = sum(t.actual_hours for t in completed_with_hours) / len(completed_with_hours) if completed_with_hours else None
            
            return TaskStats(
                total_tasks=total_tasks,
                pending_tasks=pending_tasks,
                in_progress_tasks=in_progress_tasks,
                completed_tasks=completed_tasks,
                overdue_tasks=overdue_tasks,
                high_priority_tasks=high_priority_tasks,
                roadmap_generated_tasks=roadmap_generated_tasks,
                manual_tasks=manual_tasks,
                completion_rate=round(completion_rate, 2),
                average_completion_time_hours=avg_completion_time
            )
            
        except Exception as e:
            logger.error(f"Error getting task stats for user {user_id}: {str(e)}")
            raise
    
    async def generate_tasks_from_roadmap(self, roadmap_id: str, user_id: str) -> List[Task]:
        """Generate tasks from a roadmap's phases and milestones"""
        try:
            # First, get the roadmap data
            roadmap = await self.db_service.load_roadmap(roadmap_id)
            if not roadmap or roadmap.user_id != self.db_service._convert_user_id_to_uuid(user_id):
                return []
            
            generated_tasks = []
            
            for phase_idx, phase in enumerate(roadmap.phases):
                phase_number = phase.phase_number
                
                # Generate milestone tasks
                for milestone_idx, milestone in enumerate(phase.milestones):
                    if not milestone.is_completed:
                        # Calculate due date based on estimated weeks
                        due_date = None
                        if milestone.estimated_completion_weeks:
                            due_date = datetime.utcnow() + timedelta(weeks=milestone.estimated_completion_weeks)
                        
                        task_data = TaskCreate(
                            title=milestone.title or f'Complete milestone {milestone_idx + 1}',
                            description=milestone.description,
                            priority=TaskPriority.HIGH if phase_number == (roadmap.current_phase or 1) else TaskPriority.MEDIUM,
                            task_type=TaskType.MILESTONE,
                            due_date=due_date,
                            tags=[
                                roadmap.target_role,
                                f"Phase {phase_number}",
                                "Milestone"
                            ],
                            metadata={
                                'roadmap_id': roadmap_id,
                                'phase_number': phase_number,
                                'milestone_index': milestone_idx,
                                'estimated_weeks': milestone.estimated_completion_weeks
                            }
                        )
                        
                        # Create the task with roadmap association
                        task = await self._create_roadmap_task(
                            user_id, task_data, roadmap_id, phase_number, milestone_idx
                        )
                        generated_tasks.append(task)
                
                # Generate skill development tasks
                for skill in phase.skills_to_develop:
                    if skill.current_level != skill.target_level:
                        task_data = TaskCreate(
                            title=f"Develop {skill.name} skill",
                            description=f"Progress from {skill.current_level} to {skill.target_level} level",
                            priority=self._skill_priority_to_task_priority(skill.priority),
                            task_type=TaskType.SKILL,
                            estimated_hours=skill.estimated_hours,
                            tags=[
                                roadmap.target_role,
                                skill.name,
                                f"Phase {phase_number}"
                            ],
                            metadata={
                                'roadmap_id': roadmap_id,
                                'phase_number': phase_number,
                                'skill_name': skill.name,
                                'current_level': skill.current_level,
                                'target_level': skill.target_level
                            }
                        )
                        
                        task = await self._create_roadmap_task(
                            user_id, task_data, roadmap_id, phase_number, skill_name=skill.name
                        )
                        generated_tasks.append(task)
                
                # Generate learning resource tasks
                for resource in phase.learning_resources:
                    task_data = TaskCreate(
                        title=f"Complete: {resource.title}",
                        description=resource.description,
                        priority=TaskPriority.MEDIUM,
                        task_type=TaskType.LEARNING,
                        tags=[
                            roadmap.target_role,
                            resource.resource_type,
                            f"Phase {phase_number}"
                        ],
                        metadata={
                            'roadmap_id': roadmap_id,
                            'phase_number': phase_number,
                            'resource_url': resource.url,
                            'resource_type': resource.resource_type
                        }
                    )
                    
                    task = await self._create_roadmap_task(
                        user_id, task_data, roadmap_id, phase_number
                    )
                    generated_tasks.append(task)
            
            return generated_tasks
            
        except Exception as e:
            logger.error(f"Error generating tasks from roadmap {roadmap_id}: {str(e)}")
            raise
    
    async def _create_roadmap_task(
        self, 
        user_id: str, 
        task_data: TaskCreate, 
        roadmap_id: str,
        phase_number: int,
        milestone_index: Optional[int] = None,
        skill_name: Optional[str] = None
    ) -> Task:
        """Create a task associated with a roadmap"""
        try:
            # Convert user_id to UUID format if needed
            converted_user_id = self.db_service._convert_user_id_to_uuid(user_id)
            
            # Prepare task data for database
            db_data = {
                "user_id": converted_user_id,
                "roadmap_id": roadmap_id,
                "title": task_data.title,
                "description": task_data.description,
                "status": task_data.status.value if hasattr(task_data.status, 'value') else str(task_data.status),
                "priority": task_data.priority.value if hasattr(task_data.priority, 'value') else str(task_data.priority),
                "task_type": task_data.task_type.value if hasattr(task_data.task_type, 'value') else str(task_data.task_type),
                "phase_number": phase_number,
                "milestone_index": milestone_index,
                "skill_name": skill_name,
                "due_date": task_data.due_date.isoformat() if task_data.due_date else None,
                "estimated_hours": task_data.estimated_hours,
                "tags": task_data.tags or [],
                "metadata": task_data.metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db_service.supabase.table("tasks").insert(db_data).execute()
            
            if result.data:
                task_data = result.data[0]
                logger.info(f"Created roadmap task {task_data['id']} for user {user_id}")
                return self._convert_db_to_task(task_data)
            
            raise Exception("No data returned from roadmap task creation")
            
        except Exception as e:
            logger.error(f"Error creating roadmap task: {str(e)}")
            raise
    
    def _skill_priority_to_task_priority(self, skill_priority: int) -> TaskPriority:
        """Convert skill priority (1-5) to task priority"""
        if skill_priority <= 2:
            return TaskPriority.HIGH
        elif skill_priority <= 3:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def _is_task_overdue(self, task: Task) -> bool:
        """Check if a task is overdue"""
        return (
            task.status != TaskStatus.COMPLETED and 
            task.due_date and 
            task.due_date < datetime.utcnow()
        )
    
    def _convert_db_to_task(self, data: Dict[str, Any]) -> Optional[Task]:
        """Convert database row to Task model"""
        try:
            if not data:
                return None
            
            # Parse due_date if it exists
            due_date = None
            if data.get('due_date'):
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            
            # Parse timestamps
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            
            completed_at = None
            if data.get('completed_at'):
                completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
            
            return Task(
                id=str(data['id']),
                user_id=data['user_id'],
                roadmap_id=str(data['roadmap_id']) if data.get('roadmap_id') else None,
                title=data['title'],
                description=data.get('description'),
                status=TaskStatus(data['status']),
                priority=TaskPriority(data['priority']),
                task_type=TaskType(data['task_type']),
                phase_number=data.get('phase_number'),
                milestone_index=data.get('milestone_index'),
                skill_name=data.get('skill_name'),
                due_date=due_date,
                estimated_hours=data.get('estimated_hours'),
                actual_hours=data.get('actual_hours'),
                tags=data.get('tags', []),
                metadata=data.get('metadata', {}),
                created_at=created_at,
                updated_at=updated_at,
                completed_at=completed_at
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to task: {str(e)}")
            return None