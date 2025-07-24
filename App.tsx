import React, { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from 'reactflow';
import { ChatMessage } from './types';
import { useStore } from './store';
import SidePanel from './components/SidePanel';
import WorkflowCanvas from './components/WorkflowCanvas';
import { ApiKeyModal } from './components/ApiKeyModal';
import Notification from './components/Notification';
import { useWorkflowStatus } from './hooks/useWorkflowStatus';

const App: React.FC = () => {
    const [chatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);

    // State for the react-flow canvas
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // Get workflow status
    const { workflowStatus } = useWorkflowStatus(currentWorkflowId);

    // Get global state from the Zustand store
    const { setIsApiKeyModalOpen } = useStore();

    // Effect to show the API key modal on first visit
    useEffect(() => {
        const hasVisited = localStorage.getItem('hasVisited');
        if (!hasVisited) {
            setIsApiKeyModalOpen(true);
            localStorage.setItem('hasVisited', 'true');
        }
    }, [setIsApiKeyModalOpen]);

    // Update nodes and edges when workflow status changes
    useEffect(() => {
        if (workflowStatus?.nodes && workflowStatus?.edges) {
            setNodes(workflowStatus.nodes);
            setEdges(workflowStatus.edges);
        }
    }, [workflowStatus, setNodes, setEdges]);

    const handleSendMessage = async () => {
        // This is now handled by the ChatPanel component
        // which will call handleWorkflowStart when a workflow begins
    };

    const handleWorkflowStart = (workflowId: string) => {
        setCurrentWorkflowId(workflowId);
        setIsLoading(true);
        setError(null);
    };

    const handleNodeDoubleClick = (_event: React.MouseEvent, node: any) => {
        // This could open a modal with detailed information about the node
        console.log('Node double-clicked:', node);
    };

    // Update loading state based on workflow status
    useEffect(() => {
        if (workflowStatus?.status === 'completed' || workflowStatus?.status === 'failed') {
            setIsLoading(false);
        }
    }, [workflowStatus]);

    return (
        <div className="flex h-screen bg-brand-bg text-white font-sans">
            <SidePanel
                chatMessages={chatMessages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                onWorkflowStart={handleWorkflowStart}
            />
            <main className="flex-1 flex flex-col">
                <div className="flex-1 relative">
                    <WorkflowCanvas
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeDoubleClick={handleNodeDoubleClick}
                    />
                    
                    {/* Workflow info overlay */}
                    {workflowStatus && (
                        <div className="absolute top-4 left-4 bg-brand-surface p-4 rounded-lg shadow-lg max-w-md">
                            <h3 className="text-lg font-semibold text-brand-text-primary mb-2">
                                Workflow Analysis
                            </h3>
                            <p className="text-sm text-brand-text-secondary mb-2">
                                Query: {workflowStatus.query}
                            </p>
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-brand-text-secondary">Status:</span>
                                <span className={`text-sm font-semibold ${
                                    workflowStatus.status === 'completed' ? 'text-green-400' :
                                    workflowStatus.status === 'failed' ? 'text-red-400' :
                                    workflowStatus.status === 'running' ? 'text-yellow-400' :
                                    'text-blue-400'
                                }`}>
                                    {workflowStatus.status}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </main>
            <ApiKeyModal />
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;