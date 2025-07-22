import { Report, Plan, AgentFinding, AgentInvocation } from '../types';
import { agentRegistry, getAgentDefinition } from '../agents/registry';
import { executeTool, toolRegistry } from '../tools/financialTools';
import { agentFinalResponseSchema, agentToolCallSchema, planSchema, reportSynthesizerSchema } from '../agents/schemas';
import { useStore } from '../store';

export class AgentFailureError extends Error {
    payload: AgentFailure;
    constructor(message: string, payload: AgentFailure) {
        super(message);
        this.name = 'AgentFailureError';
        this.payload = payload;
    }
}

// Re-defining this type locally as it's only used here.
interface AgentFailure {
    agentName: string;
    task: string;
    error: string;
}


const purposeToSchemaMap = {
    coordinator: planSchema,
    tool_planning: agentToolCallSchema,
    synthesis: agentFinalResponseSchema,
    report: reportSynthesizerSchema,
};

async function callGeminiApi(prompt: string, purpose: keyof typeof purposeToSchemaMap): Promise<any> {
    const apiKey = useStore.getState().geminiApiKey;
    if (!apiKey) {
        throw new Error("Gemini API key not found in store. The Visual engine requires a key to be set.");
    }

    const model = 'gemini-1.5-flash';
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
    const schema = purposeToSchemaMap[purpose];

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: schema,
                temperature: 0.1,
            },
        }),
    });

    const responseData = await response.json();
    if (!response.ok || responseData.error) {
        throw new Error(`Gemini API call failed: ${responseData?.error?.message || response.statusText}`);
    }
    if (!responseData.candidates?.[0]?.content?.parts?.[0]?.text) {
        throw new Error("Gemini API call failed: No valid response content found.");
    }
    return JSON.parse(responseData.candidates[0].content.parts[0].text);
}

export const runCoordinatorPlanner = async (query: string): Promise<{plan: Plan[], analysis: string}> => {
    const availableAgents = agentRegistry.map(a => `- ${a.name}: ${a.description}`).join('\n');
    const prompt = `User Query: "${query}". Available agents:
${availableAgents}
Analyze the query and create a plan by selecting 2-3 agents and defining a specific task for each.`;
    return callGeminiApi(prompt, 'coordinator');
};

async function planToolCalls(agentName: string, task: string): Promise<any> {
    const agentDef = getAgentDefinition(agentName);
    const availableTools = agentDef?.tools.map(t => toolRegistry.get(t)).filter(Boolean) || [];
    const toolSchemas = availableTools.map(t => ({ name: t!.name, description: t!.description, parameters: t!.parameters }));
    const prompt = `You are ${agentName}. Task: "${task}". Available tools:
${JSON.stringify(toolSchemas)}
Decide which tools to call.`;
    return callGeminiApi(prompt, 'tool_planning');
}

async function synthesizeResults(agentName: string, task: string, toolResults: any[]): Promise<string> {
    const prompt = `You are ${agentName}. Task: "${task}". Tool results:
${JSON.stringify(toolResults)}
Synthesize a final answer.`;
    const result = await callGeminiApi(prompt, 'synthesis');
    return result.finalResponse;
}

export const runAgentTask = async (plan: Plan, addStatusMessage: (msg: string) => void): Promise<AgentInvocation> => {
    try {
        const plannedTools = await planToolCalls(plan.agentName, plan.task);
        const toolCallResults = await Promise.all(
            plannedTools.toolCalls.map(async (call: any) => {
                addStatusMessage(`[${plan.agentName}] Executing tool: ${call.toolName}`);
                const result = await executeTool(call.toolName, JSON.parse(call.parameters));
                return { toolName: call.toolName, toolInput: call.parameters, ...result };
            })
        );
        const synthesizedResponse = await synthesizeResults(plan.agentName, plan.task, toolCallResults);
        return {
            agentName: plan.agentName,
            naturalLanguageTask: plan.task,
            toolCalls: toolCallResults,
            synthesizedResponse,
            status: 'success'
        };
    } catch (error: any) {
        throw new AgentFailureError(error.message, { agentName: plan.agentName, task: plan.task, error: error.message });
    }
};

export const runReportSynthesizer = async (query: string, agentFindings: AgentFinding[]): Promise<Report> => {
    const prompt = `Original Query: "${query}". Agent Findings:
${JSON.stringify(agentFindings)}
Synthesize a final, user-facing report.`;
    return callGeminiApi(prompt, 'report');
};