import { Tool, ToolRegistry } from "./toolTypes";

/**
 * The secure proxy base URL.
 * All tool calls will go through our own backend, which securely attaches API keys.
 */
const PROXY_BASE_URL = '/api/proxy';

/**
 * A standardized helper function to call the backend proxy.
 * This reduces code duplication and centralizes error handling for all tool executions.
 *
 * @param provider - The API provider (e.g., 'alpha_vantage', 'fred').
 * @param params - The URL search parameters to forward to the provider.
 * @returns The JSON response from the proxied API.
 * @throws An error if the network request or the proxied API call fails.
 */
const callProxy = async (provider: string, params: URLSearchParams) => {
    const url = `${PROXY_BASE_URL}/${provider}?${params}`;
    
    try {
        const response = await fetch(url);

        // Attempt to parse JSON error from the backend for more specific messages
        if (!response.ok) {
            const errorData = await response.json().catch(() => null); // Gracefully handle non-JSON responses
            const message = errorData?.error || `Backend proxy error! Status: ${response.status}`;
            throw new Error(message);
        }

        const data = await response.json();

        // Handle API-specific error messages or informational notes
        if (data.error) throw new Error(data.error);
        if (data.Note) throw new Error(`API provider note: ${data.Note}`);
        
        return data;

    } catch (error) {
        // Re-throw with a more informative message for easier debugging
        const errorMessage = error instanceof Error ? error.message : "An unknown network error occurred.";
        throw new Error(`Failed to call proxy for '${provider}': ${errorMessage}`);
    }
};

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
        const data = await callProxy('alpha_vantage', params);

        const quoteData = data['Global Quote'];
        if (!quoteData || Object.keys(quoteData).length === 0) {
            throw new Error(`No market data received for ticker: ${ticker}.`);
        }

        const output = {
            ticker: quoteData['01. symbol'],
            price: parseFloat(quoteData['05. price']),
            volume: parseInt(quoteData['06. volume'], 10),
            change_percent: quoteData['10. change percent'],
        };
        
        return {
            output,
            summary: `[LIVE] Market data for ${output.ticker}: Price is $${output.price.toFixed(2)} (${output.change_percent}).`
        };
    },
};

const get_company_overview: Tool = {
    name: "get_company_overview",
    description: "Fetches key information about a company, including its market cap, P/E ratio, and description.",
    parameters: {
        type: "OBJECT",
        properties: { ticker: { type: "STRING", description: "The stock ticker symbol (e.g., 'GOOGL')." } },
        required: ["ticker"],
    },
    execute: async ({ ticker }) => {
        const params = new URLSearchParams({ function: 'OVERVIEW', symbol: ticker });
        const data = await callProxy('alpha_vantage', params);

        if (!data.Symbol) {
            throw new Error(`No company overview data found for ticker: ${ticker}. It may be an invalid symbol.`);
        }

        const output = {
            ticker: data.Symbol,
            name: data.Name,
            description: data.Description,
            market_cap: parseInt(data.MarketCapitalization, 10),
            pe_ratio: parseFloat(data.PERatio),
            eps: parseFloat(data.EPS),
        };

        return {
            output,
            summary: `[INFO] Overview for ${output.name} (${output.ticker}): Market Cap is $${(output.market_cap / 1e9).toFixed(2)}B, P/E Ratio is ${output.pe_ratio}.`
        };
    },
};

const search_news: Tool = {
    name: "search_news",
    description: "Searches for recent news articles and sentiment scores related to specific stock tickers or topics.",
    parameters: {
        type: "OBJECT",
        properties: {
            tickers: { type: "STRING", description: "A comma-separated list of stock tickers to search (e.g., 'COIN,CRYPTO:BTC')." },
            topics: { type: "STRING", description: "A comma-separated list of topics (e.g., 'TECHNOLOGY,FINANCE')." }
        },
    },
    execute: async ({ tickers, topics }) => {
        const params = new URLSearchParams({
            function: 'NEWS_SENTIMENT',
            limit: "10" // Fetch 10 recent articles
        });

        if (tickers) params.set('tickers', tickers);
        if (topics) params.set('topics', topics);

        // Either tickers or topics must be provided.
        if (!tickers && !topics) {
            throw new Error("Search query is required. Please provide at least one ticker or topic.");
        }
        
        const data = await callProxy('alpha_vantage', params);
        const articles = data.feed || [];

        if (articles.length === 0) {
            return { output: [], summary: "[NEWS] No relevant news articles were found for the query." };
        }

        const output = articles.map((article: any) => ({
            title: article.title,
            url: article.url,
            summary: article.summary,
            source: article.source,
            overall_sentiment: article.overall_sentiment_label,
        }));
        
        return {
            output,
            summary: `[NEWS] Found ${output.length} news articles related to the query.`
        };
    }
};

const get_economic_data_from_fred: Tool = {
    name: "get_economic_data_from_fred",
    description: "Retrieves a time series for a specific economic indicator from FRED (Federal Reserve Economic Data).",
    parameters: {
        type: "OBJECT",
        properties: {
            series_id: { type: "STRING", description: "The FRED series ID to fetch (e.g., 'GNPCA', 'UNRATE')." },
            limit: { type: "NUMBER", description: "The number of recent data points to retrieve. Default is 10." }
        },
        required: ["series_id"],
    },
    execute: async ({ series_id, limit = 10 }) => {
        const params = new URLSearchParams({
            series_id,
            limit: limit.toString(),
            sort_order: 'desc',
            file_type: 'json'
        });

        const data = await callProxy('fred', params);
        if (!data.observations || data.observations.length === 0) {
            throw new Error(`No data received from FRED for series ID: ${series_id}.`);
        }
        
        const output = {
            series_id,
            series: data.observations.map((obs: any) => ({ date: obs.date, value: obs.value }))
        };

        return {
            output,
            summary: `[ECO] Fetched ${output.series.length} data points for FRED series ${series_id}. The most recent value is ${output.series[0].value} on ${output.series[0].date}.`
        };
    }
};

// --- Tool Registry and Executor ---

// Create and populate the tool registry.
export const toolRegistry: ToolRegistry = new Map();
[
    get_market_data,
    get_company_overview,
    search_news,
    get_economic_data_from_fred
].forEach(tool => {
    toolRegistry.set(tool.name, tool);
});

/**
 * Main executor function that finds and runs a tool from the registry.
 * @param toolName - The name of the tool to execute.
 * @param parameters - The parameters to pass to the tool's execute function.
 * @returns A promise that resolves to the tool's output and summary.
 */
export const executeTool = async (toolName: string, parameters: any): Promise<{ output: any; summary: string }> => {
    const tool = toolRegistry.get(toolName);
    if (!tool) {
        throw new Error(`Tool "${toolName}" not found in registry.`);
    }
    // Wrap execution in a try-catch block to handle errors from individual tools
    try {
        return await tool.execute(parameters);
    } catch (error) {
        console.error(`Error executing tool '${toolName}':`, error);
        // Re-throw a standardized error object for the UI to handle
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred during tool execution.";
        throw new Error(`Tool Error: ${errorMessage}`);
    }
};