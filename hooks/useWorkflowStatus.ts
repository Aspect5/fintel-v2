// In hooks/useWorkflowStatus.ts
import { useState, useEffect, useCallback } from 'react';
import { WorkflowStatus } from '../types';

export const useWorkflowStatus = (workflowId: string | null) => {
    const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);

    const fetchStatus = useCallback(async () => {
        if (!workflowId) return;
        
        try {
            const response = await fetch(`/api/workflow-status/${workflowId}`);
            if (response.ok) {
                const status = await response.json();
                
                if (status && status.nodes && status.edges) {
                    setWorkflowStatus(status);
                } else {
                    console.warn('Incomplete workflow status received:', status);
                }
            }
        } catch (err) {
            console.error('Failed to fetch workflow status:', err);
        }
    }, [workflowId]);

    useEffect(() => {
        if (!workflowId) return;

        const interval = setInterval(() => {
            if (workflowStatus?.status === 'completed' || workflowStatus?.status === 'failed') {
                clearInterval(interval);
                return;
            }
            fetchStatus();
        }, 1000);

        return () => clearInterval(interval);
    }, [workflowId, fetchStatus, workflowStatus]);

    return { workflowStatus };
};