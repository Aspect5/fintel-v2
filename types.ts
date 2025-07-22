
import type { Node, Edge } from 'reactflow';

export interface AgentFinding {
  agentName: string;
  specialization: string;
  summary: string;
  details: string[];
}

export interface ToolCallRequest {
  toolName: string;
  parameters: string; // This will be a JSON string from the model
}

export interface ToolCallResult {
  toolName: string;
  toolInput: string; // A stringified version of the parameters for display
  toolOutput: any;
  toolOutputSummary: string;
}


export type AgentInvocationStatus = 'pending' | 'running' | 'success' | 'failure';

export interface AgentInvocation {
  agentName:string;
  naturalLanguageTask: string;
  toolCalls: ToolCallResult[];
  synthesizedResponse: string;
  status: AgentInvocationStatus;
  error?: string;
}

export interface ExecutionTrace {
  fintelQueryAnalysis: string;
  agentInvocations: AgentInvocation[];
}

export interface Report {
  executiveSummary: string;
  agentFindings: AgentFinding[];
  failedAgents: AgentFailure[];
  crossAgentInsights: string;
  actionableRecommendations: string[];
  riskAssessment: string;
  confidenceLevel: number;
  dataQualityNotes: string;
  executionTrace: ExecutionTrace; // Keep for data integrity
}

export interface Plan {
    agentName: string;
    task: string;
}

export interface AgentFailure {
    agentName: string;
    task: string;
    error: string;
}

export type ChatMessage = {
    id: string;
    sender: 'user' | 'ai';
    content: string;
    timestamp: string;
};

export interface Notification {
  type: 'success' | 'error' | 'info';
  message: string;
}

// A base interface for all node data. The coordinator and synthesizer
// also need a status, so it's included here.

export interface BasicNodeData {
  label: string;
  details: string;
  status: AgentInvocationStatus;
};

// Agent-specific data extends the base, adding its unique properties.
// `toolCalls` is now non-optional as it's always initialized in your code.
export interface AgentNodeData extends BasicNodeData {
  error?: string;
  result?: string;
  toolCalls: ToolCallResult[];
};

// A union of all possible data types for our nodes.
// THIS is the correct type to pass as a generic to useNodesState.
export type CustomNodeData = BasicNodeData | AgentNodeData;

// A simple, clear type alias for a React Flow node using our custom data union.
// This is the type that the `nodes` array will hold.
export type CustomNode = Node<CustomNodeData>;

export type CustomEdge = Edge;