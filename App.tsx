import React, { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from 'reactflow';
import { ChatMessage } from './types';
import { useStore } from './store';
import SidePanel from './components/SidePanel';
import WorkflowCanvas from './components/WorkflowCanvas';
import { ApiKeyModal } from './components/ApiKeyModal';
// The 'executeTool' import is now correctly REMOVED
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
    const { executionEngine, controlFlowProvider, customBaseUrl, setIsApiKeyModalOpen } = useStore();

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
            let assistantMessage: ChatMessage;
            if (executionEngine === 'Gemini (Visual)') {
                // This engine correctly runs on the frontend via the browser's window.ai
                if (!window.ai) {
                    throw new Error("Built-in AI (window.ai) is not available in this browser.");
                }
                const geminiResponse = await window.ai.prompt(message);
                assistantMessage = { role: 'assistant', content: geminiResponse.text() };
            } else {
                // This engine correctly runs on the backend for security
                const agentResponse = await runAgent(message, controlFlowProvider, customBaseUrl);
                assistantMessage = { role: 'assistant', content: agentResponse.output, trace: agentResponse.trace };
            }
            setChatMessages(prev => [...prev, assistantMessage]);
        } catch (e: any) {
            console.error("Error processing message:", e);
            const errorMessage = e.message || "An unexpected error occurred.";
            setError(errorMessage);
            const errorChatMessage: ChatMessage = { role: 'assistant', content: `Error: ${errorMessage}` };
            setChatMessages(prev => [...prev, errorChatMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    // --- THIS IS THE CORRECTED LOGIC ---
    // The tool handler for the Gemini Visual engine now calls our secure backend proxy.
    if (window.ai) {
        window.ai.tool = async (toolName: string, parameters: any) => {
            console.log(`Proxying tool call for: ${toolName}`, parameters);

            // The toolName (e.g., 'alpha_vantage') becomes the provider path for the proxy.
            const provider = toolName;
            
            // Convert the parameters object into a URL query string (e.g., "?function=TIME_SERIES_DAILY&symbol=IBM")
            const queryParams = new URLSearchParams(parameters).toString();
            const proxyUrl = `http://127.0.0.1:5001/api/proxy/${provider}?${queryParams}`;

            try {
                const response = await fetch(proxyUrl);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Proxy request failed for ${toolName}`);
                }
                const data = await response.json();
                
                // For the LLM, we return the raw data as 'output' and a summary
                return { 
                    output: data, 
                    summary: `Successfully fetched data from ${toolName}.` 
                };
            } catch (error: any) {
                console.error(`Error executing tool via proxy ${toolName}:`, error);
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
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;