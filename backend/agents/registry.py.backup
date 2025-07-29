import yaml
from pathlib import Path
from typing import Dict, List, Optional
import controlflow as cf
from .base import BaseAgentConfig
from backend.providers.factory import ProviderFactory

class AgentRegistry:
    """Registry for managing agents and their configurations"""
    
    def __init__(self):
        self._agent_configs: Dict[str, BaseAgentConfig] = {}
        self._agents: Dict[str, cf.Agent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agent configurations from YAML"""
        self._load_yaml_agents()
    
    def _load_yaml_agents(self):
        """Load agents from agents.yaml file"""
        yaml_path = Path(__file__).parent.parent / "config" / "agents.yaml"
        if not yaml_path.exists():
            print(f"Warning: {yaml_path} not found. No agents will be loaded.")
            return
        
        try:
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # Load regular agents
            if 'agents' in data and data['agents'] is not None:
                for agent_data in data['agents']:
                    config = BaseAgentConfig(
                        name=agent_data['name'],
                        instructions=agent_data['instructions'],
                        tools=agent_data.get('tools', [])
                    )
                    self._agent_configs[agent_data['name']] = config
            
            # Load system agents
            if 'system_agents' in data and data['system_agents'] is not None:
                for agent_data in data['system_agents']:
                    config = BaseAgentConfig(
                        name=agent_data['name'],
                        instructions=agent_data['instructions'],
                        tools=agent_data.get('tools', [])
                    )
                    self._agent_configs[agent_data['name']] = config
                    
        except Exception as e:
            print(f"Error loading agents.yaml: {e}")
    
    def create_agent(self, agent_name: str, provider: str = "openai") -> Optional[cf.Agent]:
        """Create an agent instance with specified provider"""
        if agent_name not in self._agent_configs:
            return None
        
        # Get provider
        provider_instance = ProviderFactory.create_provider(provider)
        if not provider_instance:
            return None
        
        # Create model configuration
        model_config = provider_instance.create_model_config()
        
        # Create agent
        agent_config = self._agent_configs[agent_name]
        agent = agent_config.create_agent(model_config)
        
        # Cache agent
        cache_key = f"{agent_name}_{provider}"
        self._agents[cache_key] = agent
        
        return agent
    
    def get_agent(self, agent_name: str, provider: str = "openai") -> Optional[cf.Agent]:
        """Get cached agent or create new one"""
        cache_key = f"{agent_name}_{provider}"
        
        if cache_key in self._agents:
            return self._agents[cache_key]
        
        return self.create_agent(agent_name, provider)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self._agent_configs.keys())
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """Get agent configuration information"""
        if agent_name not in self._agent_configs:
            return None
        
        config = self._agent_configs[agent_name]
        return {
            "name": config.name,
            "instructions": config.instructions,
            "tools": config.tools,
        }
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have specific capabilities (tool-based)"""
        if capability == "all":
            return self.get_available_agents()

        agents_with_capability = []
        for agent_name, config in self._agent_configs.items():
            if capability in config.tools:
                agents_with_capability.append(agent_name)
        return agents_with_capability

# Global registry instance
_registry = None

def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
