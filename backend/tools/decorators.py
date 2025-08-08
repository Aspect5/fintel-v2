from functools import wraps
import controlflow as cf
import time

def prevent_duplicate_calls(func):
    """Decorator to prevent duplicate tool calls within a task"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get current task context
        current_task = cf.get_current_task()
        if not current_task:
            return func(*args, **kwargs)
        
        # Create a unique key for this call
        call_key = f"{func.__name__}_{args}_{kwargs}"
        
        # Check if we've made this exact call before in this task
        if not hasattr(current_task, '_tool_call_history'):
            current_task._tool_call_history = set()
        
        if call_key in current_task._tool_call_history:
            return {"error": "Duplicate tool call prevented", "message": "This exact tool call has already been made"}
        
        # Record the call and execute
        current_task._tool_call_history.add(call_key)
        return func(*args, **kwargs)
    
    return wrapper

def track_tool_usage(func):
    """Decorator to track tool usage for analytics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False
        result = None
        
        try:
            # Execute the tool
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            # Tool execution failed
            success = False
            raise e
        finally:
            # Track usage regardless of success/failure
            execution_time = time.time() - start_time
            
            try:
                # Get the tool registry and track usage
                from backend.tools.registry import get_tool_registry
                registry = get_tool_registry()
                registry.track_usage(func.__name__, success, execution_time)
                
                # Also track in workflow if available
                current_task = cf.get_current_task()
                if current_task and hasattr(current_task, '_workflow'):
                    workflow = current_task._workflow
                    if hasattr(workflow, '_track_tool_usage'):
                        workflow._track_tool_usage(func.__name__, success, execution_time)
                        
            except Exception as tracking_error:
                # Don't let tracking errors affect tool execution
                print(f"Warning: Failed to track tool usage for {func.__name__}: {tracking_error}")
    
    return wrapper

def cf_tool_with_tracking(func):
    """Combined decorator: ControlFlow tool + usage tracking"""
    # Apply tracking decorator first, then ControlFlow tool decorator
    tracked_func = track_tool_usage(func)
    return cf.tool(tracked_func)
