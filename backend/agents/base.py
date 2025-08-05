from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import controlflow as cf

@dataclass
class BaseAgentConfig:
    """Base configuration for agents with enhanced metadata"""
    name: str
    instructions: str
    tools: List[str]
    capabilities: List[str] = None
    required: bool = False
    enabled: bool = True
    model: Optional[str] = None
    temperature: float = 0.1
    fallback_agent: Optional[str] = None
    retry_config: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields"""
        if self.capabilities is None:
            self.capabilities = []
        if self.retry_config is None:
            self.retry_config = {}
    
    def create_agent(self, model: str) -> cf.Agent:
        """Create ControlFlow agent instance with enhanced tool validation"""
        from backend.tools.registry import get_tool_registry
        tool_registry = get_tool_registry()
        available_tools = tool_registry.get_available_tools()
        
        # Get tools for this agent with validation
        agent_tools = []
        missing_tools = []
        
        for tool_name in self.tools:
            if tool_name in available_tools:
                agent_tools.append(available_tools[tool_name])
            else:
                missing_tools.append(tool_name)
        
        # Log missing tools for debugging
        if missing_tools:
            print(f"Warning: Agent '{self.name}' has missing tools: {missing_tools}")
        
        return cf.Agent(
            name=self.name,
            instructions=self.instructions,
            tools=agent_tools,
            model=model
        )
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get validation status for this agent configuration"""
        from backend.tools.registry import get_tool_registry
        
        try:
            tool_registry = get_tool_registry()
            tool_validation = tool_registry.validate_tool_availability(self.tools)
            
            return {
                "valid": True,
                "enabled": self.enabled,
                "required": self.required,
                "tool_validation": tool_validation,
                "missing_tools": [tool for tool, status in tool_validation.items() if status != "available"],
                "capabilities": self.capabilities,
                "has_capabilities": len(self.capabilities) > 0
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "enabled": self.enabled,
                "required": self.required
            }