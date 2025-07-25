// In hooks/useWorkflowStatus.ts
import { useState, useEffect, useCallback } from 'react';
import { WorkflowStatus } from '../types';

export const useWorkflowStatus = (workflowId: string | null, initialStateSet: boolean) => {
    const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);

    const fetchStatus = useCallback(async () => {
        if (!workflowId) return;
        
        try {
            const response = await fetch(`/api/workflow-status/${workflowId}`);
            if (response.ok) {
                const status = await response.json();
                
                // Add debug logging
                console.log(`[WorkflowStatus] Fetched status for ${workflowId}:`, {
                    status: status.status,
                    nodes: status.nodes?.length || 0,
                    edges: status.edges?.length || 0
                });
                
                if (status && status.nodes && status.edges) {
                    setWorkflowStatus(status);
                } else {
                    console.warn('[WorkflowStatus] Incomplete workflow status received:', status);
                }
            }
        } catch (err) {
            console.error('[WorkflowStatus] Failed to fetch workflow status:', err);
        }
    }, [workflowId]);

    // Polling effect
    useEffect(() => {
        if (!workflowId || !initialStateSet) {
            return; // Don't start polling until we have an ID and the initial state is set
        }

        console.log(`[WorkflowStatus] Starting to poll for workflow: ${workflowId}`);
        const interval = setInterval(() => {
            if (workflowStatus?.status === 'completed' || workflowStatus?.status === 'failed') {
                console.log(`[WorkflowStatus] Workflow ${workflowId} finished, stopping polling`);
                clearInterval(interval);
                return;
            }
            fetchStatus();
        }, 1000);

        return () => clearInterval(interval);
    }, [workflowId, initialStateSet, fetchStatus, workflowStatus?.status]);

    return { workflowStatus, setWorkflowStatus };
};
