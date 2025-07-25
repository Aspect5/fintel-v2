from functools import wraps
import controlflow as cf

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
