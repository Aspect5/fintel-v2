// In hooks/useWorkflowStatus.ts
import { useEffect, useCallback } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';

export const useWorkflowStatus = (workflowId: string | null) => {
    const { updateWorkflowStatus, status: workflowStatus } = useWorkflowStore(state => ({
        updateWorkflowStatus: state.updateWorkflowStatus,
        status: state.status,
    }));

    const fetchStatus = useCallback(async () => {
        if (!workflowId) return;
        
        try {
            const response = await fetch(`/api/workflow-status/${workflowId}`);
            if (response.ok) {
                const status = await response.json();
                
                // Comprehensive logging to track data flow
                console.log(`[useWorkflowStatus] Raw backend data for ${workflowId}:`, status);
                console.log(`[useWorkflowStatus] Data breakdown:`, {
                    status: status.status,
                    hasNodes: !!status.nodes,
                    hasEdges: !!status.edges,
                    nodesCount: status.nodes?.length || 0,
                    edgesCount: status.edges?.length || 0,
                    hasGraph: !!status.workflow_graph,
                    hasResult: !!status.result,
                    hasEnhancedResult: !!status.enhanced_result,
                    hasAgentInvocations: !!status.agent_invocations,
                    hasToolCalls: !!status.tool_calls,
                    hasTrace: !!status.trace,
                    currentTask: status.current_task,
                    executionTime: status.execution_time,
                    resultType: typeof status.result,
                    enhancedResultType: typeof status.enhanced_result,
                });

                // Update the store directly
                updateWorkflowStatus(status);
                
                // Log after store update
                setTimeout(() => {
                    const storeState = useWorkflowStore.getState();
                    console.log(`[useWorkflowStatus] Store state after update:`, {
                        storeStatus: storeState.status,
                        storeHasResult: !!storeState.result,
                        storeHasEnhancedResult: !!storeState.enhanced_result,
                        storeHasAgentInvocations: !!storeState.agent_invocations,
                    });
                }, 0);
            }
        } catch (err) {
            console.error('[useWorkflowStatus] Failed to fetch workflow status:', err);
        }
    }, [workflowId, updateWorkflowStatus]);

    // Initial fetch when the component mounts or workflowId changes
    useEffect(() => {
        if (workflowId) {
            fetchStatus();
        }
    }, [workflowId, fetchStatus]);

    // Polling effect
    useEffect(() => {
        if (!workflowId) {
            return;
        }

        console.log(`[useWorkflowStatus] Starting to poll for workflow: ${workflowId}`);
        const interval = setInterval(() => {
            if (workflowStatus === 'completed' || workflowStatus === 'failed') {
                console.log(`[useWorkflowStatus] Workflow ${workflowId} finished with status: ${workflowStatus}. Stopping polling.`);
                clearInterval(interval);
                return;
            }
            fetchStatus();
        }, 2000); // Polling interval set to 2 seconds

        return () => {
            console.log(`[useWorkflowStatus] Cleaning up polling for ${workflowId}`);
            clearInterval(interval);
        };
    }, [workflowId, fetchStatus, workflowStatus]);

    // This hook no longer returns anything as it interacts directly with the store
};