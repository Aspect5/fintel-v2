from enum import Enum
from datetime import datetime
import uuid

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Task:
    def __init__(self, title, description="", priority=Priority.MEDIUM, due_date=None):
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        if len(title) > 200:
            raise ValueError("Title cannot be longer than 200 characters")
        
        self.id = str(uuid.uuid4())
        self.title = title.strip()
        self.description = description
        self.priority = priority
        self.status = Status.TODO
        self.due_date = due_date
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.completed_at = None
    
    def mark_in_progress(self):
        self.status = Status.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def mark_completed(self):
        self.status = Status.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    @property
    def is_overdue(self):
        if self.status == Status.COMPLETED or not self.due_date:
            return False
        return datetime.now() > self.due_date
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_overdue": self.is_overdue
        }
