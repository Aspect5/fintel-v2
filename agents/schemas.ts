

// This file centralizes the JSON schemas used to enforce structured
// output from the Gemini API when called via the REST endpoint.

export const planSchema = {
    type: 'OBJECT',
    properties: {
        analysis: { type: 'STRING', description: "Your reasoning for the chosen agents and tasks." },
        plan: {
            type: 'ARRAY',
            description: "A plan of which specialized agents to invoke for the user's query.",
            items: {
                type: 'OBJECT',
                properties: {
                    agentName: { type: 'STRING', description: "The name of the agent to invoke from the available list." },
                    task: { type: 'STRING', description: "The specific, natural-language task for that agent to perform." },
                },
                required: ["agentName", "task"],
            },
        }
    },
    required: ["analysis", "plan"]
};

export const agentToolCallSchema = {
    type: 'OBJECT',
    properties: {
        toolCalls: {
            type: 'ARRAY',
            description: "An array of tool calls the agent wants to make.",
            items: {
                type: 'OBJECT',
                properties: {
                    toolName: { type: 'STRING', description: "The name of the tool to call." },
                    parameters: { 
                        type: 'STRING',
                        description: "A JSON string representing an object of parameters for the tool call. For example: \"{\\\"ticker\\\":\\\"GOOGL\\\"}\""
                    },
                },
                required: ["toolName", "parameters"],
            },
        },
    },
    required: ["toolCalls"],
};

export const agentFinalResponseSchema = {
    type: 'OBJECT',
    properties: {
        finalResponse: {
            type: 'STRING',
            description: "The final, synthesized response from the agent after reviewing tool results.",
        },
    },
    required: ["finalResponse"],
};

export const reportSynthesizerSchema = {
    type: 'OBJECT',
    properties: {
        executiveSummary: { type: 'STRING' },
        crossAgentInsights: { type: 'STRING' },
        actionableRecommendations: { type: 'ARRAY', items: { type: 'STRING' } },
        riskAssessment: { type: 'STRING' },
        confidenceLevel: { type: 'NUMBER', description: "A value between 0.0 and 1.0." },
        dataQualityNotes: { type: 'STRING' },
    },
    required: ["executiveSummary", "crossAgentInsights", "actionableRecommendations", "riskAssessment", "confidenceLevel", "dataQualityNotes"],
};
