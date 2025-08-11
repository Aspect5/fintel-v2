import { Report } from '../src/types';
import { ControlFlowProvider } from '@/stores/store';
import { parseReportContent } from '../src/utils/reportParser';

const API_BASE_URL = '/api';

interface RunWorkflowPayload {
    task: string;
    provider: ControlFlowProvider;
    base_url?: string;
}

// Registry-related interfaces
export interface ToolInfo {
    name: string;
    description: string;
    category: string;
    enabled: boolean;
    api_key_required?: string;
    examples: string[];
    dependencies: string[];
    retry_config: Record<string, any>;
    usage_stats: Record<string, any>;
}

export interface AgentInfo {
    name: string;
    instructions: string;
    tools: string[];
    capabilities: string[];
    required: boolean;
    enabled: boolean;
    validation_status: {
        valid: boolean;
        enabled: boolean;
        required: boolean;
        tool_validation: Record<string, string>;
        missing_tools: string[];
        capability_validation: {
            has_capabilities: boolean;
            capabilities: string[];
        };
    };
}

export interface RegistryHealth {
    status: 'healthy' | 'degraded';
    validation: {
        valid: boolean;
        errors: string[];
        warnings: string[];
    };
    components: {
        tool_registry: {
            valid: boolean;
            errors: string[];
            warnings: string[];
            total_tools: number;
            enabled_tools: number;
        };
        agent_registry: {
            valid: boolean;
            errors: string[];
            warnings: string[];
            total_agents: number;
            enabled_agents: number;
            required_agents: number;
            capabilities: string[];
        };
    };
    summary: {
        total_tools: number;
        enabled_tools: number;
        total_agents: number;
        enabled_agents: number;
        required_agents: number;
        capabilities: string[];
        validation_errors: number;
        validation_warnings: number;
    };
    api_keys: Record<string, boolean>;
}

export interface SystemSummary {
    validation: {
        valid: boolean;
        error_count: number;
        warning_count: number;
    };
    tools: {
        total: number;
        enabled: number;
        categories: string[];
        configuration_summary: Record<string, any>;
        validation_status: Record<string, any>;
    };
    agents: {
        total: number;
        enabled: number;
        required: number;
        available: string[];
        capabilities: string[];
        validation_status: Record<string, any>;
    };
    mapping: {
        tool_to_agents: Record<string, string[]>;
        capability_to_agents: Record<string, string[]>;
        agent_tool_validation: Record<string, Record<string, string>>;
    };
    api_keys: Record<string, boolean>;
    system_health: Record<string, any>;
}

// Registry API functions
export const getRegistryHealth = async (): Promise<RegistryHealth> => {
    const response = await fetch(`${API_BASE_URL}/registry/health`);
    if (!response.ok) {
        throw new Error(`Failed to get registry health: ${response.statusText}`);
    }
    return response.json();
};

export const getRegistryStatus = async (): Promise<{
    validation: {
        valid: boolean;
        errors: string[];
        warnings: string[];
        details: Record<string, any>;
    };
    summary: SystemSummary;
    timestamp: string;
}> => {
    const response = await fetch(`${API_BASE_URL}/registry/status`);
    if (!response.ok) {
        throw new Error(`Failed to get registry status: ${response.statusText}`);
    }
    return response.json();
};

export const getSystemSummary = async (): Promise<SystemSummary> => {
    const response = await fetch(`${API_BASE_URL}/registry/summary`);
    if (!response.ok) {
        throw new Error(`Failed to get system summary: ${response.statusText}`);
    }
    return response.json();
};

export const getTools = async (): Promise<ToolInfo[]> => {
    const response = await fetch(`${API_BASE_URL}/registry/tools`);
    if (!response.ok) {
        throw new Error(`Failed to get tools: ${response.statusText}`);
    }
    return response.json();
};

export const getToolDetails = async (toolName: string): Promise<ToolInfo & { agents_using_tool: string[] }> => {
    const response = await fetch(`${API_BASE_URL}/registry/tools/${toolName}`);
    if (!response.ok) {
        throw new Error(`Failed to get tool details: ${response.statusText}`);
    }
    return response.json();
};

export const getAgents = async (): Promise<AgentInfo[]> => {
    const response = await fetch(`${API_BASE_URL}/agents`);
    if (!response.ok) {
        throw new Error(`Failed to get agents: ${response.statusText}`);
    }
    const data = await response.json();
    return Object.values(data.agent_info || {});
};

export const getAgentDetails = async (agentName: string): Promise<AgentInfo> => {
    const response = await fetch(`${API_BASE_URL}/registry/agents/${agentName}`);
    if (!response.ok) {
        throw new Error(`Failed to get agent details: ${response.statusText}`);
    }
    return response.json();
};

export const getCapabilities = async (): Promise<{
    capabilities: string[];
    capability_mapping: Record<string, string[]>;
}> => {
    const response = await fetch(`${API_BASE_URL}/registry/capabilities`);
    if (!response.ok) {
        throw new Error(`Failed to get capabilities: ${response.statusText}`);
    }
    return response.json();
};

/**
 * Executes a workflow on the Python backend.
 *
 * @param query - The user's natural language query.
 * @param provider - The selected LLM provider ('openai', 'gemini', 'local').
 * @param baseUrl - The optional base URL for a local model.
 * @returns A promise that resolves to the final report from the backend.
 */
export const runWorkflow = async (
    query: string, 
    provider: ControlFlowProvider, 
    baseUrl?: string
): Promise<Report> => {
    
    const payload: RunWorkflowPayload = {
        task: query,
        provider: provider,
    };

    if (provider === 'local' && baseUrl) {
        payload.base_url = baseUrl;
    }

    console.log("Frontend Service: Sending request to backend...", { url: `${API_BASE_URL}/run-workflow`, payload });

    try {
        const response = await fetch(`${API_BASE_URL}/run-workflow`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        console.log("Frontend Service: Received response from backend", { status: response.status });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: "Failed to parse error response from backend." }));
            console.error("Frontend Service: Backend returned an error", { errorData });
            throw new Error(errorData.error || `Request failed with status ${response.status}`);
        }

        const data = await response.json();
        console.log("Frontend Service: Successfully parsed backend response", { data });
        
        // Parse the backend response to extract sections
        const parsedSections = parseReportContent(data.result);
        
        // Extract agent invocations and results from the response
        const agentInvocations = data.agent_invocations || [];
        const agentResults = data.trace?.agent_results || {};
        
        // Create agent findings from both invocations and results
        const agentFindings = [];
        
        // Add findings from agent results
        for (const [agentName, results] of Object.entries(agentResults)) {
            if (Array.isArray(results) && results.length > 0) {
                const lastResult = results[results.length - 1];
                agentFindings.push({
                    agentName: agentName,
                    summary: lastResult.content || `Completed analysis at ${lastResult.timestamp}`,
                    details: lastResult.content || `Agent ${agentName} completed its analysis successfully.`
                });
            }
        }
        
        // Add findings from invocations if no results available
        if (agentFindings.length === 0) {
            agentFindings.push(...agentInvocations
                .filter((inv: any) => inv.action === 'completed')
                .map((inv: any) => ({
                    agentName: inv.agent,
                    summary: `Completed analysis at ${inv.timestamp}`,
                    details: `Agent ${inv.agent} completed its analysis successfully.`
                })));
        }
        
        // Create a comprehensive Report object with parsed sections
        const comprehensiveReport: Report = {
            executiveSummary: data.result,
            agentFindings: agentFindings,
            failedAgents: [],
            crossAgentInsights: `Generated by ControlFlow (Python) with the '${provider}' provider using ${agentFindings.length} specialist agents.`,
            actionableRecommendations: parsedSections.actionItems,
            riskAssessment: parsedSections.riskAssessment || "N/A",
            confidenceLevel: parsedSections.confidenceLevel,
            dataQualityNotes: "Based on the synthesis from the selected LLM provider with comprehensive event tracking.",
            executionTrace: { 
                fintelQueryAnalysis: parsedSections.queryAnalysis || '', 
                agentInvocations: agentInvocations 
            },
            retryAnalysis: parsedSections.retryAnalysis,
            parsedSections: parsedSections,
        };

        return comprehensiveReport;

    } catch (error) {
        console.error("Frontend Service: An error occurred during the API call.", { error });
        const errorMessage = error instanceof Error ? error.message : "An unknown network error occurred.";
        throw new Error(`Failed to execute workflow on Python backend: ${errorMessage}`);
    }
};
