# troubleshoot_controlflow.py
import controlflow as cf
from textwrap import dedent
import inspect

def print_header(title):
    """Prints a formatted header."""
    print("\n" + "=" * 80)
    print(f"| {title.center(76)} |")
    print("=" * 80)

def inspect_module(module, module_name):
    """Prints the contents of a module."""
    print_header(f"Inspecting Module: {module_name}")
    print(f"Location: {getattr(module, '__file__', 'N/A')}")
    print("\n" + "-" * 30)
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
        if doc:
            first_line = doc.strip().split('\n')[0]  # FIXED: Changed from split('') to split('\n')
        else:
            first_line = "No docstring available."
        
        print(f"Description: {first_line}")
        print(f"Module: {cls.__module__}")
        
        print("\n" + "-" * 30)
        print("Pydantic Model Fields (if any):")
        print("-" * 30)
        if hasattr(cls, 'model_fields'):
            for name, field in cls.model_fields.items():
                # Handle different Pydantic versions
                if hasattr(field, 'annotation'):
                    field_type = field.annotation
                else:
                    field_type = field
                print(f"  - {name}: {field_type}")
        else:
            print("  Not a Pydantic model or no fields found.")

        print("\n" + "-" * 30)
        print("Attributes & Methods:")
        print("-" * 30)
        
        attributes = [attr for attr in dir(cls) if not attr.startswith('_')]
        for i in range(0, len(attributes), 3):
            print("    ".join(f"{attr:<30}" for attr in attributes[i:i+3]))

    except Exception as e:
        print(f"Could not inspect class {class_name}: {e}")
        # Add more detailed error info
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()

def verify_imports():
    """Verifies that key classes can be imported from their expected locations."""
    print_header("Verifying Key Imports")
    imports_to_check = {
        "Handler": "controlflow.orchestration.handler",
        "AgentToolCall": "controlflow.events.events",
        "EventToolResult": "controlflow.events.events", # Renamed to avoid conflict
        "NestedToolResult": "controlflow.tools.tools" # The class we need to inspect
    }
    
    results = {}
    for class_name, module_name in imports_to_check.items():
        try:
            if class_name == "NestedToolResult":
                exec(f"from {module_name} import ToolResult as {class_name}")
            elif class_name == "EventToolResult":
                exec(f"from {module_name} import ToolResult as {class_name}")
            else:
                exec(f"from {module_name} import {class_name}")
            print(f"[SUCCESS] Successfully imported '{class_name}' from '{module_name}'")
            results[class_name] = True
        except ImportError as e:
            print(f"[FAILED]  Could not import '{class_name}' from '{module_name}': {e}")
            results[class_name] = False
            
    print("\nBased on these results, you can update your code with the correct import paths.")
    return results


if __name__ == "__main__":
    print("Running ControlFlow Codebase Checks...")
    
    # 1. Verify that the key imports are working as expected
    import_results = verify_imports()
    
    # 2. Inspect the key classes, especially the nested ToolResult
    try:
        from controlflow.orchestration.handler import Handler
        inspect_class(Handler, "Handler (from orchestration.handler)")
    except ImportError as e:
        print(f"[ERROR] Could not find Handler to inspect: {e}")

    try:
        # This is the event wrapper
        from controlflow.events.events import ToolResult as EventToolResult
        inspect_class(EventToolResult, "ToolResult (Event Wrapper from events.events)")
        
        # Try to create a sample instance to see its structure
        print("\n" + "-" * 30)
        print("Attempting to understand EventToolResult structure:")
        print("-" * 30)
        try:
            sig = inspect.signature(EventToolResult)
            print(f"Constructor signature: {sig}")
        except:
            print("Could not get constructor signature")
            
    except ImportError as e:
        print(f"[ERROR] Could not import EventToolResult: {e}")

    try:
        # THIS IS THE NESTED OBJECT that is causing the error
        from controlflow.tools.tools import ToolResult as NestedToolResult
        inspect_class(NestedToolResult, "ToolResult (Nested Object from tools.tools)")
        
        # Try to understand its structure better
        print("\n" + "-" * 30)
        print("Attempting to understand NestedToolResult structure:")
        print("-" * 30)
        try:
            sig = inspect.signature(NestedToolResult)
            print(f"Constructor signature: {sig}")
        except:
            print("Could not get constructor signature")
            
    except ImportError as e:
        print(f"[ERROR] Could not find NestedToolResult: {e}")
        # Try alternative locations
        print("\nTrying alternative import locations...")
        alternative_imports = [
            "controlflow.tools",
            "controlflow.events.tools",
            "controlflow.events.base",
        ]
        for module_path in alternative_imports:
            try:
                exec(f"from {module_path} import ToolResult")
                print(f"[SUCCESS] Found ToolResult in {module_path}")
                exec(f"from {module_path} import ToolResult as AltToolResult")
                inspect_class(AltToolResult, f"ToolResult (from {module_path})")
                break
            except:
                continue
        
    print_header("Checks Complete")
    print(dedent("""
    To use this information:
    1. Look at the 'Inspecting Class: ToolResult' sections above.
    2. Find the correct attribute for the tool's name within its Pydantic fields or attributes.
    3. The attribute is likely named 'tool_name', 'name', 'tool', or similar.
    4. Update the 'on_tool_result' method in 'backend/utils/observability.py' with the correct attribute.
    
    If the nested ToolResult couldn't be found, check the EventToolResult structure instead,
    as it likely contains the nested object as an attribute.
    """))