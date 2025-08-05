# backend/utils/monitoring.py
"""
Comprehensive monitoring and observability utilities for workflow execution
Combines resource monitoring with event-based observability
"""

import time
import logging
import psutil
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import controlflow as cf
from controlflow.orchestration.handler import Handler
from controlflow.events.events import AgentToolCall, AgentMessage, ToolResult
from controlflow.events.task_events import TaskStart, TaskSuccess, TaskFailure

logger = logging.getLogger(__name__)

@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution"""
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    success: bool = False
    error: Optional[str] = None
    execution_time: float = 0.0
    
    @property
    def duration(self) -> float:
        """Calculate execution duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

class FintelEventHandler(Handler):
    """Custom event handler for structured observability"""
    
    def __init__(self):
        super().__init__()
        self.events: List[Dict[str, Any]] = []
    
    def on_task_start(self, event: TaskStart):
        """Log task start events"""
        log_data = {
            "event_type": "task_start",
            "task_id": str(event.task.id),
            "task_objective": event.task.objective,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(f"TASK START: {json.dumps(log_data, indent=2)}")
        self.events.append(log_data)
        
    def on_task_success(self, event: TaskSuccess):
        """Log successful task completion"""
        result_str = str(event.task.result)
        log_data = {
            "event_type": "task_success",
            "task_id": str(event.task.id),
            "result": result_str[:250] + "..." if len(result_str) > 250 else result_str,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"TASK SUCCESS: {json.dumps(log_data, indent=2)}")
        self.events.append(log_data)

    def on_task_failure(self, event: TaskFailure):
        """Log task failures"""
        log_data = {
            "event_type": "task_failure",
            "task_id": str(event.task.id),
            "error": str(event.reason),
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"TASK FAILURE: {json.dumps(log_data, indent=2)}")
        self.events.append(log_data)
        
    def on_agent_message(self, event: AgentMessage):
        """Log raw agent messages to see their reasoning and tool calls"""
        log_data = {
            "event_type": "agent_message",
            "agent_name": event.agent.name,
            "message_content": event.message.get('content'),
            "tool_calls": event.message.get('tool_calls'),
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"AGENT MESSAGE: {json.dumps(log_data, indent=2)}")
        self.events.append(log_data)
        
    def on_agent_tool_call(self, event: AgentToolCall):
        """Log agent tool calls"""
        tool_call_data = event.tool_call or {}
        
        # Extract parameters from the tool call
        tool_input = {}
        if isinstance(tool_call_data, dict):
            tool_input = tool_call_data.get('args', tool_call_data.get('input', {}))
        elif hasattr(tool_call_data, 'args'):
            tool_input = tool_call_data.args
        elif hasattr(tool_call_data, 'input'):
            tool_input = tool_call_data.input
        
        log_data = {
            "event_type": "agent_tool_call",
            "agent_name": event.agent.name,
            "tool_name": tool_call_data.get('name', 'unknown_tool') if isinstance(tool_call_data, dict) else getattr(tool_call_data, 'name', 'unknown_tool'),
            "tool_input": tool_input,
            "tool_output": None,  # Will be filled by tool_result event
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"AGENT TOOL CALL: {json.dumps(log_data, indent=2)}")
        self.events.append(log_data)

    def on_tool_result(self, event: ToolResult):
        """Log tool execution results with robust attribute checking and retry tracking"""
        tool_name = "unknown_tool"
        result_str = "No result"
        is_error = False
        retry_info = None

        if hasattr(event, 'tool_result'):
            tool_result_obj = event.tool_result
            is_error = getattr(tool_result_obj, 'is_error', False)
            result_str = getattr(tool_result_obj, 'str_result', str(getattr(tool_result_obj, 'result', '')))

            # Attempt to find the tool name from multiple possible locations
            if hasattr(tool_result_obj, 'tool') and tool_result_obj.tool and hasattr(tool_result_obj.tool, 'name'):
                tool_name = tool_result_obj.tool.name
            elif hasattr(tool_result_obj, 'tool_call'):
                tool_call_obj = tool_result_obj.tool_call
                if isinstance(tool_call_obj, dict):
                    tool_name = tool_call_obj.get('name', 'unknown_tool')
                else:
                    tool_name = getattr(tool_call_obj, 'name', 'unknown_tool')
            
            # Extract retry information for financial data processing tool
            if tool_name == "process_financial_data":
                try:
                    result_obj = json.loads(result_str) if isinstance(result_str, str) else result_str
                    if isinstance(result_obj, dict) and "retry_info" in result_obj:
                        retry_info = result_obj["retry_info"]
                except:
                    pass
        
        log_data = {
            "event_type": "tool_result", 
            "tool_name": tool_name,
            "result": result_str[:250] + "..." if len(result_str) > 250 else result_str,
            "is_error": is_error,
            "retry_info": retry_info,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(f"TOOL RESULT: {json.dumps(log_data, indent=2)}")
        self.events.append(log_data)

class WorkflowMonitor:
    """Comprehensive monitor for workflow execution, resource usage, and observability"""
    
    def __init__(self):
        self.metrics: Dict[str, WorkflowMetrics] = {}
        self.event_handler = FintelEventHandler()
        self.max_memory_mb = 1024  # 1GB limit
        self.max_cpu_percent = 80
        self.max_execution_time = 60  # 60 seconds
    
    def start_workflow(self, workflow_id: str) -> WorkflowMetrics:
        """Start monitoring a workflow"""
        process = psutil.Process()
        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            start_time=time.time(),
            memory_usage_mb=process.memory_info().rss / 1024 / 1024,
            cpu_usage_percent=process.cpu_percent()
        )
        self.metrics[workflow_id] = metrics
        logger.info(f"Started monitoring workflow {workflow_id}")
        return metrics
    
    def end_workflow(self, workflow_id: str, success: bool, error: str = None):
        """End monitoring a workflow"""
        if workflow_id in self.metrics:
            process = psutil.Process()
            metrics = self.metrics[workflow_id]
            metrics.end_time = time.time()
            metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            metrics.cpu_usage_percent = process.cpu_percent()
            metrics.success = success
            metrics.error = error
            metrics.execution_time = metrics.duration
            
            # Log metrics
            logger.info(f"Workflow {workflow_id} completed: "
                       f"duration={metrics.duration:.2f}s, "
                       f"memory={metrics.memory_usage_mb:.1f}MB, "
                       f"cpu={metrics.cpu_usage_percent:.1f}%, "
                       f"success={success}")
            
            # Check for resource violations
            if metrics.memory_usage_mb > self.max_memory_mb:
                logger.warning(f"Workflow {workflow_id} exceeded memory limit: {metrics.memory_usage_mb:.1f}MB")
            
            if metrics.cpu_usage_percent > self.max_cpu_percent:
                logger.warning(f"Workflow {workflow_id} exceeded CPU limit: {metrics.cpu_usage_percent:.1f}%")
            
            if metrics.duration > self.max_execution_time:
                logger.warning(f"Workflow {workflow_id} exceeded time limit: {metrics.duration:.2f}s")
    
    def check_resources(self) -> Dict[str, float]:
        """Check current resource usage"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        return {
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
            'memory_limit_exceeded': memory_mb > self.max_memory_mb,
            'cpu_limit_exceeded': cpu_percent > self.max_cpu_percent
        }
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """Get metrics for a specific workflow"""
        return self.metrics.get(workflow_id)
    
    def get_all_metrics(self) -> Dict[str, WorkflowMetrics]:
        """Get all workflow metrics"""
        return self.metrics.copy()
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all captured events"""
        return self.event_handler.events.copy()
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events filtered by type"""
        return [event for event in self.event_handler.events if event.get('event_type') == event_type]
    
    def get_tool_usage_summary(self) -> Dict[str, int]:
        """Get summary of tool usage"""
        tool_calls = self.get_events_by_type('agent_tool_call')
        tool_usage = {}
        for event in tool_calls:
            tool_name = event.get('tool_name', 'unknown')
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        return tool_usage
    
    def cleanup_old_metrics(self, max_age_hours: int = 24):
        """Clean up old metrics and events"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Clean up old workflow metrics
        old_workflows = [
            workflow_id for workflow_id, metrics in self.metrics.items()
            if metrics.start_time < cutoff_time
        ]
        
        for workflow_id in old_workflows:
            del self.metrics[workflow_id]
        
        # Clean up old events
        self.event_handler.events = [
            event for event in self.event_handler.events
            if datetime.fromisoformat(event.get('timestamp', '1970-01-01')).timestamp() > cutoff_time
        ]
        
        if old_workflows:
            logger.info(f"Cleaned up {len(old_workflows)} old workflow metrics and events")

# Global monitor instance
workflow_monitor = WorkflowMonitor() 