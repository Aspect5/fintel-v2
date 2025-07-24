# backend/utils/observability.py
import logging
import controlflow as cf
from typing import Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class FintelEventHandler(cf.events.Handler):
    """Custom event handler for structured observability"""
    
    def __init__(self):
        super().__init__()
        self.events = []
    
    def on_task_start(self, event: cf.events.TaskStart):
        """Log task start events"""
        log_data = {
            "event_type": "task_start",
            "task_name": event.task.name if hasattr(event.task, 'name') else 'unnamed_task',
            "task_objective": event.task.objective,
            "timestamp": datetime.now().isoformat(),
            "agents": [agent.name for agent in event.task.agents] if event.task.agents else []
        }
        logger.info(f"Task Started: {json.dumps(log_data)}")
        self.events.append(log_data)
    
    def on_task_success(self, event: cf.events.TaskSuccess):
        """Log successful task completion"""
        log_data = {
            "event_type": "task_success", 
            "task_name": event.task.name if hasattr(event.task, 'name') else 'unnamed_task',
            "result_type": type(event.task.result).__name__,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Task Completed: {json.dumps(log_data)}")
        self.events.append(log_data)
    
    def on_task_failure(self, event: cf.events.TaskFailure):
        """Log task failures"""
        log_data = {
            "event_type": "task_failure",
            "task_name": event.task.name if hasattr(event.task, 'name') else 'unnamed_task', 
            "error": str(event.reason),
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"Task Failed: {json.dumps(log_data)}")
        self.events.append(log_data)
    
    def on_agent_tool_call(self, event: cf.events.AgentToolCall):
        """Log agent tool calls"""
        log_data = {
            "event_type": "agent_tool_call",
            "agent_name": event.agent.name,
            "tool_name": event.tool_call.name if hasattr(event.tool_call, 'name') else 'unknown_tool',
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Tool Called: {json.dumps(log_data)}")
        self.events.append(log_data)

# Usage in workflows
def create_observable_workflow():
    """Create workflow with proper observability"""
    handler = FintelEventHandler()
    
    # Register the handler globally
    cf.events.add_handler(handler)
    
    return handler