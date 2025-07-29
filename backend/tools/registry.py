# backend/tools/registry.py - Add this to the existing file
from typing import Dict, List, Any, Optional
import controlflow as cf
from pathlib import Path
from backend.tools.plugin_loader import ToolPluginLoader
from backend.tools.auto_discovery import get_auto_discovery
from .market_data import MarketDataTool, CompanyOverviewTool
from .economic_data import EconomicDataTool
from backend.config.settings import get_settings

class ToolRegistry:
    """Central registry for all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._tool_instances: Dict[str, Any] = {}
        self._tool_descriptions: Dict[str, str] = {}
        self._plugin_loader = ToolPluginLoader()
        self._auto_discovery = get_auto_discovery()
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools using automatic discovery"""
        settings = get_settings()
        
        # Instantiate and register built-in tool instances
        self._tool_instances['market_data'] = MarketDataTool()
        self._tool_instances['company_overview'] = CompanyOverviewTool()
        self._tool_instances['economic_data'] = EconomicDataTool()

        # Set tool instances for builtin_tools module
        from .builtin_tools import set_tool_instances
        set_tool_instances(self._tool_instances)

        # Use automatic discovery to find all tools
        discovered_tools = self._auto_discovery.discover_all_tools()
        
        # Create ControlFlow tools from discovered functions
        for tool_name, tool_func in discovered_tools.items():
            # Skip if already a ControlFlow tool
            if hasattr(tool_func, '_controlflow_tool'):
                self._tools[tool_name] = tool_func
            else:
                # Only wrap if it's a proper tool function (not helper functions)
                if tool_name in ['get_market_data', 'get_company_overview', 'get_economic_data_from_fred', 
                               'calculate_pe_ratio', 'analyze_cash_flow', 'get_competitor_analysis',
                               'process_strict_json']:
                    try:
                        cf_tool = cf.tool(tool_func)
                        self._tools[tool_name] = cf_tool
                    except Exception as e:
                        print(f"Warning: Failed to wrap tool {tool_name}: {e}")
                        # Keep the original function as fallback
                        self._tools[tool_name] = tool_func
        
        # Get descriptions from auto discovery
        self._tool_descriptions = self._auto_discovery.get_tool_descriptions()
        
        # Load legacy plugin tools (for backward compatibility)
        self._plugin_loader.load_plugins()
        plugin_tools = self._plugin_loader.get_all_tool_names()
        for tool_name in plugin_tools:
            if tool_name not in self._tools:
                self._tools[tool_name] = self._plugin_loader._controlflow_tools[tool_name]
                # Extract description from plugin tool if not already set
                if tool_name not in self._tool_descriptions:
                    tool_func = self._plugin_loader._controlflow_tools[tool_name]
                    if hasattr(tool_func, '__doc__') and tool_func.__doc__:
                        self._tool_descriptions[tool_name] = tool_func.__doc__.strip().split('\n')[0]
    
    def reload_plugins(self):
        """Reload all plugins - useful for development"""
        self._plugin_loader.load_plugins()
        self._initialize_tools()

    def get_tools(self, tool_names: List[str]) -> List[Any]:
        """Get specific tools by name"""
        tools = []
        for name in tool_names:
            if name in self._tools:
                tools.append(self._tools[name])
        return tools
        
    def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        return self._tools.copy()
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool descriptions"""
        return self._tool_descriptions.copy()

_tool_registry_instance = None

def get_tool_registry():
    """Returns a singleton instance of the ToolRegistry."""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    return _tool_registry_instance