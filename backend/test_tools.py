import controlflow as cf

@cf.tool
def test_tool(message: str) -> str:
    """A simple test tool"""
    return f"Test: {message}"

if __name__ == "__main__":
    import inspect
    for name, func in inspect.getmembers(__import__(__name__), inspect.isfunction):
        if func.__module__ == __name__:
            print(f'Tool found: {name}')
