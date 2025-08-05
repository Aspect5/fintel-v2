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

export type AgentInvocationStatus = 'pending' | 'running' | 'success' | 'failure' | 'completed';

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
  retryAnalysis?: RetryAnalysisData;
  parsedSections?: ParsedReport;
  result?: any; // Enhanced workflow results
}

// Import retry analysis types from the parser
export interface RetryAnalysisData {
  agentsEncounteringErrors: string[];
  specificErrors: string[];
  retryAttempts: number;
  adaptationStrategies: string[];
  adaptationSuccess: boolean;
  impactOnAnalysis: string;
  retryDetails: RetryDetail[];
}

export interface RetryDetail {
  agent: string;
  specialization: string;
  tool: string;
  totalAttempts: number;
  finalStatus: 'success' | 'failed';
  retrySequence: RetryAttempt[];
  adaptationStrategy?: string;
}

export interface RetryAttempt {
  attemptNumber: number;
  status: 'success' | 'error';
  input: any;
  errorType?: string;
  errorMessage?: string;
  receivedData?: any;
  expectedFormat?: string;
}

export interface ParsedReport {
  executiveSummary: string;
  investmentRecommendation: string;
  keyFindings: string[];
  riskAssessment: string;
  actionItems: string[];
  retryAnalysis?: RetryAnalysisData;
  confidenceLevel: number;
  queryAnalysis?: string;
  executionTime?: string;
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
  status: AgentInvocationStatus;
  type?: string;
  agent?: string;
  details?: string;
  result?: any;
  error?: string;
}

export interface AgentNodeData extends BasicNodeData {
  toolCalls?: ToolCallResult[];
}

export type CustomNodeData = BasicNodeData | AgentNodeData;
export type CustomNode = Node<CustomNodeData>;
export type CustomEdge = Edge;

// --- Workflow Graph Types ---

export interface WorkflowGraphNode {
  id: string;
  label: string;
  status: AgentInvocationStatus;
  type: 'input' | 'tool' | 'agent' | 'output';
  agent?: string;
  details?: string;
  result?: any;
  error?: string;
}

export interface WorkflowGraphEdge {
  from: string;
  to: string;
}

export interface WorkflowGraph {
  nodes: WorkflowGraphNode[];
  edges: WorkflowGraphEdge[];
  ticker?: string;
}

export interface WorkflowStatus {
    workflow_id?: string;
    nodes?: CustomNode[];
    edges?: CustomEdge[];
    workflow_graph?: WorkflowGraph;
    status: 'initializing' | 'running' | 'completed' | 'failed';
    query?: string;
    result?: string;
    trace?: any;
    error?: string;
    current_task?: string;
    execution_time?: number;
    enhanced_result?: any;
    agent_invocations?: AgentInvocation[];
    tool_calls?: any[];
    tool_analytics?: any;
    metrics?: any;
    resource_usage?: any;
    registry_status?: any;
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
