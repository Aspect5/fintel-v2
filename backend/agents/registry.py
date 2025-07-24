import yaml
from pathlib import Path
from typing import Dict, List, Optional
import controlflow as cf
from .base import BaseAgentConfig
from .financial import FinancialAnalystConfig
from .market import MarketAnalystConfig
from .economic import EconomicAnalystConfig
from providers.factory import ProviderFactory

class AgentRegistry:
    """Registry for managing agents and their configurations"""
    
    def __init__(self):
        self._agent_configs: Dict[str, BaseAgentConfig] = {}
        self._agents: Dict[str, cf.Agent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agent configurations"""
        # Built-in specialized agents
        self._agent_configs = {
            "FinancialAnalyst": FinancialAnalystConfig(),
            "MarketAnalyst": MarketAnalystConfig(),
            "EconomicAnalyst": EconomicAnalystConfig()
        }
        
        # Load additional agents from YAML if exists
        self._load_yaml_agents()
    
    def _load_yaml_agents(self):
        """Load agents from agents.yaml file"""
        yaml_path = Path(__file__).parent.parent / "config" / "agents.yaml"
        if not yaml_path.exists():
            return
        
        try:
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # Load regular agents
            if 'agents' in data:
                for agent_data in data['agents']:
                    config = BaseAgentConfig(
                        name=agent_data['name'],
                        instructions=agent_data['instructions'],
                        tools=agent_data.get('tools', [])
                    )
                    self._agent_configs[agent_data['name']] = config
            
            # Load system agents
            if 'system_agents' in data:
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
            "specialized": agent_name in ["FinancialAnalyst", "MarketAnalyst", "EconomicAnalyst"]
        }
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have specific capabilities"""
        capability_map = {
            "market_analysis": ["MarketAnalyst", "FinancialAnalyst"],
            "economic_analysis": ["EconomicAnalyst", "FinancialAnalyst"],
            "comprehensive": ["FinancialAnalyst"],
            "all": list(self._agent_configs.keys())
        }
        
        return capability_map.get(capability, [])

# Global registry instance
_registry = None

def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry