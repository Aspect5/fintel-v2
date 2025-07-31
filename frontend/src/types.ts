import { Node, Edge } from 'reactflow';

export type { Node, Edge };

// --- Core Chat and Notification Types ---

/**
 * Defines the structure of a single chat message, used in App.tsx.
 */
export interface ChatMessage {
  role: 'user' | 'assistant'; // The role of the message sender
  content: string; // The text content of the message
  trace?: any; // Optional agent trace data for visualization
}

/**
 * Defines the structure for a UI notification, used in the global store.
 */
export interface Notification {
  type: 'success' | 'error' | 'info';
  message: string;
}

// --- Agent and Workflow Types ---

export interface AgentFinding {
  agentName: string;
  specialization: string;
  summary: string;
  details: string[];
  toolCalls?: ToolCallResult[];
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
  executionTrace: ExecutionTrace;
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

// --- React Flow Node Types for Workflow Canvas ---

export interface BasicNodeData {
  label: string;
  details: string;
  status: AgentInvocationStatus;
};

export interface AgentNodeData extends BasicNodeData {
  error?: string;
  result?: string;
  toolCalls?: ToolCallResult[];
}

export type CustomNodeData = BasicNodeData | AgentNodeData;
export type CustomNode = Node<CustomNodeData>;
export type CustomEdge = Edge;

export interface WorkflowStatus {
    workflow_id?: string;
    nodes: CustomNode[];
    edges: CustomEdge[];
    status: 'initializing' | 'running' | 'completed' | 'failed';
    query?: string;
    result?: string;
    trace?: any;
    error?: string;
    current_task?: string;
    execution_time?: number;
}

// --- Global Type Declarations ---

/**
 * Extends the global Window interface to include the experimental 'ai' property
 * for the built-in browser AI, used in App.tsx.
 */
declare global {
  interface Window {
    ai?: {
      prompt: (prompt: string) => Promise<{ text: () => string }>;
      tool: (toolName: string, parameters: any) => Promise<any>;
    };
  }
}
