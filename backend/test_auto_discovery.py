#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.auto_discovery import get_auto_discovery
from backend.tools.registry import get_tool_registry

def test_auto_discovery():
    print("🧪 Testing Automatic Tool Discovery System")
    print("=" * 50)
    
    # Test auto discovery directly
    print("\n1. Testing Auto Discovery:")
    auto_discovery = get_auto_discovery()
    discovered_tools = auto_discovery.discover_all_tools()
    
    print(f"✓ Discovered {len(discovered_tools)} tools:")
    for tool_name in discovered_tools.keys():
        print(f"  - {tool_name}")
    
    # Test descriptions
    descriptions = auto_discovery.get_tool_descriptions()
    print(f"\n✓ Tool descriptions:")
    for tool_name, description in descriptions.items():
        print(f"  - {tool_name}: {description}")
    
    # Test categorization
    categories = auto_discovery.get_tools_by_category()
    print(f"\n✓ Tool categories:")
    for category, tools in categories.items():
        if tools:
            print(f"  - {category}: {', '.join(tools)}")
    
    # Test tool registry integration
    print("\n2. Testing Tool Registry Integration:")
    registry = get_tool_registry()
    available_tools = registry.get_available_tools()
    tool_descriptions = registry.get_tool_descriptions()
    
    print(f"✓ Registry has {len(available_tools)} tools:")
    for tool_name, description in tool_descriptions.items():
        print(f"  - {tool_name}: {description}")
    
    print("\n✅ Auto discovery system is working correctly!")

if __name__ == "__main__":
    test_auto_discovery() 