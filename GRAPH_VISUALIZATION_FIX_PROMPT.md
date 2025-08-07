# Graph Visualization Fix Prompt

## Problem Description

The workflow graph visualization in the frontend is currently displaying:
```
📊
No Workflow Data
Waiting for workflow execution...
Debug: 0 nodes, 0 edges
```

However, the workflow execution is completing successfully and generating reports. The issue is that the graph visualization is not receiving or processing the nodes and edges data properly.

## System Architecture Context

### Frontend Components
- **WorkflowCanvas.tsx**: Main visualization component using React Flow
- **workflowStore.ts**: Zustand store managing workflow state (nodes, edges, status)
- **useWorkflowStatus.ts**: Hook that polls backend for workflow status updates
- **App.tsx**: Main component that renders WorkflowCanvas with nodes/edges from store

### Backend Components
- **config_driven_workflow.py**: Generates workflow graph via `_generate_workflow_graph()` method
- **app.py**: API endpoints for workflow status (`/api/workflow-status/<workflow_id>`)
- **base.py**: Base workflow class with status management

### Data Flow
1. Backend workflow generates nodes/edges in `_generate_workflow_graph()`
2. Status updates sent via `_update_status()` method with `nodes` and `edges` fields
3. Frontend polls `/api/workflow-status/<workflow_id>` every 2 seconds
4. `useWorkflowStatus` hook calls `updateWorkflowStatus()` on store
5. Store processes nodes/edges and calls `layoutNodes()` for positioning
6. WorkflowCanvas receives nodes/edges as props and renders React Flow graph

## Key Code Sections

### Backend Graph Generation
```python
# backend/workflows/config_driven_workflow.py:420-492
def _generate_workflow_graph(self) -> Dict[str, List[Dict[str, Any]]]:
    """Dynamically generate workflow nodes and edges for frontend visualization."""
    nodes, edges = [], []
    agent_configs = self.workflow_config.get('agents', [])
    current_task = self.execution_context.get('current_task')
    workflow_status = self.execution_context.get('status', 'initializing')

    if not agent_configs:
        return {"nodes": [], "edges": []}

    # Creates nodes for: input, agent tasks, synthesis, output
    # Creates edges connecting them in sequence
    return {"nodes": nodes, "edges": edges}
```

### Backend Status Updates
```python
# backend/workflows/config_driven_workflow.py:120-159
def _update_status(self, update: Dict[str, Any]):
    # Generate workflow graph for frontend visualization
    try:
        workflow_graph = self._generate_workflow_graph()
        update['nodes'] = workflow_graph['nodes']
        update['edges'] = workflow_graph['edges']
        update['hasNodes'] = True if workflow_graph['nodes'] else False
    except Exception as e:
        logger.error(f"Error generating workflow graph: {e}", exc_info=True)
        update['nodes'] = []
        update['edges'] = []
        update['hasNodes'] = False
```

### Frontend Store Processing
```typescript
// frontend/src/stores/workflowStore.ts:194-283
updateWorkflowStatus: (update) => {
  // Handle graph updates - backend returns nodes and edges directly
  if (update.nodes && update.edges) {
    // If the store has no nodes yet, this is the initial graph. Layout and set.
    if (state.nodes.length === 0) {
      get().layoutNodes(update.nodes, update.edges);
    } else {
      // Otherwise, merge status updates into existing nodes.
      // ... merge logic
    }
  }
}
```

### Frontend Canvas Rendering
```typescript
// frontend/src/components/WorkflowCanvas.tsx:200-250
{nodes.length === 0 ? (
  <div className="flex items-center justify-center h-full bg-brand-bg text-brand-text-secondary">
    <div className="text-center">
      <div className="text-2xl mb-2">📊</div>
      <div className="text-lg font-semibold mb-2">No Workflow Data</div>
      <div className="text-sm">Waiting for workflow execution...</div>
      <div className="text-xs mt-2 text-brand-text-tertiary">
        Debug: {nodes.length} nodes, {edges.length} edges
      </div>
    </div>
  </div>
) : (
  <ReactFlow
    nodes={nodes}
    edges={edges}
    // ... other props
  />
)}
```

## Potential Issues to Investigate

### 1. Backend Graph Generation
- **Agent Config Loading**: Check if `self.workflow_config.get('agents', [])` is returning empty
- **Execution Context**: Verify `self.execution_context` has proper data
- **Exception Handling**: The `_generate_workflow_graph()` might be throwing exceptions
- **Workflow Config**: Ensure workflow configuration is properly loaded

### 2. Status Update Flow
- **Callback Registration**: Verify status callbacks are properly registered
- **Update Frequency**: Check if `_update_status()` is being called during execution
- **Data Structure**: Ensure nodes/edges have correct React Flow format

### 3. Frontend Data Processing
- **API Response**: Verify `/api/workflow-status/<workflow_id>` returns nodes/edges
- **Store Updates**: Check if `updateWorkflowStatus` is receiving the data
- **Layout Function**: Ensure `layoutNodes()` is working correctly
- **State Management**: Verify Zustand store is properly updating

### 4. React Flow Integration
- **Node Types**: Check if custom node types are properly registered
- **Edge Types**: Verify edge types are correctly configured
- **Data Format**: Ensure node/edge data matches React Flow expectations

## Debugging Steps

### 1. Backend Logging
Add comprehensive logging to track:
- Workflow config loading
- Graph generation process
- Status update calls
- API response data

### 2. Frontend Logging
Check browser console for:
- API response data
- Store state updates
- React Flow warnings/errors
- Component re-renders

### 3. Network Inspection
- Monitor `/api/workflow-status/<workflow_id>` responses
- Verify nodes/edges are in the response
- Check for any API errors

### 4. State Inspection
- Use React DevTools to inspect Zustand store state
- Check if nodes/edges are being set in the store
- Verify component props are being passed correctly

## Expected Data Structure

### Backend Node Format
```python
{
    "id": "task_market_analysis",
    "type": "task",
    "position": {"x": 280, "y": 100},
    "data": {
        "label": "Market Analysis",
        "status": "running",
        "description": "Analyzing market data...",
        "agentName": "Market Analyst",
        "tools": ["get_stock_price", "get_company_info"],
        "liveDetails": {...}  # if running
    }
}
```

### Backend Edge Format
```python
{
    "id": "edge_input_to_task_market_analysis",
    "source": "input",
    "target": "task_market_analysis",
    "type": "depends_on"
}
```

### Frontend Expected Format
```typescript
// CustomNode interface
interface CustomNode extends Node {
  data: {
    label: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    description?: string;
    agentName?: string;
    tools?: string[];
    liveDetails?: any;
    result?: any;
    error?: any;
  };
}

// Edge interface
interface Edge {
  id: string;
  source: string;
  target: string;
  type: string;
}
```

## Questions to Answer

1. **Is the workflow configuration being loaded correctly?** Check if `agent_configs` is empty in `_generate_workflow_graph()`

2. **Are status updates being sent during execution?** Verify `_update_status()` is called with nodes/edges

3. **Is the API returning the correct data?** Check the actual response from `/api/workflow-status/<workflow_id>`

4. **Is the frontend store receiving the data?** Verify `updateWorkflowStatus` is called with nodes/edges

5. **Is the layout function working?** Check if `layoutNodes()` is positioning nodes correctly

6. **Are there any React Flow errors?** Look for console warnings about node types, edge types, or data format

## Recommended Fixes

### Immediate Debugging
1. Add logging to `_generate_workflow_graph()` to see if it's being called and what data it returns
2. Check the API response in browser network tab
3. Add console.log in `updateWorkflowStatus` to see if nodes/edges are received
4. Verify workflow configuration is loaded correctly

### Potential Code Fixes
1. **Backend**: Ensure `_update_status()` is called during workflow execution
2. **Backend**: Add error handling and logging to graph generation
3. **Frontend**: Add validation for nodes/edges data structure
4. **Frontend**: Ensure proper React Flow node/edge type registration

### Testing Strategy
1. Test with a simple workflow to isolate the issue
2. Add temporary hardcoded nodes/edges to verify frontend rendering
3. Check if the issue is specific to certain workflow types
4. Verify the fix works across different execution states

## Additional Context

- The project uses a modular architecture with config-driven workflows
- React Flow is used for graph visualization with custom node types
- Zustand is used for state management
- The backend uses ControlFlow patterns for task orchestration
- The system should be extremely modular for easy agent/tool swapping

Please analyze the logs provided and identify the root cause of why nodes and edges are not being generated or displayed in the frontend visualization.
