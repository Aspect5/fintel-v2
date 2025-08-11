import { ControlFlowProvider } from '@/stores/store';

// Define the payload interface to include optional base_url
interface WorkflowPayload {
    query: string;
    provider: ControlFlowProvider;
    workflow: string;
    base_url?: string; // Optional property for local provider
}

export const runAgent = async (
    query: string,
    provider: ControlFlowProvider,
    baseUrl?: string
): Promise<{ output: string; trace: any }> => {
    const DEBUG = import.meta.env.MODE === 'development' && (window as any).__DEBUG__;
    if (DEBUG) {
        console.log('🚀 Starting request to /api/run-workflow');
        console.log('📝 Request payload:', { query, provider, baseUrl });
    }
    
    // Create payload with proper typing
    const payload: WorkflowPayload = {
        query,
        provider,
        workflow: 'enhanced_simplified' // Use enhanced simplified workflow
    };
    
    // Add base_url only if provider is local and baseUrl is provided
    if (provider === 'local' && baseUrl) {
        payload.base_url = baseUrl;
    }
    
    try {
        const response = await fetch('/api/run-workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (DEBUG) console.log('📡 Response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            if (DEBUG) console.error('❌ Error response:', errorData);
            
            const errorMessage = errorData.error || `Request failed with status ${response.status}`;
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        if (DEBUG) console.log('✅ Success! Full response:', data);
        
        return {
            output: data.result || 'No result returned',
            trace: data.trace || 'No trace available'
        };
        
    } catch (error) {
        if (DEBUG) console.error('❌ Fetch error:', error);
        
        if (error instanceof Error) {
            throw error;
        } else {
            throw new Error(`Unknown error: ${String(error)}`);
        }
    }
};

// Add function to fetch available tools (as mentioned in the refactoring plan)
export const fetchAvailableTools = async (): Promise<Record<string, any>> => {
    try {
        const response = await fetch('/api/tools');
        if (!response.ok) {
            throw new Error(`Failed to fetch tools: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch available tools:', error);
        return {};
    }
};