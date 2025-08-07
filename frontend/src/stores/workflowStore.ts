// frontend/src/stores/workflowStore.ts
import { create } from 'zustand';
import {
  Edge, OnNodesChange, OnEdgesChange, applyNodeChanges, applyEdgeChanges,
} from 'reactflow';
import {
  WorkflowStatus, CustomNode, PersistedWorkflowStatus,
} from '../types';

// This represents the comprehensive status object received from the backend.
export type FullWorkflowStatus = WorkflowStatus & PersistedWorkflowStatus;

export interface WorkflowState {
  nodes: CustomNode[];
  edges: Edge[];
  status: 'idle' | 'running' | 'completed' | 'failed' | 'initializing';
  result: any;
  workflowId: string | null;
  query: string | null;
  executionTime: number;
  error: string | null;
  trace?: any;
  current_task?: string;
  agent_invocations?: any[];
  tool_calls?: any[];
  enhanced_result?: any;
  event_history?: any[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  startWorkflow: (workflowId: string, query: string, initialStatus: Partial<FullWorkflowStatus>) => void;
  updateWorkflowStatus: (statusUpdate: Partial<FullWorkflowStatus>) => void;
  resetWorkflow: () => void;
  setPollingWorkflow: (workflowId: string) => void;
}

const initialState: Omit<WorkflowState, 'onNodesChange' | 'onEdgesChange' | 'startWorkflow' | 'updateWorkflowStatus' | 'resetWorkflow' | 'setPollingWorkflow'> = {
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

// Standalone layout function
const layoutNodes = (nodes: CustomNode[], edges: Edge[]): CustomNode[] => {
    if (!nodes || nodes.length === 0) return [];
    
    const adjacencyList = new Map<string, string[]>();
    const inDegree = new Map<string, number>();

    nodes.forEach(node => {
        adjacencyList.set(node.id, []);
        inDegree.set(node.id, 0);
    });

    edges.forEach(edge => {
        if (adjacencyList.has(edge.source)) {
            adjacencyList.get(edge.source)!.push(edge.target);
        }
        if (inDegree.has(edge.target)) {
            inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
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

    const levelSpacing = 300;
    const nodeSpacing = 350;

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
                x: startX + nodeIndex * nodeSpacing,
                y: nodeLevel * levelSpacing,
            },
        };
    });
};

export const useWorkflowStore = create<WorkflowState>((set) => ({
  ...initialState,

  onNodesChange: (changes) => set((state) => ({ nodes: applyNodeChanges(changes, state.nodes) })),
  onEdgesChange: (changes) => set((state) => ({ edges: applyEdgeChanges(changes, state.edges) })),

  startWorkflow: (workflowId, query, initialStatus) => {
    set({
      ...initialState,
      workflowId,
      query,
      status: initialStatus.status || 'initializing',
    });
  },

  setPollingWorkflow: (workflowId: string) => {
    set({
        ...initialState,
        workflowId,
        status: 'running',
    });
  },

  updateWorkflowStatus: (update) => {
    set((state) => {
      if (!state.workflowId || state.workflowId !== update.workflow_id) {
        return state;
      }
      
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

      if (update.nodes && update.edges && update.nodes.length > 0) {
          if (state.nodes.length === 0) {
              console.log('[Store] Received initial workflow graph. Performing layout.');
              const rawEdges = update.edges.map((edge: any, index: number) => ({
                id: `edge-${index}`,
                source: edge.source,
                target: edge.target,
                type: edge.type || 'default',
              }));
              newState.nodes = layoutNodes(update.nodes, rawEdges);
              newState.edges = rawEdges;
          } else {
              console.log('[Store] Merging node updates.');
              const updatedNodes = state.nodes.map(existingNode => {
                  const nodeUpdate = update.nodes!.find(n => n.id === existingNode.id);
                  if (nodeUpdate) {
                      return {
                          ...existingNode,
                          data: {
                              ...existingNode.data,
                              ...nodeUpdate.data,
                          },
                      };
                  }
                  return existingNode;
              });
              newState.nodes = updatedNodes;
          }
      }
      
      return { ...state, ...newState };
    });
  },

  resetWorkflow: () => set(initialState),
}));