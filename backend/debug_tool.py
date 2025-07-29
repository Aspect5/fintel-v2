#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.builtin_tools import get_market_data

def debug_tool():
    print("Debugging Tool object:")
    print(f"Type: {type(get_market_data)}")
    print(f"Class: {get_market_data.__class__}")
    print(f"Class name: {get_market_data.__class__.__name__}")
    print(f"Callable: {callable(get_market_data)}")
    print(f"Has __call__: {hasattr(get_market_data, '__call__')}")
    
    # Check for name attribute
    if hasattr(get_market_data, '__name__'):
        print(f"Has __name__: {get_market_data.__name__}")
    else:
        print("No __name__ attribute")
    
    # Check for other potential name attributes
    for attr in ['name', 'func_name', 'function_name']:
        if hasattr(get_market_data, attr):
            print(f"Has {attr}: {getattr(get_market_data, attr)}")
    
    # Check for function-related attributes
    for attr in ['fn', 'function', 'func', 'original_function']:
        if hasattr(get_market_data, attr):
            print(f"Has {attr}: {getattr(get_market_data, attr)}")
    
    # Check if it has a run method
    if hasattr(get_market_data, 'run'):
        print(f"Has run method: {get_market_data.run}")
    
    # Try to call it
    try:
        print("Trying to call the tool...")
        result = get_market_data("AAPL")
        print(f"Call successful: {result}")
    except Exception as e:
        print(f"Call failed: {e}")

if __name__ == "__main__":
    debug_tool() 