import pytest
from datetime import datetime, timedelta
from backend.models.task import Task, Priority, Status
from backend.services.task_manager import TaskManager
from backend.cli.commands import TaskCLI

class TestIntegration:
    @pytest.mark.integration
    def test_end_to_end_task_management(self):
        """Test complete end-to-end task management"""
        cli = TaskCLI()
        
        # Step 1: Add multiple tasks
        cli.add_task("Project Setup", "Initialize new project", "high", "2024-12-25")
        cli.add_task("Write Tests", "Create comprehensive test suite", "medium", "2024-12-30")
        cli.add_task("Documentation", "Write user documentation", "low")
        
        # Step 2: Verify tasks were added
        all_tasks = cli.task_manager.get_all_tasks()
        assert len(all_tasks) == 3
        
        # Step 3: Update task statuses
        project_task = next(t for t in all_tasks if t.title == "Project Setup")
        test_task = next(t for t in all_tasks if t.title == "Write Tests")
        
        cli.update_status(project_task.id, "completed")
        cli.update_status(test_task.id, "in_progress")
        
        # Step 4: Verify status updates
        completed_tasks = cli.task_manager.get_tasks_by_status(Status.COMPLETED)
        in_progress_tasks = cli.task_manager.get_tasks_by_status(Status.IN_PROGRESS)
        
        assert len(completed_tasks) == 1
        assert len(in_progress_tasks) == 1
        assert completed_tasks[0].title == "Project Setup"
        assert in_progress_tasks[0].title == "Write Tests"
        
        # Step 5: Filter by priority
        high_priority_tasks = cli.task_manager.get_tasks_by_priority(Priority.HIGH)
        assert len(high_priority_tasks) == 1
        assert high_priority_tasks[0].title == "Project Setup"
        
        # Step 6: Clean up
        for task in all_tasks:
            cli.delete_task(task.id)
        
        assert len(cli.task_manager.get_all_tasks()) == 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_dataset_performance(self):
        """Test performance with larger dataset"""
        task_manager = TaskManager()
        
        # Add many tasks
        for i in range(100):
            task_manager.add_task(
                title=f"Task {i}",
                description=f"Description for task {i}",
                priority=Priority.MEDIUM if i % 2 == 0 else Priority.LOW
            )
        
        # Test retrieval performance
        all_tasks = task_manager.get_all_tasks()
        assert len(all_tasks) == 100
        
        # Test filtering performance
        medium_tasks = task_manager.get_tasks_by_priority(Priority.MEDIUM)
        low_tasks = task_manager.get_tasks_by_priority(Priority.LOW)
        
        assert len(medium_tasks) == 50
        assert len(low_tasks) == 50
        
        # Test bulk status updates
        for i, task in enumerate(all_tasks[:50]):
            task.mark_completed()
        
        completed_tasks = task_manager.get_tasks_by_status(Status.COMPLETED)
        assert len(completed_tasks) == 50

    @pytest.mark.integration
    def test_data_consistency(self):
        """Test data consistency across operations"""
        task_manager = TaskManager()
        
        # Create task with specific data
        original_task = task_manager.add_task(
            title="Consistency Test",
            description="Testing data consistency",
            priority=Priority.HIGH,
            due_date=datetime.now() + timedelta(days=5)
        )
        
        task_id = original_task.id
        original_created_at = original_task.created_at
        
        # Update task
        task_manager.update_task(
            task_id,
            title="Updated Consistency Test",
            priority=Priority.MEDIUM
        )
        
        # Retrieve and verify
        updated_task = task_manager.get_task_by_id(task_id)
        
        # Check what should change
        assert updated_task.title == "Updated Consistency Test"
        assert updated_task.priority == Priority.MEDIUM
        assert updated_task.updated_at > original_created_at
        
        # Check what should remain the same
        assert updated_task.id == task_id
        assert updated_task.description == "Testing data consistency"
        assert updated_task.created_at == original_created_at
        assert updated_task.status == Status.TODO