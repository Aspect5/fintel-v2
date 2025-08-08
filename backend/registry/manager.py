# backend/registry/manager.py - Unified Registry Manager
"""
Unified Registry Manager - Single Source of Truth Coordinator

This module provides a unified interface for managing tools and agents,
ensuring consistency and validation across the entire system.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml

from backend.tools.registry import get_tool_registry, ToolCategory
from backend.agents.registry import get_agent_registry

@dataclass
class ValidationResult:
    """Result of registry validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]

class RegistryManager:
    """Unified registry manager for tools and agents"""
    
    def __init__(self):
        self.tool_registry = get_tool_registry()
        self.agent_registry = get_agent_registry()
        self.validation_result = None
        self._validate_registries()
    
    def _validate_registries(self) -> ValidationResult:
        """Validate that all agent tools exist in tool registry with enhanced checks"""
        errors = []
        warnings = []
        details = {
            "tool_validation": {},
            "agent_validation": {},
            "tool_agent_mapping": {},
            "capability_mapping": {},
            "api_key_validation": {},
            "system_health": {}
        }
        
        # Get all available tools
        available_tools = set(self.tool_registry._tools.keys())
        enabled_tools = set(name for name, info in self.tool_registry._tools.items() if info.enabled)
        
        # Validate each agent's tools
        for agent_name, agent_config in self.agent_registry._agent_configs.items():
            agent_tools = agent_config.tools
            missing_tools = []
            disabled_tools = []
            valid_tools = []
            api_key_issues = []
            
            for tool_name in agent_tools:
                if tool_name not in available_tools:
                    missing_tools.append(tool_name)
                elif tool_name not in enabled_tools:
                    disabled_tools.append(tool_name)
                else:
                    valid_tools.append(tool_name)
                    
                    # Check API key requirements
                    tool_info = self.tool_registry._tools[tool_name]
                    if tool_info.api_key_required:
                        from backend.config.settings import get_settings
                        settings = get_settings()
                        api_key_map = {
                            'alpha_vantage': settings.alpha_vantage_api_key,
                            'fred': settings.fred_api_key,
                            'openai': settings.openai_api_key,
                            'google': settings.google_api_key
                        }
                        
                        if not api_key_map.get(tool_info.api_key_required):
                            api_key_issues.append(f"{tool_name} (requires {tool_info.api_key_required})")
            
            # Record validation results
            details["agent_validation"][agent_name] = {
                "tools": agent_tools,
                "valid_tools": valid_tools,
                "missing_tools": missing_tools,
                "disabled_tools": disabled_tools,
                "api_key_issues": api_key_issues,
                "enabled": agent_config.enabled,
                "required": agent_config.required,
                "capabilities": list(self.agent_registry._capabilities.get(agent_name, []))
            }
            
            # Generate errors and warnings
            if missing_tools:
                errors.append(f"Agent '{agent_name}' references non-existent tools: {missing_tools}")
            
            if disabled_tools:
                warnings.append(f"Agent '{agent_name}' references disabled tools: {disabled_tools}")
            
            if api_key_issues:
                warnings.append(f"Agent '{agent_name}' has tools with missing API keys: {api_key_issues}")
            
            # Check required agents
            if agent_config.required and not agent_config.enabled:
                errors.append(f"Required agent '{agent_name}' is disabled")
        
        # Create tool-to-agent mapping
        tool_agent_mapping = {}
        for agent_name, agent_config in self.agent_registry._agent_configs.items():
            for tool_name in agent_config.tools:
                if tool_name not in tool_agent_mapping:
                    tool_agent_mapping[tool_name] = []
                tool_agent_mapping[tool_name].append(agent_name)
        
        details["tool_agent_mapping"] = tool_agent_mapping
        
        # Create capability mapping
        details["capability_mapping"] = self.agent_registry.get_capability_to_agents_mapping()
        
        # Validate tool availability and API keys
        for tool_name in available_tools:
            tool_info = self.tool_registry._tools[tool_name]
            details["tool_validation"][tool_name] = {
                "enabled": tool_info.enabled,
                "category": tool_info.category.value,
                "api_key_required": tool_info.api_key_required,
                "used_by_agents": tool_agent_mapping.get(tool_name, []),
                "callable": callable(tool_info.function)
            }
        
        # API key validation
        from backend.config.settings import get_settings
        settings = get_settings()
        api_keys = {
            'alpha_vantage': settings.alpha_vantage_api_key,
            'fred': settings.fred_api_key,
            'openai': settings.openai_api_key,
            'google': settings.google_api_key
        }
        
        details["api_key_validation"] = {
            key_name: bool(key_value and key_value.strip())
            for key_name, key_value in api_keys.items()
        }

        # Derived warnings for missing keys affecting enabled tools
        missing_key_to_tools: Dict[str, List[str]] = {}
        for tool_name, tool_info in self.tool_registry._tools.items():
            if not tool_info.enabled:
                continue
            required = tool_info.api_key_required
            if required and not details["api_key_validation"].get(required, False):
                missing_key_to_tools.setdefault(required, []).append(tool_name)
        for key_name, tool_list in missing_key_to_tools.items():
            if tool_list:
                warnings.append(
                    f"Missing API key '{key_name}' — affected tools: {sorted(tool_list)}"
                )
        
        # System health summary
        details["system_health"] = {
            "total_tools": len(available_tools),
            "enabled_tools": len(enabled_tools),
            "total_agents": len(self.agent_registry._agent_configs),
            "enabled_agents": len(self.agent_registry.get_available_agents()),
            "required_agents": len([a for a in self.agent_registry._agent_configs.values() if a.required]),
            "capabilities": list(set().union(*self.agent_registry._capabilities.values())),
            "validation_errors": len(errors),
            "validation_warnings": len(warnings)
        }
        
        # Create validation result
        self.validation_result = ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
        
        return self.validation_result
    
    def get_validation_status(self) -> ValidationResult:
        """Get current validation status"""
        if self.validation_result is None:
            self._validate_registries()
        return self.validation_result
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed tool information"""
        return self.tool_registry.get_tool_info(tool_name)
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed agent information"""
        return self.agent_registry.get_agent_info(agent_name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get all tools in a category"""
        return self.tool_registry.get_tools_by_category(category)
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have specific capabilities"""
        return self.agent_registry.get_agents_by_capability(capability)
    
    def get_agents_by_tool(self, tool_name: str) -> List[str]:
        """Get all agents that can use a specific tool"""
        return self.agent_registry.get_agents_by_tool(tool_name)
    
    def get_tool_to_agents_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of tools to agents that can use them"""
        return self.agent_registry.get_tool_to_agents_mapping()
    
    def get_capability_to_agents_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of capabilities to agents that have them"""
        return self.agent_registry.get_capability_to_agents_mapping()
    
    def validate_agent_tools(self, agent_name: str) -> Dict[str, str]:
        """Validate that an agent's tools are available"""
        agent_info = self.get_agent_info(agent_name)
        if not agent_info:
            return {"error": "Agent not found"}
        
        tool_names = agent_info.get("tools", [])
        return self.tool_registry.validate_tool_availability(tool_names)
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a comprehensive system summary"""
        validation = self.get_validation_status()
        
        return {
            "validation": {
                "valid": validation.valid,
                "error_count": len(validation.errors),
                "warning_count": len(validation.warnings)
            },
            "tools": {
                "total": len(self.tool_registry._tools),
                "enabled": len([t for t in self.tool_registry._tools.values() if t.enabled]),
                "categories": list(set(t.category.value for t in self.tool_registry._tools.values())),
                "configuration_summary": self.tool_registry.get_configuration_summary(),
                "validation_status": self.tool_registry.get_validation_status()
            },
            "agents": {
                "total": len(self.agent_registry._agent_configs),
                "enabled": len(self.agent_registry.get_available_agents()),
                "required": len([a for a in self.agent_registry._agent_configs.values() if a.required]),
                "available": self.agent_registry.get_available_agents(),
                "capabilities": self._get_all_capabilities(),
                "validation_status": self.agent_registry.get_validation_status()
            },
            "mapping": {
                "tool_to_agents": self.get_tool_to_agents_mapping(),
                "capability_to_agents": self.get_capability_to_agents_mapping(),
                "agent_tool_validation": {
                    agent: self.validate_agent_tools(agent) 
                    for agent in self.agent_registry.get_available_agents()
                }
            },
            "api_keys": validation.details.get("api_key_validation", {}),
            "system_health": validation.details.get("system_health", {})
        }
    
    def _get_all_capabilities(self) -> List[str]:
        """Get all unique capabilities across agents"""
        capabilities = set()
        for agent_name in self.agent_registry.get_available_agents():
            agent_info = self.get_agent_info(agent_name)
            if agent_info and "capabilities" in agent_info:
                capabilities.update(agent_info["capabilities"])
        return list(capabilities)
    
    def get_agent_with_tools(self, agent_name: str, provider: str = "openai"):
        """Get an agent instance with its validated tools"""
        # Validate agent tools first
        tool_validation = self.validate_agent_tools(agent_name)
        
        if "error" in tool_validation:
            raise ValueError(f"Agent validation failed: {tool_validation['error']}")
        
        # Get agent instance
        agent = self.agent_registry.get_agent(agent_name, provider)
        if not agent:
            raise ValueError(f"Failed to create agent: {agent_name}")
        
        return agent
    
    def get_tools_for_agent(self, agent_name: str) -> List[str]:
        """Get list of tools available to an agent"""
        agent_info = self.get_agent_info(agent_name)
        if not agent_info:
            return []
        
        tools = agent_info.get("tools", [])
        # Filter to only enabled tools
        return [tool for tool in tools if self.tool_registry.has_tool(tool)]
    
    def get_agents_for_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Get agents suitable for a specific workflow"""
        # This could be enhanced to load workflow-specific agent requirements
        available_agents = self.agent_registry.get_available_agents()
        
        workflow_agents = {}
        for agent_name in available_agents:
            agent_info = self.get_agent_info(agent_name)
            if agent_info:
                workflow_agents[agent_name] = {
                    "name": agent_name,
                    "capabilities": agent_info.get("capabilities", []),
                    "tools": agent_info.get("tools", []),
                    "required": agent_info.get("required", False),
                    "enabled": agent_info.get("enabled", True),
                    "validation": agent_info.get("validation_status", {})
                }
        
        return workflow_agents
    
    def get_health_check(self) -> Dict[str, Any]:
        """Get comprehensive health check for the system"""
        validation = self.get_validation_status()
        
        return {
            "status": "healthy" if validation.valid else "degraded",
            "validation": {
                "valid": validation.valid,
                "errors": validation.errors,
                "warnings": validation.warnings
            },
            "components": {
                "tool_registry": self.tool_registry.get_validation_status(),
                "agent_registry": self.agent_registry.get_validation_status()
            },
            "summary": validation.details.get("system_health", {}),
            "api_keys": validation.details.get("api_key_validation", {})
        }

# Global registry manager instance
_registry_manager = None

def get_registry_manager() -> RegistryManager:
    """Get global registry manager instance"""
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = RegistryManager()
    return _registry_manager 