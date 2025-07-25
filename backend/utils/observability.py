# backend/utils/observability.py
import logging
import controlflow as cf
from typing import Dict, Any
import json
from datetime import datetime
from controlflow.orchestration.handler import Handler
from controlflow.events.events import AgentToolCall


logger = logging.getLogger(__name__)

class FintelEventHandler(Handler):
    """Custom event handler for structured observability"""
    
    def __init__(self):
        super().__init__()
        self.events = []
    
    def on_agent_tool_call(self, event: AgentToolCall):
        """Log agent tool calls"""
        # event.tool_call is a dictionary, so we use .get() for safe access
        tool_call_data = event.tool_call or {}
        log_data = {
            "event_type": "agent_tool_call",
            "agent_name": event.agent.name,
            "tool_name": tool_call_data.get('name', 'unknown_tool'),
            "tool_input": tool_call_data.get('input', {}),
            "tool_output": tool_call_data.get('result', None),
            "tool_summary": "Default summary", # Placeholder
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Tool Called: {json.dumps(log_data)}")
        self.events.append(log_data)
