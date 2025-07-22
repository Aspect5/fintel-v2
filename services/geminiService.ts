import { Report, Plan, AgentFinding, AgentInvocation, ToolCallRequest, ToolCallResult, AgentFailure } from '../types';
import { agentRegistry, getAgentDefinition } from '../agents/registry';
import { executeTool, toolRegistry } from '../tools/financialTools';
import { agentFinalResponseSchema, agentToolCallSchema, planSchema, reportSynthesizerSchema } from '../agents/schemas';
import { useApiKeyStore } from '../store';

export class AgentFailureError extends Error {
    payload: AgentFailure;
    constructor(message: string, payload: AgentFailure) {
        super(message);
        this.name = 'AgentFailureError';
        this.payload = payload;
    }
}

const purposeToSchemaMap = {
    coordinator: planSchema,
    tool_planning: agentToolCallSchema,
    synthesis: agentFinalResponseSchema,
    report: reportSynthesizerSchema,
};

/**
 * A helper to call the Gemini REST API directly using fetch.
 * This avoids the ReadableStream error encountered with the SDK in some environments.
 * @param prompt The user prompt or content for the model.
 * @param purpose A string indicating which schema to use for structured JSON output.
 * @returns The parsed JSON object from the model's response.
 */
async function callGeminiApi(prompt: string, purpose: 'coordinator' | 'tool_planning' | 'synthesis' | 'report'): Promise<any> {
    const apiKey = useApiKeyStore.getState().geminiApiKey;
    if (!apiKey) {
        throw new Error("Gemini API key has not been set. Please provide your key to proceed.");
    }
    
    const model = 'gemini-2.5-flash';
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

    const schema = purposeToSchemaMap[purpose];
    const requestBody = {
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
            responseMimeType: "application/json",
            responseSchema: schema,
            temperature: 0.1, // Lower temperature for more predictable, structured output
        },
    };

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
    });

    const responseData = await response.json();

    if (!response.ok || responseData.error) {
        const details = responseData?.error?.message || `HTTP error! Status: ${response.status}`;
        throw new Error(`Gemini API call failed: ${details}`);
    }

    if (!responseData.candidates || responseData.candidates.length === 0 || !responseData.candidates[0].content?.parts?.[0]?.text) {
        throw new Error("Gemini API call failed: No response candidates or valid content found.");
    }

    try {
        const jsonString = responseData.candidates[0].content.parts[0].text;
        return JSON.parse(jsonString);
    } catch(e) {
        console.error("Failed to parse JSON response from Gemini:", responseData.candidates[0].content.parts[0].text);
        throw new Error("The AI returned a malformed JSON response. Please try again.");
    }
}


export const runCoordinatorPlanner = async (query: string): Promise<{plan: Plan[], analysis: string}> => {
    const availableAgentsString = agentRegistry.map(agent => `- ${agent.name} (${agent.description}): Tools=[${agent.tools.join(', ')}]`).join('\n');
    
    const prompt = `
        You are FINTEL, a sophisticated multi-agent AI coordinator. Your job is to analyze a user's query and create an optimal execution plan by selecting specialized agents.

        Available Agents, their specializations, and their tools:
        ${availableAgentsString}

        User Query: "${query}"

        Instructions:
        1.  **Analyze Query:** Deeply understand the user's request, identifying the key entities, questions, and goals.
        2.  **Select Agents:** Choose a diverse set of 2-3 of the most relevant agents to handle the query. It is crucial to select multiple agents if their specializations provide complementary perspectives.
        3.  **Assign Tasks:** For each selected agent, define a single, clear, and specific natural-language task.
        4.  **Format Output:** Return your reasoning and the plan as a single, valid JSON object with two keys: "analysis" (your reasoning) and "plan" (an array of agent tasks).
        
        You must respond with only the raw JSON object as specified by the schema.
    `;

    try {
        const result = await callGeminiApi(prompt, 'coordinator');
        return result;
    } catch (error) {
        console.error("Error in Coordinator Planner:", error);
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
        throw new Error(`The AI coordinator failed to create a plan. Reason: ${errorMessage}`);
    }
};

async function planToolCalls(agentName: string, task: string, addStatusMessage: (msg: string) => void): Promise<ToolCallRequest[]> {
    const agentDef = getAgentDefinition(agentName);
    if (!agentDef) throw new Error(`Agent definition for ${agentName} not found.`);

    const availableTools = agentDef.tools
        .map(toolName => toolRegistry.get(toolName))
        .filter(Boolean);

    if (availableTools.length === 0) {
        return [];
    }

    const toolSchemas = availableTools.map(tool => ({
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
    }));

    const prompt = `
        You are the ${agentName} agent. Your instructions are: "${agentDef.instructions}".
        Your current task is: "${task}".

        You have access to the following tools and must decide which to call.
        
        Tools Available:
        ${JSON.stringify(toolSchemas, null, 2)}

        Based on your task, respond with ONLY a raw JSON object with a "toolCalls" key. The value should be an array of objects, where each object has "toolName" and "parameters".
        IMPORTANT: The value for the "parameters" key MUST be a JSON string. For example: { "toolCalls": [{ "toolName": "get_market_data", "parameters": "{\\"ticker\\":\\"MSFT\\"}" }] }
        If no tools are necessary, return an object with an empty "toolCalls" array.
    `;
    
    addStatusMessage(`[${agentName}] Planning tool usage for task: "${task}"`);
    const parsed = await callGeminiApi(prompt, 'tool_planning');
    return parsed.toolCalls as ToolCallRequest[];
}

async function synthesizeResults(agentName: string, task: string, toolCallResults: ToolCallResult[], addStatusMessage: (msg: string) => void): Promise<string> {
    const agentDef = getAgentDefinition(agentName);
    if (!agentDef) throw new Error(`Agent definition for ${agentName} not found.`);

    const toolResultsString = toolCallResults.length > 0 
        ? JSON.stringify(toolCallResults.map(r => ({ toolName: r.toolName, toolOutput: r.toolOutput })), null, 2)
        : "No tool calls were made.";

    const prompt = `
        You are the ${agentName} agent. Your instructions are: "${agentDef.instructions}".
        Your original task was: "${task}".

        You have executed your planned tool calls and received the following results:
        ${toolResultsString}

        Based on these results, synthesize a final, comprehensive answer to your original task.
        Respond with ONLY a raw JSON object with a "finalResponse" key containing your detailed answer as a string.
    `;

    addStatusMessage(`[${agentName}] Synthesizing final response from tool results.`);
    const parsed = await callGeminiApi(prompt, 'synthesis');
    return parsed.finalResponse;
}

export const runAgentTask = async (plan: Plan, addStatusMessage: (msg: string) => void): Promise<AgentInvocation> => {
    try {
        const toolCallRequests = await planToolCalls(plan.agentName, plan.task, addStatusMessage);

        const agentDef = getAgentDefinition(plan.agentName);
        if(!agentDef) throw new Error(`Agent ${plan.agentName} not found.`);

        const toolCallResults: ToolCallResult[] = await Promise.all(toolCallRequests.map(async request => {
            addStatusMessage(`[${plan.agentName}] Executing tool: ${request.toolName}`);
            
            if (!agentDef.tools.includes(request.toolName)) {
                throw new Error(`Agent ${plan.agentName} is not authorized to use tool ${request.toolName}.`);
            }
            
            const parsedParameters = JSON.parse(request.parameters);
            const result = await executeTool(request.toolName, parsedParameters);

            return {
                toolName: request.toolName,
                toolInput: request.parameters,
                toolOutput: result.output,
                toolOutputSummary: result.summary,
            };
        }));
        
        const synthesizedResponse = await synthesizeResults(plan.agentName, plan.task, toolCallResults, addStatusMessage);

        return {
            agentName: plan.agentName,
            naturalLanguageTask: plan.task,
            toolCalls: toolCallResults,
            synthesizedResponse: synthesizedResponse,
            status: 'success'
        };

    } catch (error) {
        console.error(`Error in agent ${plan.agentName}:`, error);
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
        throw new AgentFailureError(errorMessage, { agentName: plan.agentName, task: plan.task, error: errorMessage });
    }
};

export const runReportSynthesizer = async (query: string, agentFindings: AgentFinding[]): Promise<Omit<Report, 'agentFindings' | 'failedAgents' | 'executionTrace'>> => {
    const prompt = `
        You are FINTEL, a multi-agent AI coordinator. Your final job is to synthesize the findings from your specialized agents into a cohesive, user-facing report.

        Original User Query: "${query}"

        Agent Findings:
        ${JSON.stringify(agentFindings, null, 2)}

        Instructions:
        1.  **Synthesize**: Review all agent findings and the original query.
        2.  **Write Executive Summary**: Create a high-level summary that combines the key insights.
        3.  **Identify Cross-Agent Insights**: Find connections, correlations, or contradictions between the findings of different agents.
        4.  **Formulate Recommendations**: Based on the combined analysis, provide clear, actionable recommendations.
        5.  **Assess Risks**: Detail any risks or downsides identified.
        6.  **Estimate Confidence**: Provide a confidence score (0.0-1.0) and notes on data quality based on the inputs.
        7.  **Produce JSON**: Generate the report sections as a single, valid JSON object matching the required schema.
    `;
     try {
        return await callGeminiApi(prompt, 'report');
    } catch (error) {
        console.error("Error in Report Synthesizer:", error);
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
        throw new Error(`The AI failed to synthesize the final report. Reason: ${errorMessage}`);
    }
};