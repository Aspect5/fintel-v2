import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from backend.cli.commands import TaskCLI
from backend.models.task import Priority, Status

class TestTaskCLI:
    def setup_method(self):
        """Setup for each test method"""
        self.cli = TaskCLI()

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=StringIO)
    def test_list_empty_tasks(self, mock_stdout):
        """Test listing when no tasks exist"""
        self.cli.list_tasks()
        output = mock_stdout.getvalue()
        assert "No tasks found" in output

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_task_command(self, mock_stdout):
        """Test adding task via CLI"""
        self.cli.add_task("Test Task", "Test Description", "high", "2024-12-31")
        
        tasks = self.cli.task_manager.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Test Task"
        assert tasks[0].priority == Priority.HIGH

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=StringIO)
    def test_list_tasks_with_data(self, mock_stdout):
        """Test listing tasks when tasks exist"""
        # Add some test tasks
        self.cli.add_task("Task 1", "Description 1", "high")
        self.cli.add_task("Task 2", "Description 2", "low")
        
        self.cli.list_tasks()
        output = mock_stdout.getvalue()
        
        assert "Task 1" in output
        assert "Task 2" in output
        assert "HIGH" in output
        assert "LOW" in output

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=StringIO)
    def test_update_task_status(self, mock_stdout):
        """Test updating task status"""
        # Add a task first
        self.cli.add_task("Test Task", "Description")
        tasks = self.cli.task_manager.get_all_tasks()
        task_id = tasks[0].id
        
        # Update status
        self.cli.update_status(task_id, "in_progress")
        
        updated_task = self.cli.task_manager.get_task_by_id(task_id)
        assert updated_task.status == Status.IN_PROGRESS

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_task(self, mock_stdout):
        """Test deleting a task"""
        # Add a task first
        self.cli.add_task("Task to Delete", "Description")
        tasks = self.cli.task_manager.get_all_tasks()
        task_id = tasks[0].id
        
        # Delete task
        self.cli.delete_task(task_id)
        
        assert len(self.cli.task_manager.get_all_tasks()) == 0

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=StringIO)
    def test_filter_by_status(self, mock_stdout):
        """Test filtering tasks by status"""
        # Add tasks with different statuses
        task1 = self.cli.task_manager.add_task("Todo Task", "Description")
        task2 = self.cli.task_manager.add_task("Progress Task", "Description")
        task2.mark_in_progress()
        
        # Filter by TODO status
        self.cli.list_tasks(status="todo")
        output = mock_stdout.getvalue()
        
        assert "Todo Task" in output
        assert "Progress Task" not in output

    @pytest.mark.integration
    @patch('sys.stdout', new_callable=StringIO)
    def test_complete_workflow(self, mock_stdout):
        """Test complete CLI workflow"""
        # Add task
        self.cli.add_task("Workflow Task", "Test complete workflow", "high", "2024-12-31")
        
        # List tasks
        self.cli.list_tasks()
        output1 = mock_stdout.getvalue()
        assert "Workflow Task" in output1
        
        # Get task ID
        tasks = self.cli.task_manager.get_all_tasks()
        task_id = tasks[0].id
        
        # Update status
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.cli.update_status(task_id, "completed")
        
        # Verify completion
        completed_tasks = self.cli.task_manager.get_tasks_by_status(Status.COMPLETED)
        assert len(completed_tasks) == 1
        
        # Delete task
        self.cli.delete_task(task_id)
        assert len(self.cli.task_manager.get_all_tasks()) == 0