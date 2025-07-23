import { ControlFlowProvider } from '../store';

export const runAgent = async (
    query: string,
    provider: ControlFlowProvider,
    baseUrl?: string
): Promise<{ output: string; trace: any }> => {
    console.log('🚀 Starting request to /api/run-workflow');
    console.log('📝 Request payload:', { query, provider, baseUrl });
    
    try {
        const response = await fetch('/api/run-workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                provider,
                baseUrl,
            }),
        });

        console.log('📡 Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Error response:', errorText);
            throw new Error(`Request failed with status ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('✅ Success! Full response:', data);
        
        return {
            output: data.result,
            trace: data.trace
        };
        
    } catch (error) {
        console.error('❌ Fetch error:', error);
        
        if (error instanceof Error) {
            throw error;
        } else {
            throw new Error(`Unknown error: ${String(error)}`);
        }
    }
};
