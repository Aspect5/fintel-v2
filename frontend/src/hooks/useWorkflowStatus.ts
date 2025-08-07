// In hooks/useWorkflowStatus.ts
import { useEffect, useCallback } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';
import { createLogger } from '../utils/logger';

const hookLogger = createLogger('useWorkflowStatus');

export const useWorkflowStatus = (workflowId: string | null) => {
    const { updateWorkflowStatus, status: workflowStatus } = useWorkflowStore(state => ({
        updateWorkflowStatus: state.updateWorkflowStatus,
        status: state.status,
    }));



    // Polling effect
    useEffect(() => {
        if (!workflowId) {
            return;
        }

        hookLogger.info('Starting to poll for workflow', { workflowId });
        
        let intervalId: NodeJS.Timeout;
        let shouldContinuePolling = true;
        
        const pollWithErrorHandling = async () => {
            if (!shouldContinuePolling) return;
            
            try {
                const response = await fetch(`/api/workflow-status/${workflowId}`);
                if (!response.ok) {
                    if (response.status === 404) {
                        hookLogger.warn('Workflow not found. Stopping polling', { workflowId, status: response.status });
                        shouldContinuePolling = false;
                        if (intervalId) {
                            clearInterval(intervalId);
                        }
                        const { resetWorkflow } = useWorkflowStore.getState();
                        resetWorkflow();
                        return;
                    }
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const status = await response.json();
                
                // Comprehensive logging to track data flow
                hookLogger.info('Raw backend data received', { workflowId, status });
                hookLogger.debug('Data breakdown', {
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
                
                // Extra debugging for nodes and edges
                if (status.nodes) {
                    hookLogger.debug('First few nodes', status.nodes.slice(0, 3));
                }
                if (status.edges) {
                    hookLogger.debug('First few edges', status.edges.slice(0, 3));
                }

                updateWorkflowStatus(status);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    hookLogger.info('Workflow finished. Stopping polling', { workflowId, status: status.status });
                    shouldContinuePolling = false;
                    if (intervalId) {
                        clearInterval(intervalId);
                    }
                }
            } catch (err) {
                hookLogger.error('Error polling workflow', { workflowId, error: err });
                // Continue polling on other errors, but stop on 404
            }
        };

        // Initial fetch
        pollWithErrorHandling();
        
        // Set up interval for continued polling
        intervalId = setInterval(pollWithErrorHandling, 2000);

        return () => {
            hookLogger.info('Cleaning up polling', { workflowId });
            shouldContinuePolling = false;
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [workflowId, updateWorkflowStatus]);

    // This hook no longer returns anything as it interacts directly with the store
};