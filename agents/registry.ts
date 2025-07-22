export interface AgentDefinition {
    name: string;
    description: string;
    instructions: string;
    tools: string[]; // List of tool names this agent can use
}

export const agentRegistry: AgentDefinition[] = [
    {
        name: "MarketAnalyst",
        description: "Specializes in analyzing financial markets, securities, and economic trends.",
        instructions: "You are an expert market analyst. Your goal is to provide insights into market conditions and security performance using the tools available to you.",
        tools: ["get_market_data", "get_economic_data_from_alpha_vantage", "analyze_tariff_impact", "get_company_overview", "get_news_sentiment"],
    },
    {
        name: "BudgetAnalyzer",
        description: "Specializes in analyzing organizational budgets and spending data.",
        instructions: "You are a meticulous budget analyst. You scrutinize spending data to find trends, anomalies, and insights for financial planning.",
        tools: ["analyze_spending_trends"],
    },
    {
        name: "EconomicForecaster",
        description: "Specializes in macro-economic trends and forecasting.",
        instructions: "You are an expert economic forecaster. Your primary goal is to provide a comprehensive outlook on economic conditions. To do this, you must analyze historical trends. Use the `get_economic_data_from_fred` tool to fetch time series data (e.g., the last 12-24 months for monthly data like CPI, or 8-12 quarters for quarterly data like GDP). Analyze the retrieved series to identify growth rates, momentum, and inflection points to support your forecast. Do not make a forecast based on a single data point.",
        tools: ["get_economic_data_from_alpha_vantage", "get_economic_data_from_fred", "analyze_tariff_impact"],
    },
    {
        name: "TechnologyInvestmentAnalyst",
        description: "Specializes in the financials of the technology sector.",
        instructions: "You are a tech investment analyst. You evaluate technology companies and trends based on financial data.",
        tools: ["get_market_data", "get_company_overview", "get_news_sentiment"],
    },
];

const agentMap = new Map<string, AgentDefinition>(agentRegistry.map(agent => [agent.name, agent]));

export const getAgentDefinition = (name: string): AgentDefinition | undefined => {
    return agentMap.get(name);
};