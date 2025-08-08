# backend/agents/factory.py
"""
Config-Driven Agent Factory

Creates ControlFlow agents from configuration files using the registry system.
Single source of truth for agent creation with proper tool assignment.
"""

import controlflow as cf
from typing import Dict, List, Any, Optional
from ..workflows.config_loader import get_workflow_config_loader
from ..providers.factory import ProviderFactory
from ..utils.logging import setup_logging

logger = setup_logging()

class ConfigDrivenAgentFactory:
    """Creates ControlFlow agents from configuration with proper tool assignment"""
    
    def __init__(self):
        self.config_loader = get_workflow_config_loader()
        self.provider_factory = ProviderFactory()
        
        # Import registry manager here to avoid circular imports
        from ..registry.manager import get_registry_manager
        self.registry_manager = get_registry_manager()
        
        # Validate system health on initialization
        self._validate_system_health()
    
    def _validate_system_health(self):
        """Strict validation that prevents execution if system is unhealthy"""
        health_check = self.registry_manager.get_health_check()
        
        if not health_check["validation"]["valid"]:
            errors = health_check["validation"]["errors"]
            error_msg = "System validation failed. Cannot create agents:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if health_check["validation"]["warnings"]:
            warnings = health_check["validation"]["warnings"]
            logger.warning("System validation warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
    
    def create_agents_for_workflow(self, workflow_name: str, provider_name: str) -> Dict[str, cf.Agent]:
        """
        Create isolated agents for a specific workflow execution
        
        Args:
            workflow_name: Name of workflow from workflow_config.yaml
            provider_name: Provider to use (e.g., 'openai')
            
        Returns:
            Dict mapping agent role to ControlFlow Agent instance
        """
        logger.info(f"Creating agents for workflow '{workflow_name}' with provider '{provider_name}'")
        
        # Get workflow configuration
        workflow_config = self.config_loader.get_workflow_config(workflow_name)
        if not workflow_config:
            raise ValueError(f"Workflow '{workflow_name}' not found in configuration")
        
        # Get provider instance
        provider = self.provider_factory.get_provider(provider_name)
        if not provider or not provider.is_available():
            raise ValueError(f"Provider '{provider_name}' not available")
        
        # Create model config for ControlFlow
        model_config = provider.create_model_config()
        
        agents = {}
        agent_configs = workflow_config.get('agents', [])
        
        for agent_config in agent_configs:
            try:
                agent = self._create_agent_from_config(agent_config, model_config, workflow_name)
                if agent:
                    role = agent_config.get('role')
                    agents[role] = agent
                    logger.info(f"Created agent '{agent.name}' for role '{role}'")
                    
            except Exception as e:
                # Try fallback agent if primary fails
                fallback_name = agent_config.get('fallback')
                if fallback_name:
                    logger.warning(f"Primary agent '{agent_config['name']}' failed, trying fallback '{fallback_name}': {e}")
                    try:
                        fallback_config = agent_config.copy()
                        fallback_config['name'] = fallback_name
                        agent = self._create_agent_from_config(fallback_config, model_config, workflow_name)
                        if agent:
                            role = agent_config.get('role')
                            agents[role] = agent
                            logger.info(f"Created fallback agent '{fallback_name}' for role '{role}'")
                    except Exception as fallback_error:
                        logger.error(f"Both primary and fallback agents failed for role '{agent_config.get('role')}': {fallback_error}")
                        if agent_config.get('required', False):
                            raise ValueError(f"Required agent for role '{agent_config.get('role')}' could not be created")
                else:
                    logger.error(f"Agent creation failed for role '{agent_config.get('role')}': {e}")
                    if agent_config.get('required', False):
                        raise ValueError(f"Required agent for role '{agent_config.get('role')}' could not be created")
        
        if not agents:
            raise ValueError(f"No agents could be created for workflow '{workflow_name}'")
        
        logger.info(f"Successfully created {len(agents)} agents for workflow '{workflow_name}'")
        return agents
    
    def _create_agent_from_config(self, agent_config: Dict[str, Any], model_config: str, workflow_name: str) -> Optional[cf.Agent]:
        """Create a single ControlFlow agent from configuration"""
        
        agent_name = agent_config.get('name')
        if not agent_name:
            raise ValueError("Agent configuration missing 'name' field")
        
        # Get agent info from registry
        agent_info = self.registry_manager.get_agent_info(agent_name)
        if not agent_info or not agent_info.get("enabled", True):
            raise ValueError(f"Agent '{agent_name}' not available in registry")
        
        # Resolve tools for this agent
        tools = self._resolve_tools_for_agent(agent_config, workflow_name)
        
        # Create ControlFlow agent with proper configuration
        agent = cf.Agent(
            name=agent_name,
            model=model_config,
            tools=tools,
            instructions=agent_info.get("instructions", f"You are {agent_name}, a specialized AI assistant.")
        )
        
        return agent
    
    def _resolve_tools_for_agent(self, agent_config: Dict[str, Any], workflow_name: str) -> List[Any]:
        """Resolve tool functions from configuration using the tool registry"""
        
        tool_names = agent_config.get('tools', [])
        if not tool_names:
            logger.info(f"No tools specified for agent '{agent_config.get('name')}'")
            return []
        
        # Validate tool availability first
        validation_results = self.registry_manager.tool_registry.validate_tool_availability(tool_names)
        
        tools = []
        for tool_name in tool_names:
            validation_status = validation_results.get(tool_name, "not_found")
            
            if validation_status == "available":
                tool_func = self.registry_manager.tool_registry.get_tool(tool_name)
                if tool_func:
                    tools.append(tool_func)
                    logger.debug(f"Added tool '{tool_name}' to agent '{agent_config.get('name')}'")
            elif validation_status == "api_key_missing":
                logger.warning(f"Tool '{tool_name}' requires API key that is not available")
            else:
                logger.warning(f"Tool '{tool_name}' not available: {validation_status}")
        
        logger.info(f"Resolved {len(tools)} tools for agent '{agent_config.get('name')}'")
        return tools
    
    def validate_workflow_agents(self, workflow_name: str, provider_name: str) -> Dict[str, Any]:
        """
        Validate that all required agents can be created for a workflow
        
        Returns validation results without actually creating agents
        """
        try:
            workflow_config = self.config_loader.get_workflow_config(workflow_name)
            if not workflow_config:
                return {"valid": False, "error": f"Workflow '{workflow_name}' not found"}
            
            provider = self.provider_factory.get_provider(provider_name)
            if not provider or not provider.is_available():
                return {"valid": False, "error": f"Provider '{provider_name}' not available"}
            
            validation_results = {
                "valid": True,
                "agents": {},
                "warnings": []
            }
            
            for agent_config in workflow_config.get('agents', []):
                agent_name = agent_config.get('name')
                role = agent_config.get('role')
                
                # Check agent availability
                agent_info = self.registry_manager.get_agent_info(agent_name)
                if not agent_info or not agent_info.get("enabled", True):
                    if agent_config.get('required', False):
                        validation_results["valid"] = False
                        validation_results["agents"][role] = {"status": "missing", "required": True}
                    else:
                        validation_results["warnings"].append(f"Optional agent '{agent_name}' not available")
                        validation_results["agents"][role] = {"status": "missing", "required": False}
                else:
                    # Check tools
                    tool_names = agent_config.get('tools', [])
                    tool_validation = self.registry_manager.tool_registry.validate_tool_availability(tool_names)
                    
                    available_tools = [name for name, status in tool_validation.items() if status == "available"]
                    missing_tools = [name for name, status in tool_validation.items() if status != "available"]
                    
                    validation_results["agents"][role] = {
                        "status": "available",
                        "available_tools": available_tools,
                        "missing_tools": missing_tools
                    }
                    
                    if missing_tools:
                        validation_results["warnings"].append(f"Agent '{agent_name}' missing tools: {missing_tools}")
            
            return validation_results
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

# Singleton instance
_agent_factory_instance = None

def get_agent_factory() -> ConfigDrivenAgentFactory:
    """Get singleton agent factory instance"""
    global _agent_factory_instance
    if _agent_factory_instance is None:
        _agent_factory_instance = ConfigDrivenAgentFactory()
    return _agent_factory_instance