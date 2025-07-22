import { AgentFailure } from '../types';
import { ControlFlowProvider } from '../store';

// This should be the public URL of your backend service from the Cloud Workstation
const BACKEND_URL = "https://5001-firebase-fintel-v2-1753205806440.cluster-2xid2zxbenc4ixa74rpk7q7fyk.cloudworkstations.dev";

export class AgentFailureError extends Error {
    payload: AgentFailure;
    constructor(message: string, payload: AgentFailure) {
        super(message);
        this.name = 'AgentFailureError';
        this.payload = payload;
    }
}

export const runAgent = async (
    query: string,
    provider: ControlFlowProvider,
    baseUrl?: string
): Promise<{ output: string; trace: any }> => {
    // FIX: Changed the endpoint to /api/run-workflow to match the backend
    const response = await fetch(`${BACKEND_URL}/api/run-workflow`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query,
            provider,
            baseUrl,
        }),
        // This is required for Google Cloud Workstations authentication
        credentials: 'include',
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({
            // The backend returns 'error', but the frontend expects 'output'
            // We'll provide a generic message if parsing fails.
            output: 'An unknown server error occurred.', 
        }));
        // Use errorData.error if it exists, otherwise use a default
        throw new Error(errorData.error || 'Failed to run agent via backend.');
    }
    
    // The backend returns `result` and `trace`, but the frontend expects `output` and `trace`
    // We remap the response here to match what the frontend component expects.
    const data = await response.json();
    return {
      output: data.result,
      trace: data.trace
    };
};