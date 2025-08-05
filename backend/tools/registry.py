# backend/tools/registry.py - Unified Tool Registry with YAML Configuration
from typing import Dict, Any, List, Optional
import controlflow as cf
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import yaml
from pathlib import Path
from .base import BaseTool, ToolResult
from .market_data import MarketDataTool, CompanyOverviewTool
from .economic_data import EconomicDataTool
from backend.config.settings import get_settings

class ToolCategory(Enum):
    """Tool categories from configuration"""
    MARKET_DATA = "market_data"
    ECONOMIC_DATA = "economic_data"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    UTILITY = "utility"

@dataclass
class ToolInfo:
    """Enhanced tool information from YAML configuration"""
    name: str
    description: str
    category: ToolCategory
    function: Any
    class_name: Optional[str] = None
    api_key_required: Optional[str] = None
    enabled: bool = True
    examples: List[str] = None
    dependencies: List[str] = None
    retry_config: Dict[str, Any] = None

class UnifiedToolRegistry:
    """Unified tool registry using YAML configuration as single source of truth"""
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._tool_instances: Dict[str, Any] = {}
        self._usage_stats: Dict[str, Dict[str, Any]] = {}
        self._config: Dict[str, Any] = {}
        self._validation_errors: List[str] = []
        self._validation_warnings: List[str] = []
        self._initialize_tools()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load tool configuration from YAML file"""
        config_path = Path(__file__).parent.parent / "config" / "tools.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Tool configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise ValueError(f"Error loading tool configuration: {e}")
    
    def _validate_api_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are available"""
        settings = get_settings()
        api_key_status = {}
        
        # Check each required API key
        api_keys = {
            'alpha_vantage': settings.alpha_vantage_api_key,
            'fred': settings.fred_api_key,
            'openai': settings.openai_api_key,
            'google': settings.google_api_key
        }
        
        for key_name, key_value in api_keys.items():
            api_key_status[key_name] = bool(key_value and key_value.strip())
        
        return api_key_status
    
    def _initialize_tools(self):
        """Initialize tools from YAML configuration with enhanced validation"""
        try:
            # Load configuration
            self._config = self._load_config()
            
            # Validate API keys
            api_key_status = self._validate_api_keys()
            
            # Get settings for API keys
            settings = get_settings()
            
            # Create tool instances for external APIs
            self._tool_instances['market_data'] = MarketDataTool(api_key=settings.alpha_vantage_api_key)
            self._tool_instances['company_overview'] = CompanyOverviewTool(api_key=settings.alpha_vantage_api_key)
            self._tool_instances['economic_data'] = EconomicDataTool(api_key=settings.fred_api_key)
            
            # Set tool instances for builtin_tools module
            from .builtin_tools import set_tool_instances
            set_tool_instances(self._tool_instances)
            
            # Register tools from configuration
            self._register_tools_from_config(api_key_status)
            
            # Validate tool availability
            self._validate_tool_availability()
            
        except Exception as e:
            self._validation_errors.append(f"Error initializing tool registry: {e}")
            print(f"Error initializing tool registry: {e}")
            raise
    
    def _register_tools_from_config(self, api_key_status: Dict[str, bool]):
        """Register all tools from YAML configuration with API key validation"""
        if 'tools' not in self._config:
            raise ValueError("No tools section found in configuration")
        
        for tool_id, tool_config in self._config['tools'].items():
            if tool_config.get('enabled', True):
                # Check if API key is available for this tool
                required_api_key = tool_config.get('api_key_required')
                if required_api_key and not api_key_status.get(required_api_key, False):
                    self._validation_warnings.append(
                        f"Tool '{tool_id}' requires API key '{required_api_key}' which is not available"
                    )
                    # Still register the tool but mark it as potentially non-functional
                
                self._register_tool_from_config(tool_id, tool_config)
    
    def _register_tool_from_config(self, tool_id: str, tool_config: Dict[str, Any]):
        """Register a single tool from configuration with enhanced error handling"""
        try:
            # Get the actual function from builtin_tools
            from .builtin_tools import get_tool_function
            tool_func = get_tool_function(tool_config['function'])
            
            if not tool_func:
                self._validation_errors.append(f"Tool function {tool_config['function']} not found in builtin_tools")
                return
            
            # Create ToolInfo object with enhanced metadata
            tool_info = ToolInfo(
                name=tool_config['name'],
                description=tool_config['description'],
                category=ToolCategory(tool_config['category']),
                function=tool_func,
                class_name=tool_config.get('class'),
                api_key_required=tool_config.get('api_key_required'),
                enabled=tool_config.get('enabled', True),
                examples=tool_config.get('examples', []),
                dependencies=tool_config.get('dependencies', []),
                retry_config=tool_config.get('retry_config', {})
            )
            
            # Store tool info
            self._tools[tool_id] = tool_info
            
            # Initialize usage stats
            self._usage_stats[tool_id] = {
                "invocations": 0,
                "success_count": 0,
                "error_count": 0,
                "last_used": None,
                "average_execution_time": 0.0,
                "total_execution_time": 0.0
            }
            
        except Exception as e:
            self._validation_errors.append(f"Error registering tool {tool_id}: {e}")
            print(f"Error registering tool {tool_id}: {e}")
    
    def _validate_tool_availability(self):
        """Validate that all registered tools are properly configured"""
        for tool_id, tool_info in self._tools.items():
            # Check if function is callable
            if not callable(tool_info.function):
                self._validation_errors.append(f"Tool {tool_id} function is not callable")
            
            # Check if required API keys are available
            if tool_info.api_key_required:
                settings = get_settings()
                api_key_map = {
                    'alpha_vantage': settings.alpha_vantage_api_key,
                    'fred': settings.fred_api_key,
                    'openai': settings.openai_api_key,
                    'google': settings.google_api_key
                }
                
                if not api_key_map.get(tool_info.api_key_required):
                    self._validation_warnings.append(
                        f"Tool {tool_id} requires API key '{tool_info.api_key_required}' which is not configured"
                    )
    
    def validate_tool_availability(self, tool_names: List[str]) -> Dict[str, str]:
        """Validate that all requested tools are available"""
        validation_results = {}
        
        for tool_name in tool_names:
            if tool_name not in self._tools:
                validation_results[tool_name] = "not_found"
            elif not self._tools[tool_name].enabled:
                validation_results[tool_name] = "disabled"
            else:
                # Check if API key is available
                tool_info = self._tools[tool_name]
                if tool_info.api_key_required:
                    settings = get_settings()
                    api_key_map = {
                        'alpha_vantage': settings.alpha_vantage_api_key,
                        'fred': settings.fred_api_key,
                        'openai': settings.openai_api_key,
                        'google': settings.google_api_key
                    }
                    
                    if not api_key_map.get(tool_info.api_key_required):
                        validation_results[tool_name] = "api_key_missing"
                    else:
                        validation_results[tool_name] = "available"
                else:
                    validation_results[tool_name] = "available"
        
        return validation_results
    
    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool configuration from YAML"""
        if 'tools' in self._config and tool_name in self._config['tools']:
            return self._config['tools'][tool_name]
        return None
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name"""
        if name in self._tools:
            return self._tools[name].function
        return None
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool exists and is enabled"""
        return name in self._tools and self._tools[name].enabled
    
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get all tools in a category"""
        return [
            name for name, info in self._tools.items()
            if info.category == category and info.enabled
        ]
    
    def get_all_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        return {name: info.function for name, info in self._tools.items() if info.enabled}
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools (alias for get_all_tools for compatibility)"""
        return self.get_all_tools()
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool descriptions"""
        return {name: info.description for name, info in self._tools.items() if info.enabled}
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed tool information"""
        if tool_name not in self._tools:
            return None
        
        tool_info = self._tools[tool_name]
        return {
            "name": tool_info.name,
            "description": tool_info.description,
            "category": tool_info.category.value,
            "enabled": tool_info.enabled,
            "api_key_required": tool_info.api_key_required,
            "examples": tool_info.examples or [],
            "dependencies": tool_info.dependencies or [],
            "retry_config": tool_info.retry_config or {},
            "usage_stats": self._usage_stats.get(tool_name, {})
        }
    
    def get_all_tool_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information for all tools"""
        return {
            name: self.get_tool_info(name) 
            for name in self._tools.keys()
        }
    
    def track_usage(self, tool_name: str, success: bool, execution_time: float = 0.0):
        """Track tool usage with execution time"""
        if tool_name in self._usage_stats:
            stats = self._usage_stats[tool_name]
            stats["invocations"] += 1
            stats["last_used"] = datetime.now().isoformat()
            stats["total_execution_time"] += execution_time
            
            if success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1
            
            # Calculate average execution time
            if stats["invocations"] > 0:
                stats["average_execution_time"] = stats["total_execution_time"] / stats["invocations"]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self._usage_stats.copy()
    
    def get_tool_analytics(self) -> Dict[str, Any]:
        """Get tool analytics (alias for get_usage_stats for compatibility)"""
        return self.get_usage_stats()
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the tool configuration"""
        return {
            "total_tools": len(self._tools),
            "enabled_tools": len([t for t in self._tools.values() if t.enabled]),
            "categories": list(set(t.category.value for t in self._tools.values())),
            "api_keys_required": list(set(t.api_key_required for t in self._tools.values() if t.api_key_required)),
            "validation_errors": len(self._validation_errors),
            "validation_warnings": len(self._validation_warnings)
        }
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get validation status of the tool registry"""
        return {
            "valid": len(self._validation_errors) == 0,
            "errors": self._validation_errors,
            "warnings": self._validation_warnings,
            "total_tools": len(self._tools),
            "enabled_tools": len([t for t in self._tools.values() if t.enabled])
        }

# Singleton instance
_tool_registry_instance = None

def get_tool_registry() -> UnifiedToolRegistry:
    """Get singleton tool registry instance"""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = UnifiedToolRegistry()
    return _tool_registry_instance