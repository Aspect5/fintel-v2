# backend/utils/observability.py
import logging
import controlflow as cf
from typing import Dict, Any
import json
from datetime import datetime
from controlflow.orchestration.handler import Handler
from controlflow.events.events import AgentToolCall, AgentMessage, ToolResult
from controlflow.events.task_events import TaskStart, TaskSuccess, TaskFailure


logger = logging.getLogger(__name__)

class FintelEventHandler(Handler):
    """Custom event handler for structured observability"""
    
    def __init__(self):
        super().__init__()
        self.events = []
    
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
            "tool_input": tool_input,  # Now properly extracted
            "tool_output": None,  # Will be filled by tool_result event
            "tool_summary": "Default summary",
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
