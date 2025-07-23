from typing import List, Optional
from datetime import datetime
from backend.models.task import Task, Priority, Status

class TaskManager:
    def __init__(self):
        self.tasks = []
    
    def add_task(self, title, description="", priority=Priority.MEDIUM, due_date=None):
        task = Task(title, description, priority, due_date)
        self.tasks.append(task)
        return task
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Task]:
        return self.tasks.copy()
    
    def update_task(self, task_id: str, title=None, description=None, priority=None, due_date=None) -> bool:
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if due_date is not None:
            task.due_date = due_date
        
        task.updated_at = datetime.now()
        return True
    
    def delete_task(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if task:
            self.tasks.remove(task)
            return True
        return False
    
    def get_tasks_by_status(self, status: Status) -> List[Task]:
        return [task for task in self.tasks if task.status == status]
    
    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        return [task for task in self.tasks if task.priority == priority]
    
    def get_overdue_tasks(self) -> List[Task]:
        return [task for task in self.tasks if task.is_overdue]
