# backend/agents/tools/data_tools.py

from controlflow.tools.tools import tool
import json

@tool
def process_strict_json(data: dict):
    """
    Processes a dictionary of financial data.
    IMPORTANT: This tool ONLY accepts a valid Python dictionary (JSON object).
    It will fail if you pass it a plain string. You must parse strings into a dictionary first.
    
    For example:
    - CORRECT: process_strict_json(data={"asset": "BTC", "value": 70000})
    - INCORRECT: process_strict_json(data='{"asset": "BTC", "value": 70000}')
    """
    if not isinstance(data, dict):
        raise TypeError(f"Invalid input type: Expected dict, but got {type(data).__name__}. You must parse the input into a dictionary.")
    
    # Simulate some processing
    data['status'] = 'processed'
    return f"Successfully processed JSON data. Status: {data.get('status')}, Items: {len(data)}."
