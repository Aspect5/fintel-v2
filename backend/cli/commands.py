from datetime import datetime
from backend.services.task_manager import TaskManager
from backend.models.task import Priority, Status

class TaskCLI:
    def __init__(self):
        self.task_manager = TaskManager()
    
    def add_task(self, title, description="", priority="medium", due_date=None):
        try:
            priority_enum = Priority(priority.lower())
            due_date_obj = None
            if due_date:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            
            task = self.task_manager.add_task(title, description, priority_enum, due_date_obj)
            print(f"Task added: {task.title} (ID: {task.id})")
            return task
        except Exception as e:
            print(f"Error adding task: {e}")
    
    def list_tasks(self, status=None, priority=None):
        tasks = self.task_manager.get_all_tasks()
        
        if status:
            status_enum = Status(status.lower())
            tasks = [t for t in tasks if t.status == status_enum]
        
        if priority:
            priority_enum = Priority(priority.lower())
            tasks = [t for t in tasks if t.priority == priority_enum]
        
        if not tasks:
            print("No tasks found.")
            return
        
        for task in tasks:
            status_str = task.status.value.upper()
            priority_str = task.priority.value.upper()
            overdue_str = " (OVERDUE)" if task.is_overdue else ""
            print(f"[{task.id[:8]}] {task.title} - {status_str} - {priority_str}{overdue_str}")
    
    def update_status(self, task_id, status):
        task = self.task_manager.get_task_by_id(task_id)
        if not task:
            print("Task not found.")
            return
        
        if status.lower() == "in_progress":
            task.mark_in_progress()
        elif status.lower() == "completed":
            task.mark_completed()
        else:
            task.status = Status(status.lower())
        
        print(f"Task status updated to {status}")
    
    def delete_task(self, task_id):
        if self.task_manager.delete_task(task_id):
            print("Task deleted successfully.")
        else:
            print("Task not found.")
