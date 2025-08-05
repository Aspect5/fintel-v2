import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import controlflow as cf
from .base import BaseAgentConfig
from backend.providers.factory import ProviderFactory

class AgentRegistry:
    """Registry for managing agents and their configurations"""
    
    def __init__(self):
        self._agent_configs: Dict[str, BaseAgentConfig] = {}
        self._agents: Dict[str, cf.Agent] = {}
        self._capabilities: Dict[str, Set[str]] = {}
        self._validation_errors: List[str] = []
        self._validation_warnings: List[str] = []
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agent configurations from YAML with enhanced validation"""
        self._load_yaml_agents()
        self._validate_agent_configurations()
    
    def _load_yaml_agents(self):
        """Load agents from agents.yaml file with enhanced error handling"""
        yaml_path = Path(__file__).parent.parent / "config" / "agents.yaml"
        if not yaml_path.exists():
            self._validation_errors.append(f"Agent configuration file not found: {yaml_path}")
            print(f"Warning: {yaml_path} not found. No agents will be loaded.")
            return
        
        try:
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # Load regular agents
            if 'agents' in data and data['agents'] is not None:
                for agent_name, agent_data in data['agents'].items():
                    try:
                        config = BaseAgentConfig(
                            name=agent_data['name'],
                            instructions=agent_data['instructions'],
                            tools=agent_data.get('tools', []),
                            capabilities=agent_data.get('capabilities', []),
                            required=agent_data.get('required', False),
                            enabled=agent_data.get('enabled', True)
                        )
                        self._agent_configs[agent_data['name']] = config
                        
                        # Track capabilities
                        self._capabilities[agent_data['name']] = set(agent_data.get('capabilities', []))
                        
                    except Exception as e:
                        self._validation_errors.append(f"Error loading agent {agent_name}: {e}")
                        print(f"Error loading agent {agent_name}: {e}")
            
            # Load system agents
            if 'system_agents' in data and data['system_agents'] is not None:
                for agent_name, agent_data in data['system_agents'].items():
                    try:
                        config = BaseAgentConfig(
                            name=agent_data['name'],
                            instructions=agent_data['instructions'],
                            tools=agent_data.get('tools', []),
                            capabilities=agent_data.get('capabilities', []),
                            required=agent_data.get('required', False),
                            enabled=agent_data.get('enabled', True)
                        )
                        self._agent_configs[agent_data['name']] = config
                        
                        # Track capabilities
                        self._capabilities[agent_data['name']] = set(agent_data.get('capabilities', []))
                        
                    except Exception as e:
                        self._validation_errors.append(f"Error loading system agent {agent_name}: {e}")
                        print(f"Error loading system agent {agent_name}: {e}")
                    
        except Exception as e:
            self._validation_errors.append(f"Error loading agents.yaml: {e}")
            print(f"Error loading agents.yaml: {e}")
    
    def _validate_agent_configurations(self):
        """Validate agent configurations and tool dependencies"""
        # Get tool registry for validation
        try:
            from backend.tools.registry import get_tool_registry
            tool_registry = get_tool_registry()
        except Exception as e:
            self._validation_warnings.append(f"Could not access tool registry for validation: {e}")
            return
        
        for agent_name, agent_config in self._agent_configs.items():
            # Validate tools
            for tool_name in agent_config.tools:
                if not tool_registry.has_tool(tool_name):
                    self._validation_errors.append(
                        f"Agent '{agent_name}' references non-existent tool: {tool_name}"
                    )
                else:
                    # Check if tool requires API key that might not be available
                    tool_info = tool_registry.get_tool_info(tool_name)
                    if tool_info and tool_info.get('api_key_required'):
                        # This will be validated by the tool registry itself
                        pass
            
            # Validate capabilities
            if not agent_config.capabilities:
                self._validation_warnings.append(f"Agent '{agent_name}' has no defined capabilities")
            
            # Validate required agents
            if agent_config.required and not agent_config.enabled:
                self._validation_warnings.append(f"Required agent '{agent_name}' is disabled")
    
    def create_agent(self, agent_name: str, provider: str = "openai") -> Optional[cf.Agent]:
        """Create an agent instance with specified provider and validation"""
        if agent_name not in self._agent_configs:
            self._validation_errors.append(f"Agent '{agent_name}' not found in configuration")
            return None
        
        agent_config = self._agent_configs[agent_name]
        
        # Check if agent is enabled
        if not agent_config.enabled:
            self._validation_warnings.append(f"Attempted to create disabled agent: {agent_name}")
            return None
        
        # Get provider
        provider_instance = ProviderFactory.create_provider(provider)
        if not provider_instance:
            self._validation_errors.append(f"Provider '{provider}' not available")
            return None
        
        # Create model configuration
        model_config = provider_instance.create_model_config()
        
        # Create agent
        try:
            agent = agent_config.create_agent(model_config)
            
            # Cache agent
            cache_key = f"{agent_name}_{provider}"
            self._agents[cache_key] = agent
            
            return agent
            
        except Exception as e:
            self._validation_errors.append(f"Failed to create agent '{agent_name}': {e}")
            return None
    
    def get_agent(self, agent_name: str, provider: str = "openai") -> Optional[cf.Agent]:
        """Get cached agent or create new one with validation"""
        cache_key = f"{agent_name}_{provider}"
        
        if cache_key in self._agents:
            return self._agents[cache_key]
        
        return self.create_agent(agent_name, provider)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return [name for name, config in self._agent_configs.items() if config.enabled]
    
    def get_all_agents(self) -> List[str]:
        """Get list of all agent names (including disabled)"""
        return list(self._agent_configs.keys())
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """Get agent configuration information with enhanced details"""
        if agent_name not in self._agent_configs:
            return None
        
        config = self._agent_configs[agent_name]
        return {
            "name": config.name,
            "instructions": config.instructions,
            "tools": config.tools,
            "capabilities": list(self._capabilities.get(agent_name, [])),
            "required": config.required,
            "enabled": config.enabled,
            "validation_status": self._get_agent_validation_status(agent_name)
        }
    
    def _get_agent_validation_status(self, agent_name: str) -> Dict[str, Any]:
        """Get validation status for a specific agent"""
        if agent_name not in self._agent_configs:
            return {"valid": False, "error": "Agent not found"}
        
        config = self._agent_configs[agent_name]
        validation_status = {
            "valid": True,
            "enabled": config.enabled,
            "required": config.required,
            "tool_validation": {},
            "capability_validation": {}
        }
        
        # Validate tools
        try:
            from backend.tools.registry import get_tool_registry
            tool_registry = get_tool_registry()
            
            tool_validation = tool_registry.validate_tool_availability(config.tools)
            validation_status["tool_validation"] = tool_validation
            
            # Check for missing tools
            missing_tools = [tool for tool, status in tool_validation.items() if status != "available"]
            if missing_tools:
                validation_status["valid"] = False
                validation_status["missing_tools"] = missing_tools
                
        except Exception as e:
            validation_status["tool_validation_error"] = str(e)
        
        # Validate capabilities
        capabilities = self._capabilities.get(agent_name, set())
        validation_status["capability_validation"] = {
            "has_capabilities": len(capabilities) > 0,
            "capabilities": list(capabilities)
        }
        
        return validation_status
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have specific capabilities"""
        if capability == "all":
            return self.get_available_agents()

        agents_with_capability = []
        for agent_name, capabilities in self._capabilities.items():
            if capability in capabilities and self._agent_configs[agent_name].enabled:
                agents_with_capability.append(agent_name)
        return agents_with_capability
    
    def get_agents_by_tool(self, tool_name: str) -> List[str]:
        """Get all agents that can use a specific tool"""
        mapping = self.get_tool_to_agents_mapping()
        return mapping.get(tool_name, [])
    
    def get_tool_to_agents_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of tools to agents that can use them"""
        tool_to_agents = {}
        for agent_name in self.get_available_agents():
            try:
                agent_info = self.get_agent_info(agent_name)
                if agent_info and "tools" in agent_info:
                    for tool_name in agent_info["tools"]:
                        if tool_name not in tool_to_agents:
                            tool_to_agents[tool_name] = []
                        tool_to_agents[tool_name].append(agent_name)
            except Exception as e:
                self._validation_warnings.append(f"Error processing agent {agent_name}: {e}")
                continue
        return tool_to_agents
    
    def get_capability_to_agents_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of capabilities to agents that have them"""
        capability_to_agents = {}
        for agent_name, capabilities in self._capabilities.items():
            if self._agent_configs[agent_name].enabled:
                for capability in capabilities:
                    if capability not in capability_to_agents:
                        capability_to_agents[capability] = []
                    capability_to_agents[capability].append(agent_name)
        return capability_to_agents
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get validation status of the agent registry"""
        return {
            "valid": len(self._validation_errors) == 0,
            "errors": self._validation_errors,
            "warnings": self._validation_warnings,
            "total_agents": len(self._agent_configs),
            "enabled_agents": len(self.get_available_agents()),
            "required_agents": len([a for a in self._agent_configs.values() if a.required]),
            "capabilities": list(set().union(*self._capabilities.values()))
        }
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a comprehensive system summary"""
        return {
            "agents": {
                "total": len(self._agent_configs),
                "enabled": len(self.get_available_agents()),
                "required": len([a for a in self._agent_configs.values() if a.required]),
                "capabilities": list(set().union(*self._capabilities.values()))
            },
            "validation": self.get_validation_status(),
            "mappings": {
                "tool_to_agents": self.get_tool_to_agents_mapping(),
                "capability_to_agents": self.get_capability_to_agents_mapping()
            }
        }

# Global registry instance
_registry = None

def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
