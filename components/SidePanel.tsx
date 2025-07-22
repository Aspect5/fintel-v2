import React, { useState } from 'react';
import { ChatMessage } from '../types';
import ChatPanel from './ChatPanel';
import CodeBracketIcon from './icons/CodeBracketIcon';
import DocumentTextIcon from './icons/DocumentTextIcon';
import ToolkitPanel from './ToolkitPanel';
import { useStore, ExecutionEngine, ControlFlowProvider } from '../store';
import { useKeyStatus } from '../hooks/useKeyStatus';

/**
 * The main side panel component that contains the configuration controls,
 * chat interface, and toolkit viewer.
 */
const SidePanel: React.FC<{
    chatMessages: ChatMessage[];
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}> = ({ chatMessages, onSendMessage, isLoading }) => {
    const [activeTab, setActiveTab] = useState<'chat' | 'toolkit'>('chat');
    
    // Get all necessary state and actions from the unified store
    const {
        executionEngine,
        setExecutionEngine,
        controlFlowProvider,
        setControlFlowProvider,
        customBaseUrl,
        setCustomBaseUrl,
    } = useStore();

    // Fetch the status of API keys from the backend
    const { backendKeys, isLoading: areKeysLoading } = useKeyStatus();

    const handleEngineChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setExecutionEngine(e.target.value as ExecutionEngine);
    };

    const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setControlFlowProvider(e.target.value as ControlFlowProvider);
    };

    // Determine if a required key is missing based on the current engine and provider selection
    const isKeyMissing = (() => {
        if (executionEngine === 'Gemini (Visual)') {
            // The visual engine relies on the backend proxy which needs Google and tool keys
            return !backendKeys.google || !backendKeys.alpha_vantage;
        }
        if (executionEngine === 'ControlFlow (Python)') {
            // The agentic backend's needs depend on the selected LLM provider
            if (controlFlowProvider === 'openai') return !backendKeys.openai;
            if (controlFlowProvider === 'gemini') return !backendKeys.google;
        }
        return false; // No key needed for local provider
    })();

    // A reusable button component for switching between Chat and Toolkit tabs
    const TabButton: React.FC<{ tabName: 'chat' | 'toolkit'; label: string; children: React.ReactNode }> = ({ tabName, label, children }) => (
        <button
            onClick={() => setActiveTab(tabName)}
            className={`flex-1 flex items-center justify-center p-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tabName
                    ? 'text-indigo-400 border-indigo-400'
                    : 'text-gray-400 border-transparent hover:bg-gray-800'
            }`}
            aria-label={`Switch to ${label} tab`}
        >
            {children}
            <span className="ml-2">{label}</span>
        </button>
    );

    return (
        <aside className="w-[450px] flex-shrink-0 border-r border-gray-700 flex flex-col bg-gray-900 text-white">
            {/* --- Configuration Section --- */}
            <div className="p-4 border-b border-gray-700 space-y-4">
                <div>
                    <label htmlFor="engine-select" className="block text-sm font-medium text-gray-300 mb-1">
                        Execution Engine
                    </label>
                    <select
                        id="engine-select"
                        value={executionEngine}
                        onChange={handleEngineChange}
                        className="w-full p-2 bg-gray-800 border border-gray-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    >
                        <option value="Gemini (Visual)">Gemini (Visual Tools)</option>
                        <option value="ControlFlow (Python)">ControlFlow (Python Agents)</option>
                    </select>
                </div>

                {/* --- Conditional Controls for ControlFlow Backend --- */}
                {executionEngine === 'ControlFlow (Python)' && (
                    <div className="p-3 bg-gray-800/70 rounded-md space-y-4 animate-fade-in">
                        <div>
                            <label htmlFor="provider-select" className="block text-sm font-medium text-gray-300 mb-1">
                                LLM Provider
                            </label>
                            <select
                                id="provider-select"
                                value={controlFlowProvider}
                                onChange={handleProviderChange}
                                className="w-full p-2 bg-gray-800 border border-gray-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                            >
                                <option value="openai">OpenAI</option>
                                <option value="gemini">Gemini</option>
                                <option value="local">Local Model</option>
                            </select>
                        </div>
                        {controlFlowProvider === 'local' && (
                            <div>
                                <label htmlFor="base-url-input" className="block text-sm font-medium text-gray-300 mb-1">
                                    Custom Base URL
                                </label>
                                <input
                                    id="base-url-input"
                                    type="text"
                                    value={customBaseUrl}
                                    onChange={(e) => setCustomBaseUrl(e.target.value)}
                                    placeholder="e.g., http://localhost:8080/v1"
                                    className="w-full p-2 bg-gray-800 border border-gray-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                                />
                            </div>
                        )}
                    </div>
                )}
                 {/* --- Key Status Warning --- */}
                {!areKeysLoading && isKeyMissing && (
                     <div className="mt-2 text-xs text-yellow-300 bg-yellow-900/50 p-2 rounded-md animate-fade-in">
                        <strong>Warning:</strong> The required API key for the selected configuration is not set on the backend. The application may not function correctly.
                    </div>
                )}
            </div>
            
            <div className="flex border-b border-gray-700 flex-shrink-0">
                <TabButton tabName="chat" label="Chat">
                    <DocumentTextIcon className="w-5 h-5" />
                </TabButton>
                <TabButton tabName="toolkit" label="Toolkit">
                    <CodeBracketIcon className="w-5 h-5" />
                </TabButton>
            </div>

            <div className="flex-grow overflow-hidden">
                {activeTab === 'chat' && (
                    <ChatPanel
                        chatMessages={chatMessages}
                        onSendMessage={onSendMessage}
                        isLoading={isLoading}
                    />
                )}
                {activeTab === 'toolkit' && (
                    <ToolkitPanel />
                )}
            </div>
             <style>{`
                @keyframes fade-in {
                from { opacity: 0; transform: translateY(-5px); }
                to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in {
                    animation: fade-in 0.3s ease-out forwards;
                }
            `}</style>
        </aside>
    );
};

export default SidePanel;
