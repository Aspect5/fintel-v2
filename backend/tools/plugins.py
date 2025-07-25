# backend/tools/plugins.py
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable, List
import controlflow as cf
from backend.tools.base import BaseTool

class ToolPlugin:
    """Base class for tool plugins"""
    
    @classmethod
    def get_tools(cls) -> Dict[str, Callable]:
        """Return a dictionary of tool_name -> tool_function"""
        raise NotImplementedError

class ToolPluginLoader:
    """Dynamically loads tool plugins from a directory"""
    
    def __init__(self, plugin_dir: Path = None):
        self.plugin_dir = plugin_dir or Path(__file__).parent / "plugins"
        self.plugins: Dict[str, ToolPlugin] = {}
        self._controlflow_tools: Dict[str, Any] = {}
    
    def load_plugins(self) -> None:
        """Load all tool plugins from the plugin directory"""
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True)
            return
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            module_name = f"backend.tools.plugins.{plugin_file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Find all ToolPlugin subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ToolPlugin) and 
                        obj != ToolPlugin):
                        plugin_instance = obj()
                        self.plugins[name] = plugin_instance
                        
                        # Convert to ControlFlow tools
                        tools = plugin_instance.get_tools()
                        for tool_name, tool_func in tools.items():
                            cf_tool = cf.tool(tool_func)
                            self._controlflow_tools[tool_name] = cf_tool
                            
            except Exception as e:
                print(f"Failed to load plugin {plugin_file}: {e}")
    
    def get_tools_for_agent(self, tool_names: List[str]) -> List[Any]:
        """Get ControlFlow tool objects for specified tool names"""
        tools = []
        for name in tool_names:
            if name in self._controlflow_tools:
                tools.append(self._controlflow_tools[name])
        return tools
    
    def get_all_tool_names(self) -> List[str]:
        """Get all available tool names"""
        return list(self._controlflow_tools.keys())