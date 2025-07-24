// hooks/useWorkflowStatus.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { Node, Edge } from 'reactflow';

interface WorkflowStatus {
  workflow_id: string;
  query: string;
  nodes: Node[];
  edges: Edge[];
  status: 'initializing' | 'pending' | 'running' | 'completed' | 'failed';
  current_task?: string;
  start_time?: string;
  execution_time?: number;
  result?: string;
  error?: string;
  trace?: any;
}

export const useWorkflowStatus = (workflowId: string | null) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!workflowId) return;
    
    try {
      const response = await fetch(`/api/workflow-status/${workflowId}`);
      if (response.ok) {
        const status = await response.json();
        
        // Log the received data for debugging
        console.log('Workflow status update:', {
          id: workflowId,
          status: status.status,
          nodes: status.nodes?.length || 0,
          edges: status.edges?.length || 0
        });
        
        setWorkflowStatus(status);
        
        // Stop polling if workflow is complete
        if (status.status === 'completed' || status.status === 'failed') {
          setIsLoading(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } else if (response.status === 404) {
        console.error('Workflow not found:', workflowId);
        setError('Workflow not found');
        setIsLoading(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      console.error('Failed to fetch workflow status:', err);
      setError('Failed to fetch workflow status');
    }
  }, [workflowId]);

  useEffect(() => {
    if (!workflowId) {
      setWorkflowStatus(null);
      return;
    }

    console.log('Starting to poll workflow:', workflowId);
    setIsLoading(true);
    setError(null);

    // Initial fetch
    fetchStatus();

    // Set up polling for updates
    intervalRef.current = setInterval(fetchStatus, 1000);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsLoading(false);
    };
  }, [workflowId, fetchStatus]);

  return {
    workflowStatus,
    isLoading,
    error,
    refetch: fetchStatus
  };
};