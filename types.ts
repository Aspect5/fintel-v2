
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

// Data payload for different node types in the workflow
export type AgentNodeData = {
    label: string;
    details: string;
    status: AgentInvocationStatus;
    error?: string;
    result?: string;
    toolCalls?: ToolCallResult[];
};

export type BasicNodeData = {
    label: string;
    details: string;
};

export type NodeData = BasicNodeData | AgentNodeData;

export type CustomNode =
    | (Node<BasicNodeData> & {
        type: 'coordinator';
      })
    | (Node<AgentNodeData> & {
        type: 'agent';
      })
    | (Node<AgentNodeData> & {
        type: 'synthesizer';
      });

export type CustomEdge = Edge;
