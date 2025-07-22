import { FRED_API_KEY } from '../config';
import { useApiKeyStore } from '../store';

const BASE_URL = 'https://api.stlouisfed.org/fred';

async function callFredApi(endpoint: string, params: Record<string, string>) {
    const apiKey = useApiKeyStore.getState().fredApiKey || FRED_API_KEY;
    if (!apiKey) {
        throw new Error("FRED API key has not been set. Please provide your key to proceed.");
    }

    const queryParams = new URLSearchParams({ ...params, api_key: apiKey, file_type: 'json' });
    const url = `${BASE_URL}/${endpoint}?${queryParams}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`FRED API error! Status: ${response.status}`);
        }
        const data = await response.json();
        if (data.error_message) {
            throw new Error(`FRED API Error: ${data.error_message}`);
        }
        return data;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
        console.error(`FRED API call failed:`, errorMessage);
        throw new Error(`API call to FRED failed: ${errorMessage}`);
    }
}

export const getFredSeries = (seriesId: string, limit: number) => callFredApi('series/observations', { series_id: seriesId, limit: limit.toString(), sort_order: 'desc' });
