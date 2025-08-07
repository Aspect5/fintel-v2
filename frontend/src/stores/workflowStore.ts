// frontend/src/stores/workflowStore.ts
import { create } from 'zustand';
import {
  Edge, OnNodesChange, OnEdgesChange, applyNodeChanges, applyEdgeChanges,
} from 'reactflow';
import {
  WorkflowStatus, CustomNode, PersistedWorkflowStatus,
} from '../types';
import { createLogger } from '../utils/logger';

const storeLogger = createLogger('WorkflowStore');

// This represents the comprehensive status object received from the backend.
export interface FullWorkflowStatus extends WorkflowStatus, PersistedWorkflowStatus {}

export interface WorkflowState {
  nodes: CustomNode[];
  edges: Edge[];
  status: 'idle' | 'running' | 'completed' | 'failed' | 'initializing';
  result: any; // Changed from string | null to any to handle complex objects
  workflowId: string | null;
  query: string | null;
  executionTime: number;
  error: string | null;
  
  // Add missing properties that components are trying to access
  trace?: any;
  current_task?: string;
  agent_invocations?: any[];
  tool_calls?: any[];
  enhanced_result?: any;
  event_history?: any[];

  // Actions
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  startWorkflow: (workflowId: string, query: string, initialStatus: FullWorkflowStatus) => void;
  updateWorkflowStatus: (statusUpdate: Partial<FullWorkflowStatus>) => void;
  resetWorkflow: () => void;
  setPollingWorkflow: (workflowId: string) => void;
  layoutNodes: (nodes: CustomNode[], edges: Edge[]) => void; // New action for layout
}

const initialState = {
  nodes: [],
  edges: [],
  status: 'idle' as const,
  result: null,
  workflowId: null,
  query: null,
  executionTime: 0,
  error: null,
  trace: undefined,
  current_task: undefined,
  agent_invocations: undefined,
  tool_calls: undefined,
  enhanced_result: undefined,
  event_history: undefined,
};

// The layout logic, moved from App.tsx
const layoutNodes = (nodes: any[], edges: any[]): CustomNode[] => {
    storeLogger.debug('Layout function called', { nodeCount: nodes.length, edgeCount: edges.length });
    storeLogger.debug('Sample edge structure', edges[0]);
    
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const adjacencyList = new Map(nodes.map(n => [n.id, []]));
    const inDegree = new Map(nodes.map(n => [n.id, 0]));

    edges.forEach(edge => {
        // Handle both formats: backend uses source/target, some legacy might use from/to
        const source = edge.source || edge.from;
        const target = edge.target || edge.to;
        
        storeLogger.debug('Processing edge', { source, target, originalEdge: edge });
        
        if (source && target && adjacencyList.has(source)) {
            adjacencyList.get(source).push(target);
        }
        if (target && inDegree.has(target)) {
            inDegree.set(target, (inDegree.get(target) || 0) + 1);
        }
    });

    const rootNodes = nodes.filter(node => (inDegree.get(node.id) || 0) === 0);

    const levels = new Map<number, string[]>();
    const visited = new Set<string>();
    const queue: { nodeId: string; level: number }[] = rootNodes.map(node => ({ nodeId: node.id, level: 0 }));

    while (queue.length > 0) {
        const { nodeId, level } = queue.shift()!;
        if (visited.has(nodeId)) continue;
        visited.add(nodeId);

        if (!levels.has(level)) levels.set(level, []);
        levels.get(level)!.push(nodeId);

        (adjacencyList.get(nodeId) || []).forEach((childId: string) => {
            if (!visited.has(childId)) {
                queue.push({ nodeId: childId, level: level + 1 });
            }
        });
    }

    const nodeWidth = 250;
    const nodeHeight = 120;
    const levelSpacing = 300;
    const nodeSpacing = 200;

    return nodes.map(node => {
        let nodeLevel = 0;
        let nodeIndex = 0;

        for (const [level, levelNodes] of levels.entries()) {
            const index = levelNodes.indexOf(node.id);
            if (index !== -1) {
                nodeLevel = level;
                nodeIndex = index;
                break;
            }
        }
        
        const levelNodes = levels.get(nodeLevel) || [];
        const levelWidth = levelNodes.length * nodeSpacing;
        const startX = -levelWidth / 2;

        return {
            ...node,
            position: {
                x: startX + nodeIndex * nodeSpacing + 400,
                y: nodeLevel * levelSpacing + 100,
            },
        };
    });
};


export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  ...initialState,

  onNodesChange: (changes) => set({ nodes: applyNodeChanges(changes, get().nodes) }),
  onEdgesChange: (changes) => set({ edges: applyEdgeChanges(changes, get().edges) }),

  startWorkflow: (workflowId, query, initialStatus) => {
    storeLogger.info('Starting workflow', { workflowId, query, initialStatus });
    
    set({
      ...initialState,
      workflowId,
      query,
      nodes: initialStatus.nodes || [],
      edges: initialStatus.edges || [],
      status: initialStatus.status || 'initializing',
    });
    
    // Apply layout on start if we have nodes and edges
    if (initialStatus.nodes && initialStatus.edges) {
      storeLogger.info('Applying initial layout for workflow start');
      get().layoutNodes(initialStatus.nodes, initialStatus.edges);
    } else {
      storeLogger.info('No initial nodes/edges provided, will wait for status updates');
    }
  },

  setPollingWorkflow: (workflowId: string) => {
    storeLogger.info('Setting polling workflow', { workflowId });
    set({
        ...initialState,
        workflowId,
        status: 'running',
    });
  },

  layoutNodes: (nodes, edges) => {
    storeLogger.info('Laying out nodes', { nodeCount: nodes.length, edgeCount: edges.length });
    storeLogger.debug('Sample edge structure', edges[0]);
    
    const positionedNodes = layoutNodes(nodes, edges);
    
    // Backend edges already have correct structure with source/target, just ensure they have proper IDs
    const reactFlowEdges = edges.map((edge: any, index: number) => ({
        id: edge.id || `edge-${index}`,
        source: edge.source || edge.from, // Handle both formats
        target: edge.target || edge.to,   // Handle both formats
        type: edge.type || 'default',
    }));
    
    storeLogger.info('Layout complete. Setting nodes and edges', {
      positionedNodesCount: positionedNodes.length,
      reactFlowEdgesCount: reactFlowEdges.length
    });
    storeLogger.debug('Sample React Flow edge', reactFlowEdges[0]);
    set({ nodes: positionedNodes, edges: reactFlowEdges });
  },

  updateWorkflowStatus: (update) => {
    set((state) => {
      if (!state.workflowId || state.workflowId !== update.workflow_id) {
        return state;
      }
      
      storeLogger.info('Updating workflow status', update);
      
      // Map ALL properties from the backend data to the store
      const newState: Partial<WorkflowState> = {
          status: update.status || state.status,
          result: update.result !== undefined ? update.result : state.result,
          executionTime: update.execution_time || state.executionTime,
          error: update.error || state.error,
          trace: update.trace !== undefined ? update.trace : state.trace,
          current_task: update.current_task !== undefined ? update.current_task : state.current_task,
          agent_invocations: update.agent_invocations !== undefined ? update.agent_invocations : state.agent_invocations,
          tool_calls: update.tool_calls !== undefined ? update.tool_calls : state.tool_calls,
          enhanced_result: update.enhanced_result !== undefined ? update.enhanced_result : state.enhanced_result,
          event_history: update.event_history !== undefined ? update.event_history : state.event_history,
      };

      // Handle graph updates - backend returns nodes and edges directly, not in workflow_graph wrapper
      if (update.nodes && update.edges) {
          storeLogger.info('Processing nodes and edges from update', {
              nodesCount: update.nodes.length,
              edgesCount: update.edges.length,
              sampleNode: update.nodes[0],
              sampleEdge: update.edges[0]
          });
          
          // If the store has no nodes yet, this is the initial graph. Layout and set.
          if (state.nodes.length === 0) {
              storeLogger.info('Received initial workflow graph. Performing layout');
              storeLogger.debug('Nodes from backend', update.nodes);
              storeLogger.debug('Edges from backend', update.edges);
              get().layoutNodes(update.nodes, update.edges);
          } else {
              // Otherwise, merge status updates into existing nodes.
              storeLogger.info('Merging node updates');
              const nodeMap = new Map(state.nodes.map(n => [n.id, n]));
              update.nodes.forEach(updatedNode => {
                  const existingNode = nodeMap.get(updatedNode.id);
                  if (existingNode) {
                      const mergedData = { ...existingNode.data, ...updatedNode.data };
                      nodeMap.set(updatedNode.id, { ...existingNode, data: mergedData, status: updatedNode.status || existingNode.data.status });
                  }
              });
              newState.nodes = Array.from(nodeMap.values());
          }
      }
      
      // Also handle legacy workflow_graph format for backward compatibility
      if (update.workflow_graph) {
          storeLogger.info('Processing legacy workflow_graph format', {
              nodesCount: update.workflow_graph.nodes?.length || 0,
              edgesCount: update.workflow_graph.edges?.length || 0
          });
          
          // If the store has no nodes yet, this is the initial graph. Layout and set.
          if (state.nodes.length === 0) {
              storeLogger.info('Received legacy workflow_graph format. Performing layout');
              get().layoutNodes(update.workflow_graph.nodes, update.workflow_graph.edges);
          } else {
              // Otherwise, merge status updates into existing nodes.
              storeLogger.info('Merging node updates from legacy format');
              const nodeMap = new Map(state.nodes.map(n => [n.id, n]));
              update.workflow_graph.nodes.forEach(updatedNode => {
                  const existingNode = nodeMap.get(updatedNode.id);
                  if (existingNode) {
                      const mergedData = { ...existingNode.data, ...updatedNode.data };
                      nodeMap.set(updatedNode.id, { ...existingNode, data: mergedData, status: updatedNode.status || existingNode.data.status });
                  }
              });
              newState.nodes = Array.from(nodeMap.values());
          }
      }
      
      return { ...state, ...newState };
    });
  },

  resetWorkflow: () => {
    storeLogger.info('Resetting workflow state');
    set(initialState);
  },
}));