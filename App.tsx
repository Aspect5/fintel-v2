import React, { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from 'reactflow';
import { ChatMessage } from './types';
import { useStore, ExecutionEngine, ControlFlowProvider } from './store';
import SidePanel from './components/SidePanel';
import WorkflowCanvas from './components/WorkflowCanvas';
import { ApiKeyModal } from './components/ApiKeyModal';
import { executeTool } from './tools/financialTools';
import { runAgent } from './services/agentService';
import Notification from './components/Notification';

const App: React.FC = () => {
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // State for the react-flow canvas, required by WorkflowCanvas
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // Get global state and setters from the Zustand store
    const { executionEngine, controlFlowProvider, customBaseUrl, setIsApiKeyModalOpen } = useStore();

    // Effect to show the API key modal on the user's first visit
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
            if (executionEngine === 'Gemini (Visual)') {
                // Visual tool-use execution via built-in browser AI
                if (!window.ai) {
                    throw new Error("Built-in AI (window.ai) is not available in this browser.");
                }
                const geminiResponse = await window.ai.prompt(message);
                const assistantMessage: ChatMessage = { role: 'assistant', content: geminiResponse.text() };
                setChatMessages(prev => [...prev, assistantMessage]);

            } else {
                // ControlFlow agent execution via the backend
                const agentResponse = await runAgent(message, controlFlowProvider, customBaseUrl);
                const assistantMessage: ChatMessage = { role: 'assistant', content: agentResponse.output, trace: agentResponse.trace };
                setChatMessages(prev => [...prev, assistantMessage]);
            }
        } catch (e: any) {
            console.error("Error processing message:", e);
            const errorMessage = e.message || "An unexpected error occurred.";
            setError(errorMessage);
            const errorMessageObj: ChatMessage = { role: 'assistant', content: `Error: ${errorMessage}` };
            setChatMessages(prev => [...prev, errorMessageObj]);
        } finally {
            setIsLoading(false);
        }
    };
    
    // This defines the tool handler for the Gemini Visual engine.
    // It's called by the browser's AI when a tool needs to be executed.
    if (window.ai) {
        window.ai.tool = async (toolName: string, parameters: any) => {
            console.log(`Executing tool: ${toolName}`, parameters);
            try {
                const { output, summary } = await executeTool(toolName, parameters);
                // The summary is a user-friendly string that can be returned to the LLM
                return { output, summary }; 
            } catch (error: any) {
                console.error(`Error executing tool ${toolName}:`, error);
                return { error: error.message };
            }
        };
    }

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
            {/* Only render the notification if there is an error message */}
            {error && <Notification message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;
