// frontend/src/types.ts
import { Node, Edge } from 'reactflow';

export type { Node, Edge };

// --- Core Chat and Notification Types ---

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  trace?: any;
}

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
  parameters: string;
}

export interface ToolCallResult {
  toolName: string;
  toolInput: any;
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
  result?: any;
}

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

// --- React Flow Node Types ---

export interface BasicNodeData {
  label: string;
  status: AgentInvocationStatus;
  type?: string;
  agent?: string;
  details?: string;
  result?: any;
  error?: string;
  description?: string;
  agentName?: string;
  tools?: any[];
  liveDetails?: LiveDetails | null;
  usedTools?: Array<{ name: string; mock: boolean }>;
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
  nodes: CustomNode[]; // Use CustomNode for consistency
  edges: WorkflowGraphEdge[];
}

// --- Backend and State Types ---

// This represents the detailed, structured result from a completed workflow.
export interface EnhancedResult {
    result: string | object;
    agent_invocations?: AgentInvocation[];
    provider?: string;
    query?: string;
    tool_calls?: any[];
    recommendation?: string;
    market_analysis?: string;
    content?: string;
}

// Represents the full state of a workflow as polled from the backend
export interface PersistedWorkflowStatus {
    workflow_id: string;
    status: 'initializing' | 'running' | 'completed' | 'failed';
    query: string;
    result?: any; // Use 'any' to resolve conflict
    trace?: any;
    error?: string;
    current_task?: string;
    execution_time: number;
    workflow_graph?: WorkflowGraph;
    agent_invocations?: AgentInvocation[]; // Duplicated for now
    tool_calls?: any[];
    enhanced_result?: any;
  event_history?: Array<{
    event_type: string;
    timestamp: string;
    agent_name?: string;
    agent_role?: string;
    task_id?: string;
    task_name?: string;
    tool_name?: string;
    tool_input?: any;
    tool_output?: any;
    is_internal_controlflow_tool?: boolean;
    is_error?: boolean;
    result?: string;
    error?: string;
  }>;
}

// This is the primary status object used within the frontend logic
export interface WorkflowStatus extends Omit<PersistedWorkflowStatus, 'result'> {
    nodes?: CustomNode[];
    edges?: CustomEdge[];
    result?: any; // Keep result flexible here for various stages
}

// --- Live Details Types ---

export interface LiveDetails {
  agent_reasoning?: string;
  tool_calls?: Array<{
    tool_name: string;
    tool_args?: any;
  }>;
  task_progress?: {
    current_step: string;
  };
}

// --- Global Type Declarations ---

declare global {
  interface Window {
    ai?: {
      prompt: (prompt: string) => Promise<{ text: () => string }>;
      tool: (toolName: string, parameters: any) => Promise<any>;
    };
  }
}