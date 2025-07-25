// App.tsx - Updated handleNodeDoubleClick
import React, { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from 'reactflow';
import { AgentNodeData, ChatMessage, CustomNode, CustomNodeData } from './types';
import { useStore } from './store';
import SidePanel from './components/SidePanel';
import WorkflowCanvas from './components/WorkflowCanvas';
import { ApiKeyModal } from './components/ApiKeyModal';
import AgentTraceModal from './components/AgentTraceModal';
import Notification from './components/Notification';
import { useWorkflowStatus } from './hooks/useWorkflowStatus';

// Type guard to check if a node is an AgentNode
const isAgentNode = (node: CustomNode): node is CustomNode & { data: AgentNodeData } => {
  return 'result' in node.data || 'error' in node.data;
};


const App: React.FC = () => {
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<CustomNode | null>(null);

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
            const typedNodes = workflowStatus.nodes.map((node: any) => ({
                ...node,
                type: node.type || 'default',
                data: {
                    ...node.data,
                    status: node.data?.status || 'pending'
                }
            }));
            
            setNodes(typedNodes as CustomNode[]);
            setEdges(workflowStatus.edges);
        }
    }, [workflowStatus, setNodes, setEdges]);

    const handleWorkflowStart = (workflowId: string) => {
        setCurrentWorkflowId(workflowId);
        setIsLoading(true);
        setError(null);
    };

    const handleNodeDoubleClick = (_event: React.MouseEvent, node: CustomNode) => {
        console.log('Node double-clicked:', node);
        
        // Check if this is an agent node (not input/output nodes)
        const isAgent = node.id !== 'query_input' && node.id !== 'final_synthesis';
        
        // Show modal for any agent node that has a result or error
        if (isAgent && isAgentNode(node)) {
            console.log('Opening modal for node:', node.id);
            setSelectedNode(node);
        } else {
            console.log('Node not eligible for modal:', {
                id: node.id,
                isAgent,
                hasResult: 'result' in node.data,
                hasError: 'error' in node.data,
                status: node.data.status
            });
        }
    };

    // Update loading state based on workflow status
    useEffect(() => {
        if (workflowStatus?.status === 'completed' || workflowStatus?.status === 'failed') {
            setIsLoading(false);
        }
    }, [workflowStatus]);

    const handleAddMessage = (message: ChatMessage) => {
        setChatMessages(prev => [...prev, message]);
    };

    return (
        <div className="flex h-screen bg-brand-bg text-white font-sans">
            <SidePanel
                chatMessages={chatMessages}
                onAddMessage={handleAddMessage}
                isLoading={isLoading}
                onWorkflowStart={handleWorkflowStart}
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
                    
                    {/* Workflow info overlay */}
                    {workflowStatus && (
                        <div className="absolute top-4 left-4 bg-brand-surface p-4 rounded-lg shadow-lg max-w-md z-10">
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
                            {workflowStatus.execution_time && (
                                <div className="text-sm text-brand-text-secondary mt-1">
                                    Execution time: {workflowStatus.execution_time.toFixed(2)}s
                                </div>
                            )}
                            <div className="text-xs text-brand-text-secondary mt-3">
                                💡 Double-click on agent nodes to see details
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
                />
            )}
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;
