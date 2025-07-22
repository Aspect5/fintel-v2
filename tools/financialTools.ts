import { Tool, ToolRegistry } from "./toolTypes";
import { useStore } from '../store';
import * as alphaVantage from '../services/alphaVantageService';
import * as fred from '../services/fredService';
import { ALPHA_VANTAGE_API_KEY, FRED_API_KEY } from "../config";

export const toolRegistry: ToolRegistry = new Map();

// --- Tool Implementations with Client-Side Execution ---

const get_market_data: Tool = {
    name: "get_market_data",
    description: "Retrieves the latest daily market data (price, volume, change) for a stock ticker. Powered by Alpha Vantage.",
    parameters: {
        type: "OBJECT",
        properties: {
            ticker: { type: "STRING", description: "The stock ticker symbol (e.g., 'AAPL')." },
        },
        required: ["ticker"],
    },
    execute: async ({ ticker }) => {
        const apiKey = useStore.getState().alphaVantageApiKey || ALPHA_VANTAGE_API_KEY;
        if (!apiKey) {
            console.warn("ALPHA_VANTAGE_API_KEY not found. Falling back to mock data for get_market_data.");
            const price = (Math.random() * 200 + 100).toFixed(2);
            return {
                output: { ticker, price, volume: Math.floor(Math.random() * 10e6 + 1e6), change: (Math.random() * 10 - 5).toFixed(2) },
                summary: `[MOCK] Fetched market data for ${ticker}. Current price is $${price}.`
            };
        }

        try {
            const data = await alphaVantage.getGlobalQuote(ticker);
            const quoteData = data['Global Quote'];

            if (!quoteData || Object.keys(quoteData).length === 0) {
                 if(data.Note) { throw new Error(`Alpha Vantage API Note: ${data.Note}`); }
                 throw new Error(`No data received from Alpha Vantage for ticker: ${ticker}. It may be an invalid symbol.`);
            }

            const output = {
                ticker: quoteData['01. symbol'],
                price: parseFloat(quoteData['05. price']),
                volume: parseInt(quoteData['06. volume'], 10),
                change: parseFloat(quoteData['09. change']),
                changePercent: quoteData['10. change percent'],
            };
            
            return {
                output,
                summary: `[LIVE] Successfully fetched market data for ${ticker}. Current price is $${output.price.toFixed(2)}.`
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
            console.error(`Failed to fetch stock data for ${ticker}:`, errorMessage);
            throw new Error(`API call to Alpha Vantage failed for ${ticker}: ${errorMessage}`);
        }
    },
};

const get_economic_data_from_alpha_vantage: Tool = {
    name: "get_economic_data_from_alpha_vantage",
    description: "Retrieves a time series of major US macroeconomic indicators from Alpha Vantage (e.g., CPI, GDP, Unemployment Rate). Useful for trend analysis and forecasting.",
    parameters: {
        type: "OBJECT",
        properties: {
            indicator: { type: "STRING", description: "The indicator to fetch. Supported: 'CPI', 'GDP', 'Unemployment'." },
            data_points: { type: "NUMBER", description: "The number of recent data points to retrieve (e.g., 12 for 12 months of CPI data). Default is 1."}
        },
        required: ["indicator"],
    },
     execute: async ({ indicator, data_points = 1 }) => {
        const apiKey = useStore.getState().alphaVantageApiKey || ALPHA_VANTAGE_API_KEY;
        if (!apiKey) {
            console.warn("ALPHA_VANTAGE_API_KEY not found. Falling back to mock data for get_economic_data_from_alpha_vantage.");
             const mockSeries = Array.from({length: data_points}, (_, i) => ({
                date: `2024-0${6-i}-01`,
                value: `${(Math.random() * 4 + 1.5).toFixed(1)}%`
            })).reverse();
            return {
                output: { indicator, region: 'USA', series: mockSeries },
                summary: `[MOCK] The latest ${data_points} data points for ${indicator} for USA were generated.`
            };
        }

        const indicatorMap: { [key: string]: { func: string, interval?: string, key: string, name: string } } = {
            'CPI': { func: 'CPI', interval: 'monthly', key: 'value', name: 'Consumer Price Index' },
            'GDP': { func: 'REAL_GDP', interval: 'quarterly', key: 'value', name: 'Real GDP' },
            'Unemployment': { func: 'UNEMPLOYMENT', key: 'value', name: 'Unemployment Rate'},
        };

        const selectedIndicator = indicatorMap[indicator];
        if (!selectedIndicator) {
            throw new Error(`Unsupported indicator "${indicator}". Supported indicators are: ${Object.keys(indicatorMap).join(', ')}.`);
        }

        try {
            const result = await alphaVantage.getEconomicIndicator(selectedIndicator.func, selectedIndicator.interval);
            if (!result.data || result.data.length === 0) {
                throw new Error(`No data found for indicator ${indicator}.`);
            }
            
            const historicalData = result.data.slice(0, data_points);
            const output = {
                indicator: selectedIndicator.name,
                region: 'USA',
                series: historicalData.map((d: any) => ({ date: d.date, value: d[selectedIndicator.key] }))
            };
            
            return {
                output,
                summary: `[LIVE] Successfully fetched the latest ${output.series.length} data points for ${output.indicator} for the USA.`
            };

        } catch (error) {
             const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
             console.error(`Failed to fetch Alpha Vantage data for ${indicator}:`, error);
             throw new Error(`API call to Alpha Vantage for economic data failed: ${errorMessage}`);
        }
    },
};

const get_economic_data_from_fred: Tool = {
    name: "get_economic_data_from_fred",
    description: "Retrieves a time series of a specific economic data series from FRED (Federal Reserve Economic Data).",
    parameters: {
        type: "OBJECT",
        properties: {
            series_id: { type: "STRING", description: "The FRED series ID to fetch (e.g., 'GNPCA')." },
            data_points: { type: "NUMBER", description: "The number of recent data points to retrieve. Default is 10."}
        },
        required: ["series_id"],
    },
    execute: async ({ series_id, data_points = 10 }) => {
        const apiKey = useStore.getState().fredApiKey || FRED_API_KEY;
        if (!apiKey) {
            console.warn("FRED_API_KEY not found. Falling back to mock data for get_economic_data_from_fred.");
            const mockSeries = Array.from({length: data_points}, (_, i) => ({
                date: `2024-0${6-i}-01`,
                value: (Math.random() * 1000 + 20000).toFixed(2)
            })).reverse();
            return {
                output: { series_id, series: mockSeries },
                summary: `[MOCK] Generated ${data_points} mock data points for FRED series ${series_id}.`
            };
        }

        try {
            const data = await fred.getFredSeries(series_id, data_points);
            if (!data.observations || data.observations.length === 0) {
                throw new Error(`No data received from FRED for series ID: ${series_id}.`);
            }
            const output = {
                series_id,
                series: data.observations.map((obs: any) => ({ date: obs.date, value: obs.value }))
            };
            return {
                output,
                summary: `[LIVE] Successfully fetched the latest ${output.series.length} data points for FRED series ${series_id}.`
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
            console.error(`Failed to fetch FRED data for series ${series_id}:`, errorMessage);
            throw new Error(`API call to FRED failed for ${series_id}: ${errorMessage}`);
        }
    }
};


const get_company_overview: Tool = {
    name: "get_company_overview",
    description: "Fetches fundamental company data, including market cap, P/E ratio, EPS, and a business description.",
    parameters: {
        type: "OBJECT",
        properties: {
            ticker: { type: "STRING", description: "The stock ticker symbol (e.g., 'AAPL')." },
        },
        required: ["ticker"],
    },
    execute: async ({ ticker }) => {
        const apiKey = useStore.getState().alphaVantageApiKey || ALPHA_VANTAGE_API_KEY;
        if (!apiKey) {
            throw new Error("This tool requires an Alpha Vantage API key.");
        }
        try {
            const data = await alphaVantage.getCompanyOverview(ticker);
            if (!data.Symbol) throw new Error(`No company overview data found for ticker: ${ticker}.`);

            const output = {
                ticker: data.Symbol,
                name: data.Name,
                description: data.Description,
                marketCap: `$${(parseInt(data.MarketCapitalization) / 1e9).toFixed(2)}B`,
                peRatio: data.PERatio,
                eps: data.EPS,
                sector: data.Sector,
                industry: data.Industry,
            };

            return {
                output,
                summary: `[LIVE] Fetched company overview for ${output.name} (${output.ticker}). Market Cap: ${output.marketCap}, P/E Ratio: ${output.peRatio}.`
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
            console.error(`Failed to fetch company overview for ${ticker}:`, errorMessage);
            throw new Error(`API call to Alpha Vantage (OVERVIEW) failed for ${ticker}: ${errorMessage}`);
        }
    }
};

const get_news_sentiment: Tool = {
    name: "get_news_sentiment",
    description: "Fetches recent news articles and their sentiment scores for a given stock ticker.",
    parameters: {
        type: "OBJECT",
        properties: {
            ticker: { type: "STRING", description: "The stock ticker symbol (e.g., 'AAPL')." },
        },
        required: ["ticker"],
    },
    execute: async ({ ticker }) => {
        const apiKey = useStore.getState().alphaVantageApiKey || ALPHA_VANTAGE_API_KEY;
        if (!apiKey) {
            throw new Error("This tool requires an Alpha Vantage API key.");
        }
        try {
            const data = await alphaVantage.getNewsSentiment(ticker);
            if (!data.feed || data.feed.length === 0) {
                 return {
                    output: { feed: [], overall_sentiment_label: "Neutral" },
                    summary: `[LIVE] No recent news found for ticker ${ticker}.`
                };
            }
            
            const overallSentimentScore = data.feed[0].overall_sentiment_score; // API provides this on each item
            const overallSentimentLabel = data.feed[0].overall_sentiment_label;

            const top_articles = data.feed.map((item: any) => ({
                title: item.title,
                url: item.url,
                summary: item.summary,
                sentiment_score: item.ticker_sentiment[0]?.ticker_sentiment_score,
                sentiment_label: item.ticker_sentiment[0]?.ticker_sentiment_label,
            }));
            
            const output = {
                overall_sentiment_score: overallSentimentScore,
                overall_sentiment_label: overallSentimentLabel,
                articles: top_articles,
            };
            
            return {
                output,
                summary: `[LIVE] News sentiment for ${ticker} is '${overallSentimentLabel}' based on ${output.articles.length} recent articles.`
            };

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
            console.error(`Failed to fetch news sentiment for ${ticker}:`, errorMessage);
            throw new Error(`API call to Alpha Vantage (NEWS_SENTIMENT) failed for ${ticker}: ${errorMessage}`);
        }
    }
};


const analyze_tariff_impact: Tool = {
    name: "analyze_tariff_impact",
    description: "Analyzes the potential macroeconomic impact of tariffs. This is a synthetic tool that uses an LLM for analysis, not a direct data API. Its insights are derived, not fetched.",
    parameters: {
        type: "OBJECT",
        properties: {
            sector: { type: "STRING", description: "The industrial sector to analyze (e.g., 'Semiconductors', 'Automotive')." },
            tariffRate: { type: "NUMBER", description: "The proposed tariff rate as a decimal (e.g., 0.15 for 15%)." },
            regions: { type: "ARRAY", description: "A list of key regions/countries involved (e.g., ['USA', 'China', 'Eurozone'])." },
        },
        required: ["sector", "tariffRate", "regions"],
    },
    execute: async ({ sector, tariffRate, regions }) => {
        const ratePercent = tariffRate * 100;
        const gdpImpact = -(tariffRate * 0.5).toFixed(2);
        const inflationImpact = (tariffRate * 0.8).toFixed(2);
        const supplyChainDisruption = tariffRate > 0.1 ? 'High' : 'Moderate';

        const output = {
            sector,
            tariffRate,
            regions,
            projected_gdp_impact_percent: gdpImpact,
            projected_inflation_impact_percent: inflationImpact,
            supply_chain_disruption_level: supplyChainDisruption,
        };
        
        const summary = `[SYNTHETIC] Modeled a ${ratePercent}% tariff on the ${sector} sector. Projected GDP impact: ${gdpImpact}%, Inflation impact: ${inflationImpact}%.`;
        
        return { output, summary };
    },
};

const analyze_spending_trends: Tool = {
    name: "analyze_spending_trends",
    description: "Analyzes internal spending data. This tool simulates access to private, proprietary data and is for demonstration purposes only.",
    parameters: {
        type: "OBJECT",
        properties: {
            department: { type: "STRING", description: "The department to analyze (e.g., 'Marketing', 'R&D')." },
            period: { type: "STRING", description: "The time period (e.g., 'Q3 2024')." },
        },
        required: ["department", "period"],
    },
    execute: async ({ department, period }) => {
        const total_spend = (Math.random() * 500000 + 100000).toFixed(2);
        const top_category = ['Software Licenses', 'Cloud Services', 'Contractors'][Math.floor(Math.random()*3)];
        return {
            output: { department, period, total_spend, top_category },
            summary: `[INTERNAL MOCK] Analyzed ${department} spending of $${total_spend} in ${period}, with the highest spending in ${top_category}.`
        };
    },
};


// Register all tools
[get_market_data, get_economic_data_from_alpha_vantage, get_economic_data_from_fred, get_company_overview, get_news_sentiment, analyze_tariff_impact, analyze_spending_trends].forEach(tool => {
    toolRegistry.set(tool.name, tool);
});

// Main executor function for client-side
export const executeTool = async (toolName: string, parameters: any): Promise<{ output: any; summary: string }> => {
    const tool = toolRegistry.get(toolName);
    if (!tool) {
        throw new Error(`Tool "${toolName}" not found in registry.`);
    }

    // Basic validation
    if (tool.parameters.required) {
        for (const reqParam of tool.parameters.required) {
            if (!(reqParam in parameters)) {
                throw new Error(`Missing required parameter "${reqParam}" for tool "${toolName}".`);
            }
        }
    }
    
    return tool.execute(parameters);
};