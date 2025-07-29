#!/usr/bin/env python3
"""
Debug script to test tool instance setting
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test 1: Basic global variable setting
print("=== Test 1: Basic global variable setting ===")
_tool_instances = {}

def set_tool_instances(instances):
    global _tool_instances
    _tool_instances = instances
    print(f"Inside function: {_tool_instances}")

print(f"Before: {_tool_instances}")
set_tool_instances({'test': 'value'})
print(f"After: {_tool_instances}")

# Test 2: Import and test the actual module
print("\n=== Test 2: Testing actual builtin_tools module ===")
try:
    from backend.tools.builtin_tools import set_tool_instances, _tool_instances
    print(f"Initial _tool_instances: {_tool_instances}")
    
    # Try to set instances
    set_tool_instances({'market_data': 'test_instance'})
    print(f"After set_tool_instances: {_tool_instances}")
    
    # Check if the function actually modified the global
    from backend.tools.builtin_tools import _tool_instances as check_instances
    print(f"Re-imported _tool_instances: {check_instances}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check if ControlFlow decorator affects globals
print("\n=== Test 3: Testing ControlFlow decorator impact ===")
try:
    import controlflow as cf
    
    # Create a simple decorated function
    @cf.tool
    def test_function():
        global _tool_instances
        print(f"Inside decorated function: {_tool_instances}")
        return _tool_instances
    
    # Test if the decorator affects global access
    _tool_instances = {'decorated_test': 'value'}
    result = test_function()
    print(f"Result from decorated function: {result}")
    
except Exception as e:
    print(f"Error with ControlFlow: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check the actual tool functions
print("\n=== Test 4: Testing actual tool functions ===")
try:
    from backend.tools.builtin_tools import get_market_data
    
    # Check if the tool can access instances
    result = get_market_data("GOOG")
    print(f"get_market_data result: {result}")
    
except Exception as e:
    print(f"Error testing tool function: {e}")
    import traceback
    traceback.print_exc() 