import React, { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from 'reactflow';
import { ChatMessage } from './types';
import { useStore } from './store';
import SidePanel from './components/SidePanel';
import WorkflowCanvas from './components/WorkflowCanvas';
import { ApiKeyModal } from './components/ApiKeyModal';
import { runAgent } from './services/agentService';
import Notification from './components/Notification';

const App: React.FC = () => {
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // State for the react-flow canvas
    const [nodes, , onNodesChange] = useNodesState([]);
    const [edges, , onEdgesChange] = useEdgesState([]);

    // Get global state from the Zustand store
    const { controlFlowProvider, customBaseUrl, setIsApiKeyModalOpen } = useStore();

    // Effect to show the API key modal on first visit
    useEffect(() => {
        const hasVisited = localStorage.getItem('hasVisited');
        if (!hasVisited) {
            setIsApiKeyModalOpen(true);
            localStorage.setItem('hasVisited', 'true');
        }
    }, [setIsApiKeyModalOpen]);

    const handleSendMessage = async (message: string) => {
        const userMessage: ChatMessage = { role: 'user', content: message };
        setChatMessages(prev => [...prev, userMessage]);
        
        setIsLoading(true);
        setError(null);

        try {
            const agentResponse = await runAgent(message, controlFlowProvider, customBaseUrl);
            
            const assistantMessage: ChatMessage = { 
                role: 'assistant', 
                content: agentResponse.output, 
                trace: agentResponse.trace 
            };
            
            setChatMessages(prev => [...prev, assistantMessage]);
            
        } catch (e: any) {
            let errorMessage = "An unexpected error occurred.";
            if (e.response?.data?.error) {
                errorMessage = e.response.data.error;
            } else if (e.message) {
                errorMessage = e.message;
            }
            
            setError(errorMessage);
            const errorChatMessage: ChatMessage = { 
                role: 'assistant', 
                content: `Error: ${errorMessage}` 
            };
            setChatMessages(prev => [...prev, errorChatMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-gray-900 text-white font-sans">
            <SidePanel
                chatMessages={chatMessages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
            />
            <main className="flex-1 flex flex-col">
                <WorkflowCanvas
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                />
            </main>
            <ApiKeyModal />
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;
