#!/usr/bin/env python3
"""
Test script for the task management system.
This script tests the basic functionality of the task service.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from services.task_service import TaskService
from models.task import TaskCreate, TaskUpdate, TaskStatus, TaskPriority, TaskType

async def test_task_system():
    """Test the task management system"""
    
    print("🧪 Testing Task Management System")
    print("=" * 40)
    
    try:
        # Initialize task service
        task_service = TaskService()
        test_user_id = "test-user-123"
        
        print("1. Testing task creation...")
        
        # Create a test task
        task_data = TaskCreate(
            title="Test Task",
            description="This is a test task for the task management system",
            priority=TaskPriority.HIGH,
            task_type=TaskType.MANUAL,
            due_date=datetime.utcnow() + timedelta(days=7),
            estimated_hours=2,
            tags=["test", "manual"],
            metadata={"test": True}
        )
        
        created_task = await task_service.create_task(test_user_id, task_data)
        print(f"✅ Created task: {created_task.id} - {created_task.title}")
        
        print("\n2. Testing task retrieval...")
        
        # Get user tasks
        user_tasks = await task_service.get_user_tasks(test_user_id)
        print(f"✅ Retrieved {len(user_tasks)} tasks for user")
        
        # Get specific task
        retrieved_task = await task_service.get_task_by_id(created_task.id, test_user_id)
        if retrieved_task:
            print(f"✅ Retrieved specific task: {retrieved_task.title}")
        else:
            print("❌ Failed to retrieve specific task")
            return False
        
        print("\n3. Testing task update...")
        
        # Update the task
        updates = TaskUpdate(
            description="Updated description",
            status=TaskStatus.IN_PROGRESS
        )
        
        updated_task = await task_service.update_task(created_task.id, test_user_id, updates)
        if updated_task and updated_task.status == TaskStatus.IN_PROGRESS:
            print(f"✅ Updated task status to: {updated_task.status}")
        else:
            print("❌ Failed to update task")
            return False
        
        print("\n4. Testing task completion...")
        
        # Complete the task
        completed_task = await task_service.complete_task(created_task.id, test_user_id, actual_hours=1)
        if completed_task and completed_task.status == TaskStatus.COMPLETED:
            print(f"✅ Completed task with {completed_task.actual_hours} hours")
        else:
            print("❌ Failed to complete task")
            return False
        
        print("\n5. Testing task statistics...")
        
        # Get task statistics
        stats = await task_service.get_task_stats(test_user_id)
        print(f"✅ Task statistics:")
        print(f"   Total tasks: {stats.total_tasks}")
        print(f"   Completed tasks: {stats.completed_tasks}")
        print(f"   Completion rate: {stats.completion_rate}%")
        
        print("\n6. Testing task deletion...")
        
        # Delete the task
        deleted = await task_service.delete_task(created_task.id, test_user_id)
        if deleted:
            print("✅ Successfully deleted test task")
        else:
            print("❌ Failed to delete task")
            return False
        
        print("\n🎉 All task system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_roadmap_task_generation():
    """Test generating tasks from roadmaps"""
    
    print("\n🧪 Testing Roadmap Task Generation")
    print("=" * 40)
    
    try:
        task_service = TaskService()
        test_user_id = "test-user-123"
        
        # This would require an existing roadmap
        # For now, just test that the method exists and handles missing roadmaps gracefully
        tasks = await task_service.generate_tasks_from_roadmap("non-existent-roadmap", test_user_id)
        print(f"✅ Roadmap task generation handled gracefully (returned {len(tasks)} tasks)")
        
        return True
        
    except Exception as e:
        print(f"❌ Roadmap task generation test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Task System Test Runner")
    print("=" * 40)
    
    # Check if tasks table exists first
    try:
        from services.database_service import DatabaseService
        db = DatabaseService()
        result = db.supabase.table('tasks').select('count', count='exact').limit(1).execute()
        print(f"✅ Tasks table exists with {result.count} tasks")
    except Exception as e:
        print(f"❌ Tasks table does not exist: {e}")
        print("Please run the migration first: python run_tasks_migration.py")
        sys.exit(1)
    
    # Run tests
    async def run_all_tests():
        success1 = await test_task_system()
        success2 = await test_roadmap_task_generation()
        return success1 and success2
    
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ All tests passed!")
        print("🎉 Task management system is working correctly!")
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)