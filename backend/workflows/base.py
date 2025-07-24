# backend/workflows/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    success: bool
    result: str
    trace: Any  # Can be string or dict
    agent_invocations: List[Dict[str, Any]]
    execution_time: float
    workflow_name: str
    error: Optional[str] = None
    workflow_status: Optional[Dict[str, Any]] = None  # Add this field

class BaseWorkflow(ABC):
    """Base class for all workflows"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute the workflow"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get workflow information"""
        return {
            "name": self.name,
            "description": self.description
        }