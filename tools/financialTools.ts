import { Tool, ToolRegistry } from "./toolTypes";

// The secure proxy base URL. All tool calls will go through our own backend.
const PROXY_BASE_URL = '/api/proxy';

// --- Tool Implementations using the Secure Backend Proxy ---

const get_market_data: Tool = {
    name: "get_market_data",
    description: "Retrieves the latest daily market data (price, volume, change) for a stock ticker.",
    parameters: {
        type: "OBJECT",
        properties: { ticker: { type: "STRING", description: "The stock ticker symbol (e.g., 'AAPL')." } },
        required: ["ticker"],
    },
    execute: async ({ ticker }) => {
        const params = new URLSearchParams({ function: 'GLOBAL_QUOTE', symbol: ticker });
        const url = `${PROXY_BASE_URL}/alpha_vantage?${params}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Backend proxy error! Status: ${response.status}`);
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            const quoteData = data['Global Quote'];
            if (!quoteData || Object.keys(quoteData).length === 0) {
                 if(data.Note) { throw new Error(`Alpha Vantage API Note: ${data.Note}`); }
                 throw new Error(`No data received for ticker: ${ticker}.`);
            }

            const output = {
                ticker: quoteData['01. symbol'],
                price: parseFloat(quoteData['05. price']),
                volume: parseInt(quoteData['06. volume'], 10),
                change: parseFloat(quoteData['09. change']),
            };
            
            return {
                output,
                summary: `Successfully fetched market data for ${ticker}. Price: $${output.price.toFixed(2)}.`
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
            throw new Error(`Market data tool failed for ${ticker}: ${errorMessage}`);
        }
    },
};

const get_economic_data_from_fred: Tool = {
    name: "get_economic_data_from_fred",
    description: "Retrieves a time series of a specific economic data series from FRED.",
    parameters: {
        type: "OBJECT",
        properties: {
            series_id: { type: "STRING", description: "The FRED series ID to fetch (e.g., 'GNPCA')." },
            limit: { type: "NUMBER", description: "The number of recent data points to retrieve. Default is 10."}
        },
        required: ["series_id"],
    },
    execute: async ({ series_id, limit = 10 }) => {
        const params = new URLSearchParams({ series_id, limit: limit.toString(), sort_order: 'desc' });
        const url = `${PROXY_BASE_URL}/fred?${params}`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Backend proxy error! Status: ${response.status}`);
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            if (!data.observations || data.observations.length === 0) {
                throw new Error(`No data received from FRED for series ID: ${series_id}.`);
            }
            const output = {
                series_id,
                series: data.observations.map((obs: any) => ({ date: obs.date, value: obs.value }))
            };
            return {
                output,
                summary: `Successfully fetched ${output.series.length} data points for FRED series ${series_id}.`
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
            throw new Error(`FRED tool failed for ${series_id}: ${errorMessage}`);
        }
    }
};

// ... other tools like get_company_overview would be refactored similarly ...

// Register all tools
export const toolRegistry: ToolRegistry = new Map();
[get_market_data, get_economic_data_from_fred].forEach(tool => {
    toolRegistry.set(tool.name, tool);
});

// Main executor function for client-side (Gemini Visual) tools
export const executeTool = async (toolName: string, parameters: any): Promise<{ output: any; summary: string }> => {
    const tool = toolRegistry.get(toolName);
    if (!tool) {
        throw new Error(`Tool "${toolName}" not found in registry.`);
    }
    return tool.execute(parameters);
};
