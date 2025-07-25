# troubleshoot_controlflow.py
import controlflow as cf
from textwrap import dedent
import inspect

def print_header(title):
    """Prints a formatted header."""
    print("" + "=" * 80)
    print(f"| {title.center(76)} |")
    print("=" * 80)

def inspect_module(module, module_name):
    """Prints the contents of a module."""
    print_header(f"Inspecting Module: {module_name}")
    print(f"Location: {getattr(module, '__file__', 'N/A')}")
    print("" + "-" * 30)
    print("Available Attributes:")
    print("-" * 30)
    
    attributes = [attr for attr in dir(module) if not attr.startswith('_')]
    for i in range(0, len(attributes), 4):
        print("    ".join(f"{attr:<25}" for attr in attributes[i:i+4]))
        
def inspect_class(cls, class_name):
    """Prints details of a class."""
    print_header(f"Inspecting Class: {class_name}")
    
    try:
        # Get the first line of the docstring
        doc = inspect.getdoc(cls)
        first_line = doc.split('')[0] if doc else "No docstring available."
        
        print(f"Description: {first_line}")
        print(f"Module: {cls.__module__}")
        
        print("" + "-" * 30)
        print("Methods & Properties:")
        print("-" * 30)
        
        attributes = [attr for attr in dir(cls) if not attr.startswith('_')]
        for i in range(0, len(attributes), 3):
            print("    ".join(f"{attr:<30}" for attr in attributes[i:i+3]))

    except Exception as e:
        print(f"Could not inspect class {class_name}: {e}")

def verify_imports():
    """Verifies that key classes can be imported from their expected locations."""
    print_header("Verifying Key Imports")
    imports_to_check = {
        "Handler": "controlflow.orchestration.handler",
        "AgentToolCall": "controlflow.events.events",
    }
    
    for class_name, module_name in imports_to_check.items():
        try:
            exec(f"from {module_name} import {class_name}")
            print(f"[SUCCESS] Successfully imported '{class_name}' from '{module_name}'")
        except ImportError as e:
            print(f"[FAILED]  Could not import '{class_name}' from '{module_name}': {e}")
            
    print("Based on these results, you can update your code with the correct import paths.")


if __name__ == "__main__":
    print("Running ControlFlow Codebase Checks...")
    
    # 1. Verify that the key imports are working as expected
    verify_imports()
    
    # 2. Inspect the main controlflow module
    inspect_module(cf, "controlflow")
    
    # 3. Inspect key sub-modules that have caused issues
    inspect_module(cf.events, "controlflow.events")
    inspect_module(cf.orchestration, "controlflow.orchestration")
    
    # 4. Inspect key classes
    try:
        from controlflow.orchestration.handler import Handler
        inspect_class(Handler, "Handler")
    except ImportError:
        print("[ERROR] Could not find Handler to inspect.")

    try:
        from controlflow.events.events import AgentToolCall
        inspect_class(AgentToolCall, "AgentToolCall")
    except ImportError:
        print("[ERROR] Could not find AgentToolCall to inspect.")
        
    print_header("Checks Complete")
    print(dedent("""
    To use this information:
    1. Look at the 'Verifying Key Imports' section to confirm the correct import paths.
    2. Use the module and class inspection details to explore other available features.
    3. Update your application code with the correct imports to fix any 'AttributeError' issues.
    """))
