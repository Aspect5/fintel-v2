from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str, rate_limit: int = 60):
        self.name = name
        self.description = description
        self.rate_limit = rate_limit
        self._last_call = None
        self._call_count = 0
    
    def can_execute(self) -> bool:
        """Check if tool can execute (rate limiting)"""
        if not self._last_call:
            return True
        
        time_diff = datetime.now() - self._last_call
        if time_diff > timedelta(minutes=1):
            self._call_count = 0
            return True
        
        return self._call_count < self.rate_limit
    
    def record_execution(self):
        """Record tool execution for rate limiting"""
        self._last_call = datetime.now()
        self._call_count += 1
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get tool status"""
        return {
            'name': self.name,
            'description': self.description,
            'available': self.can_execute(),
            'rate_limit': self.rate_limit,
            'calls_remaining': max(0, self.rate_limit - self._call_count)
        }