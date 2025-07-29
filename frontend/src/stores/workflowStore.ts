 import { create } from 'zustand';
import {
  Edge, OnNodesChange, OnEdgesChange, applyNodeChanges, applyEdgeChanges
} from 'reactflow';
import { WorkflowStatus, CustomNode } from '../types';

export interface WorkflowState {
  nodes: CustomNode[];
  edges: Edge[];
  status: 'idle' | 'running' | 'completed' | 'failed' | 'initializing';
  result: string | null;
  workflowId: string | null;
  query: string | null;
  executionTime: number;
  error: string | null;

  // Actions
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  startWorkflow: (workflowId: string, query: string, initialStatus: WorkflowStatus) => void;
  updateWorkflowStatus: (statusUpdate: Partial<WorkflowStatus>) => void;
  resetWorkflow: () => void;
  setPollingWorkflow: (workflowId: string) => void;
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
};

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  ...initialState,

  onNodesChange: (changes) => set({ nodes: applyNodeChanges(changes, get().nodes) }),
  onEdgesChange: (changes) => set({ edges: applyEdgeChanges(changes, get().edges) }),

  startWorkflow: (workflowId, query, initialStatus) => {
    set({
      ...initialState, // Reset state completely
      workflowId,
      query,
      nodes: initialStatus.nodes || [],
      edges: initialStatus.edges || [],
      status: initialStatus.status || 'initializing',
    });
  },
  
  setPollingWorkflow: (workflowId: string) => {
    set({
        ...initialState,
        workflowId,
        status: 'running', // Assume it's running if we are polling
    });
  },

  updateWorkflowStatus: (update) => {
    set((state) => {
        // Only update if the workflowId matches and the store is not idle
        if (!state.workflowId || state.workflowId !== update.workflow_id) return state;

        const newState: Partial<WorkflowState> = { ...update };

        // Deep merge nodes to update their data without replacing the whole object
        if (update.nodes) {
            const nodeMap = new Map(state.nodes.map(n => [n.id, n]));
            update.nodes.forEach(updatedNode => {
                const existingNode = nodeMap.get(updatedNode.id);
                if (existingNode) {
                    // This merge is critical for preserving the node object reference
                    const mergedData = { ...existingNode.data, ...updatedNode.data };
                    nodeMap.set(updatedNode.id, { ...existingNode, data: mergedData });
                } else {
                    nodeMap.set(updatedNode.id, updatedNode);
                }
            });
            newState.nodes = Array.from(nodeMap.values());
        }
        
        return { ...state, ...newState };
    });
  },

  resetWorkflow: () => set(initialState),
}));