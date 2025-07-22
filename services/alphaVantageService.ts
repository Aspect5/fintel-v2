import { ALPHA_VANTAGE_API_KEY } from '../config';
import { useApiKeyStore } from '../store';

const BASE_URL = 'https://www.alphavantage.co/query';

async function callAlphaVantageApi(params: Record<string, string>) {
    const apiKey = useApiKeyStore.getState().alphaVantageApiKey || ALPHA_VANTAGE_API_KEY;
    if (!apiKey) {
        throw new Error("Alpha Vantage API key has not been set. Please provide your key to proceed.");
    }

    const queryParams = new URLSearchParams({ ...params, apikey: apiKey });
    const url = `${BASE_URL}?${queryParams}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Alpha Vantage API error! Status: ${response.status}`);
        }
        const data = await response.json();
        if (data.Note) {
            throw new Error(`Alpha Vantage API Note: ${data.Note}`);
        }
        if (data['Error Message']) {
            throw new Error(`Alpha Vantage API Error: ${data['Error Message']}`);
        }
        return data;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
        console.error(`Alpha Vantage API call failed:`, errorMessage);
        throw new Error(`API call to Alpha Vantage failed: ${errorMessage}`);
    }
}

export const getGlobalQuote = (ticker: string) => callAlphaVantageApi({ function: 'GLOBAL_QUOTE', symbol: ticker });
export const getCompanyOverview = (ticker: string) => callAlphaVantageApi({ function: 'OVERVIEW', symbol: ticker });
export const getNewsSentiment = (ticker: string) => callAlphaVantageApi({ function: 'NEWS_SENTIMENT', tickers: ticker, limit: '10' });
export const getEconomicIndicator = (indicator: string, interval?: string) => {
    const params: Record<string, string> = { function: indicator };
    if (interval) {
        params.interval = interval;
    }
    return callAlphaVantageApi(params);
};
