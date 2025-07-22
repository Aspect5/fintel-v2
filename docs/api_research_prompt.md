# Google Deep Research Prompt: Finding Real-World APIs for FINTEL

You are an expert AI research assistant. Your task is to analyze the architecture of a prototype application called FINTEL and conduct deep research to find suitable, real-world APIs to replace its currently mocked data functionalities. The final output should be a detailed report that a senior frontend engineer can use to integrate these APIs into the application.

## 1. Project Overview: FINTEL

**FINTEL** is a Financial Intelligence Assistant. It's a sophisticated, modular multi-agent AI system built with React, TypeScript, and the Google Gemini API. It uses a coordinator-driven approach for comprehensive financial and market analysis, generating structured, actionable reports.

### Core Workflow:

1.  **Coordinator Planner**: A user provides a query (e.g., "What is the impact of a 10% tariff on the automotive industry?"). An LLM-based coordinator analyzes the query and creates a plan, selecting specialized agents to handle different parts of the task.
2.  **Agent Execution**: The selected agents run in parallel. Each agent is a specialized LLM persona with access to a specific set of "tools". These tools are currently mocked functions that return hardcoded data.
3.  **Report Synthesizer**: Another LLM-based component collects the findings from all successful agents and synthesizes them into a single, comprehensive financial report.

### Key Technologies:

*   **Frontend**: React, TypeScript, ReactFlow (for workflow visualization)
*   **AI**: `@google/genai` (Google Gemini API)
*   **Future Direction**: The user wants to integrate real APIs using the **Model Context Protocol (MCP)**. This means the selected APIs will eventually be wrapped in an MCP-compliant server. Your recommendations should be compatible with this goal, favoring simple RESTful APIs with clear JSON responses.

---

## 2. Current Architecture & Files of Interest

To understand what needs to be replaced, here is a summary of the relevant parts of the codebase.

### `agents/registry.ts`: Agent Definitions

This file defines the available agents, their specializations, and which tools they are allowed to use.

```typescript
// Example content from agents/registry.ts
export const agentRegistry: AgentDefinition[] = [
    {
        name: "MarketAnalyst",
        description: "Specializes in analyzing financial markets, securities, and economic trends.",
        tools: ["get_market_data", "get_economic_data", "analyze_tariff_impact"],
    },
    {
        name: "BudgetAnalyzer",
        description: "Specializes in analyzing organizational budgets and spending data.",
        tools: ["analyze_spending_trends"],
    },
    {
        name: "EconomicForecaster",
        description: "Specializes in macro-economic trends and forecasting.",
        tools: ["get_economic_data", "analyze_tariff_impact"],
    },
    // ... other agents
];
```

### `tools/financialTools.ts`: Tool Definitions & Mocked Implementations

This is the **most important file**. It defines the tools and their mocked `execute` functions. **Your primary goal is to find APIs to replace the logic inside these `execute` functions.**

```typescript
// Example content from tools/financialTools.ts

// Tool: get_market_data
// Goal: Retrieves the latest market data (price, volume, etc.) for a given stock ticker.
// Mocked Implementation: Returns random price and volume.
// Parameters: { ticker: string }

// Tool: get_economic_data
// Goal: Retrieves a key macroeconomic indicator for a specific region.
// Mocked Implementation: Returns random values for 'CPI', 'GDP Growth', etc.
// Parameters: { indicator: string, region: string }

// Tool: analyze_tariff_impact
// Goal: Models the potential macroeconomic impact of tariffs.
// Mocked Implementation: Simulates impact based on tariff rate.
// This is more analytical and may not be a direct 1:1 API call, but it will need real data (like GDP) as input.

// Tool: analyze_spending_trends
// Goal: Analyzes internal company spending data.
// Mocked Implementation: Returns random spending data.
// This is for internal data and likely cannot be replaced by a public API.
```

---

## 3. Your Task and Instructions

Your mission is to find and evaluate public APIs to replace the mocked implementations in `tools/financialTools.ts`.

### API Selection Criteria:

1.  **Reliability & Popularity**: Focus on well-known, stable, and maintained APIs.
2.  **Cost-Effectiveness**: Prioritize APIs that are **free** or have a **generous free tier** suitable for development. Clearly document the limits of the free tier.
3.  **Ease of Integration**: The API should use simple authentication (e.g., API key in header/query params) and return predictable JSON responses.
4.  **Data Coverage**: The API must provide the data required by the tool (e.g., stock data from major exchanges, economic data for the USA and Eurozone).

### Output Format:

Please provide your findings in a structured **Markdown report**. The report should be organized by the tool that needs replacement.

---

## **API Research Report for FINTEL**

### Tool: `get_market_data`

For this tool, research APIs that provide real-time or delayed stock market data, including price, volume, and daily change for stock tickers.

**Recommendation 1: [API Name]**
*   **Website**: [URL]
*   **Documentation**: [URL]
*   **Key Features**: [Explain why it's a good choice based on the criteria.]
*   **Pricing/Free Tier**: [Describe the free tier and its limitations, e.g., "X calls/minute, Y calls/day".]
*   **TypeScript Implementation Snippet**:
    ```typescript
    // A brief, complete example using fetch to get data for 'AAPL'
    const getStockData = async (ticker: string, apiKey: string) => {
      const response = await fetch(`...`); // API call
      const data = await response.json();
      console.log(data);
      return data;
    }
    ```
*   **MCP Mapping Suggestion**: [Explain how the API endpoint and its parameters map to the `get_market_data` tool definition.]

**(Provide 1-2 more recommendations for this tool if available)**

### Tool: `get_economic_data`

For this tool, research APIs that provide key macroeconomic indicators like CPI (Consumer Price Index), GDP Growth, and Unemployment Rate for major regions like the USA and Eurozone.

**Recommendation 1: [API Name]**
*   **Website**: [URL]
*   **Documentation**: [URL]
*   **Key Features**: [Explain why it's a good choice.]
*   **Pricing/Free Tier**: [Describe the free tier and its limitations.]
*   **TypeScript Implementation Snippet**:
    ```typescript
    // A brief, complete example using fetch to get CPI for the USA
    const getCPI = async (region: string, apiKey:string) => {
       const response = await fetch(`...`); // API call
       const data = await response.json();
       console.log(data);
       return data;
    }
    ```
*   **MCP Mapping Suggestion**: [Explain how the API endpoint and its parameters map to the `get_economic_data` tool definition.]

**(Provide 1-2 more recommendations for this tool if available)**

### Analytical & Internal Tools

**Tool: `analyze_tariff_impact`**
*   **Analysis**: This tool is analytical and won't have a direct 1:1 API replacement. However, it *consumes* economic data. Recommend which of the previously found APIs (`get_economic_data`) would be the best data source to feed into the LLM prompt for this tool's implementation.

**Tool: `analyze_spending_trends`**
*   **Analysis**: This tool is designed for internal data. State that it cannot be replaced by a public API and would typically connect to a company's internal database or a private financial API (e.g., Plaid, Stripe) which is beyond the scope of this research.
