// App.tsx - Refactored for Zustand
import React, { useState, useEffect } from 'react';
import { useStore } from './src/stores/store';
import { useWorkflowStore } from './src/stores/workflowStore'; // Import the new store
import SidePanel from './src/components/SidePanel';
import WorkflowCanvas from './src/components/WorkflowCanvas';
import { ApiKeyModal } from './src/components/ApiKeyModal';
import AgentTraceModal from './src/components/AgentTraceModal';
import ReportModal from './src/components/ReportModal';
import { buildReportFromWorkflowState } from './src/utils/reportBuilder';
import Notification from './src/components/Notification';
import { useWorkflowStatus } from './src/hooks/useWorkflowStatus';
import WorkflowHistory from './src/components/WorkflowHistory';
import LogViewer from './src/components/LogViewer';
import {
  CustomNode, Report,
} from './src/types';

// Suppress ResizeObserver loop error
const originalError = console.error;
console.error = (...args) => {
  if (args[0]?.includes?.('ResizeObserver loop completed with undelivered notifications')) {
    return;
  }
  originalError.apply(console, args);
};

// Debug flag to gate noisy logs
const DEBUG = import.meta.env.MODE === 'development' && (window as any).__DEBUG__;

// Deprecated helpers removed in favor of centralized reportBuilder


const App: React.FC = () => {
    // Component-level state
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<CustomNode | null>(null);
    const [currentReport, setCurrentReport] = useState<Report | null>(null);
    const [isReportModalVisible, setIsReportModalVisible] = useState(false);
    const [reportGenerated, setReportGenerated] = useState(false);
    const [isLogViewerVisible, setIsLogViewerVisible] = useState(false);
    const [bannerInfo, setBannerInfo] = useState<{ type: string; loadedAt: string } | null>(null);

    // Global state from regular Zustand store
    const { setIsApiKeyModalOpen, chatMessages, addChatMessage } = useStore();

    // Global state from the new workflow-specific Zustand store
    const {
        nodes, edges, onNodesChange, onEdgesChange,
        workflowId,
        status: workflowStatus, query: workflowQuery, executionTime,
        event_history,
        loadWorkflowSnapshot,
    } = useWorkflowStore();

    // This hook now manages polling and updates the store directly
    useWorkflowStatus(workflowId);

    // Reset local, derived state whenever the workflowId changes to prevent leakage
    useEffect(() => {
        setCurrentReport(null);
        setReportGenerated(false);
        setSelectedNode(null);
        setIsReportModalVisible(false);
        setBannerInfo(null);
    }, [workflowId]);

    // Effect to show the API key modal on first visit
    useEffect(() => {
        const hasVisited = localStorage.getItem('hasVisited');
        if (!hasVisited) {
            setIsApiKeyModalOpen(true);
            localStorage.setItem('hasVisited', 'true');
        }
    }, [setIsApiKeyModalOpen]);




    // Effect to handle workflow completion and generate a report
    useEffect(() => {
        const workflowData = useWorkflowStore.getState();
        if (workflowData.status === 'completed' && !reportGenerated) {
            if (DEBUG) console.log('[App] Workflow completed. Generating report...');
            const report = buildReportFromWorkflowState(workflowData as any);
            if (DEBUG) console.log('[App] Generated report via builder:', report);
            setCurrentReport(report);
            setReportGenerated(true);
            setIsReportModalVisible(true);
        }
    }, [workflowStatus, reportGenerated]);
    
    // Effect to manage loading state based on workflow status
    useEffect(() => {
        setIsLoading(workflowStatus === 'running' || workflowStatus === 'initializing');
    }, [workflowStatus]);

    const handleSelectHistoricalWorkflow = async (selectedWorkflowId: string) => {
        const data = await loadWorkflowSnapshot(selectedWorkflowId);
        const wfType = data?.workflow_type || 'unknown';
        const loadedAt = new Date().toLocaleTimeString();
        setBannerInfo({ type: wfType, loadedAt });
        const msg = `Loaded ${wfType} (${loadedAt}).`;
        useStore.getState().addChatMessage({ role: 'assistant', content: msg });
        // Clear any derived report/selection state to avoid leakage from previous workflow
        setCurrentReport(null);
        setReportGenerated(false);
        setSelectedNode(null);
        setIsReportModalVisible(false);
        // Auto-hide banner after a few seconds
        setTimeout(() => setBannerInfo(null), 4000);

    // Reconstruct a report from the loaded snapshot using centralized builder
    try {
        const report = buildReportFromWorkflowState(data);
        setCurrentReport(report);
    } catch (e) {
        if (DEBUG) console.warn('[App] Failed to reconstruct report from history snapshot', e);
    }
    };

  const handleNodeDoubleClick = (_event: React.MouseEvent, node: CustomNode) => {
    // Output node opens report
    if (node.id === 'output') {
      setIsReportModalVisible(true);
      return;
    }
    // For agent/task nodes, open the AgentTraceModal
    setSelectedNode(node);
  };

    return (
        <div className="flex h-screen bg-brand-bg text-white font-sans">
            <SidePanel
                chatMessages={chatMessages}
                onAddMessage={addChatMessage}
                isLoading={isLoading}
                onSendMessage={() => {}}
            />

            <main className="flex-1 relative">
                <div className="absolute inset-0">
                    <WorkflowCanvas
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeDoubleClick={handleNodeDoubleClick}
                    />
                    
                    <WorkflowHistory 
                        currentWorkflowId={workflowId}
                        onSelectWorkflow={handleSelectHistoricalWorkflow}
                    />
                    {bannerInfo && (
                        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-brand-surface/90 backdrop-blur px-3 py-1.5 rounded-full shadow border border-brand-border text-xs text-brand-text-primary z-20">
                            Active: <span className="font-semibold">{bannerInfo.type}</span> • loaded at {bannerInfo.loadedAt}
                        </div>
                    )}
                    
                    {workflowStatus !== 'idle' && (
                        <div className="absolute top-4 left-4 bg-brand-surface p-4 rounded-lg shadow-lg max-w-md z-10">
                            <h3 className="text-lg font-semibold text-brand-text-primary mb-2">
                                Workflow Analysis
                            </h3>
                            <p className="text-sm text-brand-text-secondary mb-2 break-words">
                                Query: {workflowQuery}
                            </p>
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-brand-text-secondary">Status:</span>
                                <span className={`text-sm font-semibold ${
                                    workflowStatus === 'completed' ? 'text-green-400' :
                                    workflowStatus === 'failed' ? 'text-red-400' :
                                    workflowStatus === 'running' ? 'text-yellow-400' :
                                    'text-blue-400'
                                }`}>
                                    {workflowStatus}
                                </span>
                                {workflowStatus === 'running' || workflowStatus === 'initializing' ? (
                                    <span className="inline-block w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin" aria-label="loading" />
                                ) : null}
                            </div>
                            {executionTime > 0 && (
                                <div className="text-sm text-brand-text-secondary mt-1">
                                    Execution time: {executionTime.toFixed(2)}s
                                </div>
                            )}
                            <div className="text-xs text-brand-text-secondary mt-3">
                                💡 Double-click nodes for details.
                            </div>
                            <div className="text-xs text-brand-text-secondary mt-1">
                                Nodes: {nodes.length}, Edges: {edges.length}
                            </div>
                            <div className="text-xs text-brand-text-secondary mt-1">
                                <button
                                    onClick={() => setIsLogViewerVisible(true)}
                                    className="text-brand-primary hover:text-brand-primary-light underline"
                                >
                                    View Logs
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </main>
            <ApiKeyModal />
            {selectedNode && (
                <AgentTraceModal 
                    node={selectedNode} 
                    onClose={() => setSelectedNode(null)}
                    eventHistory={event_history || []}
                />
            )}
            <ReportModal 
                report={currentReport}
                isVisible={isReportModalVisible}
                onClose={() => setIsReportModalVisible(false)}
                query={workflowQuery || ''}
            />
            <LogViewer 
                isVisible={isLogViewerVisible}
                onClose={() => setIsLogViewerVisible(false)}
            />
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;