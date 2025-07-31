# JSON Tool Retry Testing Scenario

## Test Query
Use this query to test the agent retry capabilities:

```
"Analyze the market data for AAPL and provide the results in JSON format for further processing"
```

## Expected Agent Behavior

### 1. Initial Attempt
The agent will likely try to call the JSON tool with market data in a non-JSON format, such as:
- A simple string: `"AAPL market data"`
- A list: `["AAPL", "market", "data"]`
- An improperly formatted string: `AAPL market data`

### 2. Error Response
The JSON tool will return an error with:
- Clear error message explaining what format was received vs expected
- Specific suggestions for how to convert the data
- Example of correct JSON format

### 3. Retry Attempt
The agent should:
- Analyze the error message
- Understand the format requirements
- Convert the data to proper JSON format
- Retry with something like: `{"ticker": "AAPL", "data_type": "market_data"}`

### 4. Success
The tool will return success with retry information showing:
- Number of attempts made
- Previous failed formats
- Previous error messages

## What to Look For in the Report

### 🔄 Retry Analysis Section
The final report should include a new section showing:
- Which agent performed the retry
- What tool was used
- Total number of attempts
- Failed formats that were tried
- Error messages received
- Final input that succeeded
- Final status (Success/Failed)

### Tool Call Details
In the workflow visualization, you should see:
- Tool calls with attempt numbers
- Retry information in tool outputs
- Error messages and recovery strategies

## Testing Different Scenarios

### Scenario 1: Market Analysis with JSON
Query: "Get market data for GOOGL in JSON format"
Expected: Agent tries to format market data as JSON

### Scenario 2: Economic Data with JSON
Query: "Provide economic indicators in JSON format for analysis"
Expected: Agent tries to format economic data as JSON

### Scenario 3: Mixed Data Types
Query: "Analyze both market and economic data and provide results in structured JSON format"
Expected: Agent attempts to combine multiple data sources into JSON

## Implementation Details

The implementation includes:
1. **JSON-only tool** that strictly validates input format
2. **Enhanced error messages** with conversion suggestions
3. **Retry tracking** with attempt counting and error history
4. **Observability integration** to capture retry events
5. **Report enhancement** to show retry analysis
6. **Agent instructions** updated to handle format errors

## Files Modified
- `backend/tools/data_format_tools.py` - New JSON-only tool
- `backend/tools/registry.py` - Tool registration
- `backend/config/agents.yaml` - Agent retry instructions
- `backend/utils/observability.py` - Retry event tracking
- `backend/workflows/dependency_workflow.py` - Retry analysis in reports
- `backend/agents.py` - Tool integration

## Running the Test
1. Start the backend server
2. Use the test query in the frontend
3. Watch the workflow visualization for retry attempts
4. Check the final report for the "🔄 Retry Analysis" section 