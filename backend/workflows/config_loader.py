# backend/workflows/config_loader.py
"""
Workflow Configuration Loader

This module provides easy access to workflow configurations for agent and tool customization.
Allows changing agents and tools without code modifications.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
# Agent registry imported in methods to avoid circular imports

class WorkflowConfigLoader:
    """Loads and manages workflow configurations"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "workflow_config.yaml"
        self.config = self._load_config()
        # Agent registry imported in methods to avoid circular imports
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load workflow config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file not found"""
        return {
            "workflows": {
                "enhanced_simplified": {
                    "name": "Enhanced Simplified Analysis",
                    "agents": [
                        {"name": "MarketAnalyst", "role": "market_analysis", "required": True},
                        {"name": "FinancialAnalyst", "role": "sentiment_classification", "required": False},
                        {"name": "RiskAssessment", "role": "risk_assessment", "required": False},
                        {"name": "Summarizer", "role": "recommendation", "required": False}
                    ]
                }
            },
            "settings": {
                "default_workflow": "enhanced_simplified",
                "enable_fallback_agents": True
            }
        }
    
    def get_workflow_config(self, workflow_name: str = None) -> Dict[str, Any]:
        """Get configuration for a specific workflow"""
        workflow_name = workflow_name or self.config.get("settings", {}).get("default_workflow", "enhanced_simplified")
        return self.config.get("workflows", {}).get(workflow_name, {})
    
    def get_agents_for_workflow(self, workflow_name: str = None) -> List[Dict[str, Any]]:
        """Get agent configurations for a workflow"""
        workflow_config = self.get_workflow_config(workflow_name)
        return workflow_config.get("agents", [])
    
    def get_agent_for_role(self, workflow_name: str, role: str, provider: str = "openai") -> Optional[Any]:
        """Get an agent instance for a specific role in a workflow"""
        workflow_config = self.get_workflow_config(workflow_name)
        agents = workflow_config.get("agents", [])
        
        # Find agent configuration for this role
        agent_config = None
        for agent in agents:
            if agent.get("role") == role:
                agent_config = agent
                break
        
        if not agent_config:
            return None
        
        # Import agent registry here to avoid circular imports
        from ..agents.registry import get_agent_registry
        agent_registry = get_agent_registry()
        
        # Try to get the primary agent
        agent_name = agent_config.get("name")
        agent = agent_registry.get_agent(agent_name, provider)
        
        # If primary agent not available and fallback is enabled
        if not agent and self.config.get("settings", {}).get("enable_fallback_agents", True):
            fallback_name = agent_config.get("fallback")
            if fallback_name:
                agent = agent_registry.get_agent(fallback_name, provider)
        
        return agent
    
    def get_available_agents_for_workflow(self, workflow_name: str, provider: str = "openai") -> Dict[str, Any]:
        """Get all available agents for a workflow with availability status"""
        workflow_config = self.get_workflow_config(workflow_name)
        agents = workflow_config.get("agents", [])
        
        # Import agent registry here to avoid circular imports
        from ..agents.registry import get_agent_registry
        agent_registry = get_agent_registry()
        
        available_agents = {}
        for agent_config in agents:
            role = agent_config.get("role")
            agent_name = agent_config.get("name")
            
            # Check if primary agent is available
            agent = agent_registry.get_agent(agent_name, provider)
            if agent:
                available_agents[role] = {
                    "agent": agent,
                    "name": agent_name,
                    "primary": True,
                    "tools": agent_config.get("tools", [])
                }
            else:
                # Check fallback agent
                fallback_name = agent_config.get("fallback")
                if fallback_name:
                    fallback_agent = agent_registry.get_agent(fallback_name, provider)
                    if fallback_agent:
                        available_agents[role] = {
                            "agent": fallback_agent,
                            "name": fallback_name,
                            "primary": False,
                            "fallback_for": agent_name,
                            "tools": agent_config.get("tools", [])
                        }
        
        return available_agents
    
    def should_include_agent(self, workflow_name: str, agent_role: str, query: str) -> bool:
        """Determine if an agent should be included based on query keywords"""
        workflow_config = self.get_workflow_config(workflow_name)
        agent_selection = workflow_config.get("agent_selection", {})
        
        # Check if agent is required
        agents = workflow_config.get("agents", [])
        for agent in agents:
            if agent.get("role") == agent_role:
                if agent.get("required", False):
                    return True
                break
        
        # Check keyword matching
        query_lower = query.lower()
        
        if agent_role == "market_analysis":
            keywords = agent_selection.get("market_keywords", [])
        elif agent_role == "economic_analysis":
            keywords = agent_selection.get("economic_keywords", [])
        elif agent_role == "risk_assessment":
            keywords = agent_selection.get("risk_keywords", [])
        else:
            return True  # Include by default for other roles
        
        return any(keyword in query_lower for keyword in keywords)
    
    def get_tool_usage_tracking(self, workflow_name: str) -> bool:
        """Check if tool usage tracking is enabled for a workflow"""
        workflow_config = self.get_workflow_config(workflow_name)
        return workflow_config.get("track_tool_usage", True)
    
    def get_agent_invocation_tracking(self, workflow_name: str) -> bool:
        """Check if agent invocation tracking is enabled for a workflow"""
        workflow_config = self.get_workflow_config(workflow_name)
        return workflow_config.get("include_agent_invocations", True)

# Global instance
_config_loader = None

def get_workflow_config_loader() -> WorkflowConfigLoader:
    """Get global workflow configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = WorkflowConfigLoader()
    return _config_loader 