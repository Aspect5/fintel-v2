#!/usr/bin/env python3
"""
Automatic Tool Discovery System

This module provides automatic discovery of tools from various sources:
1. Built-in tools in the tools directory
2. Plugin tools in the plugins directory
3. Any Python modules that contain @cf.tool decorated functions

The system automatically extracts tool descriptions from docstrings and
provides a unified interface for tool registration.
"""

import os
import sys
import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional, Tuple
import controlflow as cf

class AutoToolDiscovery:
    """Automatic tool discovery and registration system"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent
        self.discovered_tools: Dict[str, Any] = {}
        self.tool_descriptions: Dict[str, str] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        
    def discover_all_tools(self) -> Dict[str, Any]:
        """Discover all available tools from all sources"""
        self.discovered_tools.clear()
        self.tool_descriptions.clear()
        self.tool_metadata.clear()
        
        # Discover built-in tools
        self._discover_builtin_tools()
        
        # Discover plugin tools
        self._discover_plugin_tools()
        
        # Discover tools from any other Python modules
        self._discover_module_tools()
        
        return self.discovered_tools.copy()
    
    def _discover_builtin_tools(self):
        """Discover tools from built-in tool modules"""
        builtin_modules = [
            'builtin_tools',  # Main built-in tools module
            'market_data',
            'economic_data',
            'data_tools'
        ]
        
        for module_name in builtin_modules:
            try:
                module_path = self.base_path / f"{module_name}.py"
                if module_path.exists():
                    self._scan_module_for_tools(module_path, f"backend.tools.{module_name}")
            except Exception as e:
                print(f"Warning: Failed to scan builtin module {module_name}: {e}")
    
    def _discover_plugin_tools(self):
        """Discover tools from plugin modules"""
        plugin_dir = self.base_path / "plugins"
        if not plugin_dir.exists():
            return
        
        # Scan for plugin modules
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                module_name = f"backend.tools.plugins.{plugin_file.stem}"
                self._scan_module_for_tools(plugin_file, module_name)
            except Exception as e:
                print(f"Warning: Failed to scan plugin {plugin_file.name}: {e}")
    
    def _discover_module_tools(self):
        """Discover tools from any Python modules in the project"""
        # This could be extended to scan other directories
        # For now, we'll focus on the tools directory
        pass
    
    def _scan_module_for_tools(self, file_path: Path, module_name: str):
        """Scan a Python module for tools and extract metadata"""
        try:
            print(f"Scanning module: {module_name} at {file_path}")
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                print(f"Failed to create spec for {module_name}")
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Scan for tools in the module
            for name, obj in inspect.getmembers(module):
                is_tool = self._is_tool_function(obj)
                if is_tool:
                    tool_name = self._extract_tool_name(obj, name)
                    description = self._extract_tool_description(obj)
                    metadata = self._extract_tool_metadata(obj)
                    
                    # Register the tool
                    self.discovered_tools[tool_name] = obj
                    self.tool_descriptions[tool_name] = description
                    self.tool_metadata[tool_name] = metadata
                    
                    print(f"✓ Discovered tool: {tool_name} - {description}")
                
                # Also check for ToolPlugin classes and scan their static methods
                if inspect.isclass(obj) and hasattr(obj, 'get_tools'):
                    print(f"Found ToolPlugin class: {name}")
                    try:
                        # Get the tools from the plugin
                        tools_dict = obj.get_tools()
                        for tool_name, tool_func in tools_dict.items():
                            if self._is_tool_function(tool_func):
                                description = self._extract_tool_description(tool_func)
                                metadata = self._extract_tool_metadata(tool_func)
                                
                                # Register the tool
                                self.discovered_tools[tool_name] = tool_func
                                self.tool_descriptions[tool_name] = description
                                self.tool_metadata[tool_name] = metadata
                                
                                print(f"✓ Discovered plugin tool: {tool_name} - {description}")
                    except Exception as e:
                        print(f"Error scanning plugin class {name}: {e}")
                    
        except Exception as e:
            print(f"Error scanning module {module_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _is_tool_function(self, obj: Any) -> bool:
        """Check if an object is a tool function"""
        # Check if it's a ControlFlow Tool object first (these are not callable but are tools)
        if obj.__class__.__name__ == 'Tool':
            return True
        
        # Must be callable for other objects
        if not callable(obj):
            return False
        
        # Must have a name (either __name__ or name attribute)
        if not hasattr(obj, '__name__') and not hasattr(obj, 'name'):
            return False
        
        # Get the name for debugging
        obj_name = getattr(obj, '__name__', getattr(obj, 'name', 'unknown'))
        
        # Skip if it's a class, method, or builtin
        if inspect.isclass(obj) or inspect.ismethod(obj) or inspect.isbuiltin(obj):
            return False
        
        # Skip if it's a module or package
        if inspect.ismodule(obj):
            return False
        
        # Get the name for checking
        obj_name = getattr(obj, '__name__', getattr(obj, 'name', ''))
        
        # Skip internal/private functions
        if obj_name.startswith('_'):
            return False
        
        # Skip the tool decorator itself
        if obj_name == 'tool':
            return False
        
        # Check if it's already a ControlFlow Tool object
        if hasattr(obj, '_controlflow_tool'):
            return True
        
        # Check if it's a function with a docstring that looks like a tool
        if inspect.isfunction(obj) and obj.__doc__:
            doc = obj.__doc__.lower()
            # Look for specific tool patterns
            tool_keywords = ['get', 'analyze', 'calculate', 'process', 'fetch', 'retrieve']
            if any(keyword in doc for keyword in tool_keywords):
                return True
        
        # Check if it's a static method (common in plugin classes)
        if inspect.isfunction(obj) and hasattr(obj, '__qualname__'):
            # Static methods from classes should be considered tools if they have docstrings
            if obj.__doc__ and any(keyword in obj.__doc__.lower() for keyword in tool_keywords):
                return True
        
        # Check if it's a static method from a class (plugin tools)
        if inspect.isfunction(obj):
            # Check if it's a static method by looking at the qualname
            if hasattr(obj, '__qualname__') and '.' in obj.__qualname__:
                class_name, method_name = obj.__qualname__.rsplit('.', 1)
                # If it's a static method with a docstring, consider it a tool
                if obj.__doc__ and method_name in ['calculate_pe_ratio', 'analyze_cash_flow', 'get_competitor_analysis']:
                    return True
        
        return False
    
    def _extract_tool_name(self, obj: Callable, default_name: str) -> str:
        """Extract the tool name from a function"""
        # Try to get name from controlflow tool
        if hasattr(obj, '_controlflow_tool') and hasattr(obj._controlflow_tool, 'name'):
            return obj._controlflow_tool.name
        
        # Check if it's a Tool object
        if obj.__class__.__name__ == 'Tool':
            return obj.name if hasattr(obj, 'name') else default_name
        
        # Use the function name
        return default_name
    
    def _extract_tool_description(self, obj: Callable) -> Dict[str, Any]:
        """Extract structured tool description from docstring"""
        # Check if it's a Tool object with description
        if obj.__class__.__name__ == 'Tool' and hasattr(obj, 'description'):
            return {
                'summary': obj.description,
                'details': {
                    'args': {},
                    'returns': 'Unknown',
                    'examples': []
                }
            }
        
        if not obj.__doc__:
            return {
                'summary': "No description available",
                'details': {
                    'args': {},
                    'returns': 'Unknown',
                    'examples': []
                }
            }
        
        # Parse the full docstring
        doc_lines = obj.__doc__.strip().split('\n')
        
        # Extract summary (first line)
        summary = doc_lines[0].strip()
        if summary.startswith('"""') or summary.startswith("'''"):
            summary = summary[3:]
        if summary.endswith('"""') or summary.endswith("'''"):
            summary = summary[:-3]
        summary = summary.strip()
        
        # Parse Args section
        args = {}
        returns = "Unknown"
        examples = []
        
        in_args = False
        in_returns = False
        in_examples = False
        current_arg = None
        
        for line in doc_lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if line.lower().startswith('args:'):
                in_args = True
                in_returns = False
                in_examples = False
                continue
            elif line.lower().startswith('returns:'):
                in_args = False
                in_returns = True
                in_examples = False
                continue
            elif line.lower().startswith('examples:'):
                in_args = False
                in_returns = False
                in_examples = True
                continue
            elif line.startswith('---') or line.startswith('==='):
                in_args = False
                in_returns = False
                in_examples = False
                continue
            
            # Parse Args section
            if in_args and line.startswith('    '):
                # This might be an argument description
                if current_arg:
                    args[current_arg]['description'] = line.strip()
                continue
            elif in_args and ':' in line and not line.startswith('    '):
                # This is likely an argument definition
                parts = line.split(':', 1)
                if len(parts) == 2:
                    arg_name = parts[0].strip()
                    arg_desc = parts[1].strip()
                    args[arg_name] = {
                        'type': 'Any',
                        'description': arg_desc,
                        'required': True
                    }
                    current_arg = arg_name
            
            # Parse Returns section
            elif in_returns:
                returns = line
            
            # Parse Examples section
            elif in_examples:
                if line.startswith('    '):
                    examples.append(line.strip())
        
        # Try to extract arguments from function signature if not found in docstring
        if not args:
            try:
                sig = inspect.signature(obj)
                for param_name, param in sig.parameters.items():
                    if param_name != 'self':  # Skip self parameter
                        args[param_name] = {
                            'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                            'description': f'Parameter {param_name}',
                            'required': param.default == inspect.Parameter.empty
                        }
            except:
                pass
        
        return {
            'summary': summary,
            'details': {
                'args': args,
                'returns': returns,
                'examples': examples
            }
        }
    
    def _extract_tool_metadata(self, obj: Callable) -> Dict[str, Any]:
        """Extract additional metadata from tool function"""
        # Handle Tool objects that don't have __name__
        if obj.__class__.__name__ == 'Tool':
            metadata = {
                'function_name': getattr(obj, 'name', 'unknown'),
                'module': getattr(obj, '__module__', 'unknown'),
                'signature': 'Tool object',
                'has_docstring': bool(getattr(obj, 'description', None)),
            }
        else:
            metadata = {
                'function_name': obj.__name__,
                'module': obj.__module__,
                'signature': str(inspect.signature(obj)),
                'has_docstring': bool(obj.__doc__),
            }
        
        # Extract parameter information
        if obj.__class__.__name__ == 'Tool':
            # For Tool objects, try to get parameters from the underlying function
            if hasattr(obj, 'fn'):
                try:
                    sig = inspect.signature(obj.fn)
                    metadata['parameters'] = {}
                    for param_name, param in sig.parameters.items():
                        metadata['parameters'][param_name] = {
                            'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                            'default': param.default if param.default != inspect.Parameter.empty else None,
                            'required': param.default == inspect.Parameter.empty
                        }
                except:
                    metadata['parameters'] = {}
            else:
                metadata['parameters'] = {}
        else:
            sig = inspect.signature(obj)
            metadata['parameters'] = {}
            for param_name, param in sig.parameters.items():
                metadata['parameters'][param_name] = {
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'default': param.default if param.default != inspect.Parameter.empty else None,
                    'required': param.default == inspect.Parameter.empty
                }
        
        return metadata
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get all tool descriptions"""
        return self.tool_descriptions.copy()
    
    def get_tool_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool metadata"""
        return self.tool_metadata.copy()
    
    def get_tools_by_category(self) -> Dict[str, List[str]]:
        """Categorize tools based on their names and descriptions"""
        categories = {
            'market_data': [],
            'economic_data': [],
            'analysis': [],
            'data_processing': [],
            'custom': []
        }
        
        for tool_name, description in self.tool_descriptions.items():
            description_lower = description.lower()
            tool_name_lower = tool_name.lower()
            
            if any(keyword in tool_name_lower or keyword in description_lower 
                   for keyword in ['market', 'stock', 'price', 'trading', 'company']):
                categories['market_data'].append(tool_name)
            elif any(keyword in tool_name_lower or keyword in description_lower 
                     for keyword in ['economic', 'gdp', 'inflation', 'rates', 'fred']):
                categories['economic_data'].append(tool_name)
            elif any(keyword in tool_name_lower or keyword in description_lower 
                     for keyword in ['analyze', 'calculate', 'ratio', 'flow', 'competitor']):
                categories['analysis'].append(tool_name)
            elif any(keyword in tool_name_lower or keyword in description_lower 
                     for keyword in ['process', 'data', 'json', 'format']):
                categories['data_processing'].append(tool_name)
            else:
                categories['custom'].append(tool_name)
        
        return categories
    
    def reload_tools(self):
        """Reload all tools (useful for development)"""
        return self.discover_all_tools()


# Global instance for easy access
_auto_discovery_instance = None

def get_auto_discovery() -> AutoToolDiscovery:
    """Get the global auto discovery instance"""
    global _auto_discovery_instance
    if _auto_discovery_instance is None:
        _auto_discovery_instance = AutoToolDiscovery()
    return _auto_discovery_instance 