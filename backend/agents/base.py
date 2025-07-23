from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import controlflow as cf
from tools.registry import get_tool_registry

@dataclass
class BaseAgentConfig:
    """Base configuration for agents"""
    name: str
    instructions: str
    tools: List[str]
    model: Optional[str] = None
    temperature: float = 0.1
    
    def create_agent(self, model: str) -> cf.Agent:
        """Create ControlFlow agent instance"""
        tool_registry = get_tool_registry()
        available_tools = tool_registry.get_available_tools()
        
        # Get tools for this agent
        agent_tools = []
        for tool_name in self.tools:
            if tool_name in available_tools:
                agent_tools.append(available_tools[tool_name])
        
        return cf.Agent(
            name=self.name,
            instructions=self.instructions,
            tools=agent_tools,
            model=model
        )