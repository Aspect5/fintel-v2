
import React, { useState } from 'react';
import { ChatMessage } from '../types';
import ChatPanel from './ChatPanel';
import CodeBracketIcon from './icons/CodeBracketIcon';
import DocumentTextIcon from './icons/DocumentTextIcon';
import ToolkitPanel from './ToolkitPanel';
import { useStore, ExecutionEngine, ControlFlowProvider } from '../store';

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

    const handleEngineChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setExecutionEngine(e.target.value as ExecutionEngine);
    };

    const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setControlFlowProvider(e.target.value as ControlFlowProvider);
    };

    const TabButton: React.FC<{ tabName: 'chat' | 'toolkit'; label: string; children: React.ReactNode }> = ({ tabName, label, children }) => (
        <button
            onClick={() => setActiveTab(tabName)}
            className={`flex-1 flex items-center justify-center p-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tabName
                    ? 'text-brand-primary border-brand-primary'
                    : 'text-brand-text-secondary border-transparent hover:bg-brand-bg'
            }`}
            aria-label={`Switch to ${label} tab`}
        >
            {children}
            <span className="ml-2">{label}</span>
        </button>
    );

    return (
        <aside className="w-[450px] flex-shrink-0 border-r border-brand-border flex flex-col bg-brand-surface">
            {/* --- Configuration Section --- */}
            <div className="p-4 border-b border-brand-border space-y-4">
                <div>
                    <label htmlFor="engine-select" className="block text-sm font-medium text-brand-text-primary mb-1">
                        Execution Engine
                    </label>
                    <select
                        id="engine-select"
                        value={executionEngine}
                        onChange={handleEngineChange}
                        className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none text-white"
                    >
                        <option value="Gemini (Visual)">Gemini (Visual)</option>
                        <option value="ControlFlow (Python)">ControlFlow (Python)</option>
                    </select>
                </div>

                {/* --- Conditional Controls for ControlFlow Backend --- */}
                {executionEngine === 'ControlFlow (Python)' && (
                    <div className="p-3 bg-brand-bg/50 rounded-md space-y-4 animate-fade-in">
                        <div>
                            <label htmlFor="provider-select" className="block text-sm font-medium text-brand-text-primary mb-1">
                                LLM Provider
                            </label>
                            <select
                                id="provider-select"
                                value={controlFlowProvider}
                                onChange={handleProviderChange}
                                className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none text-white"
                            >
                                <option value="openai">OpenAI</option>
                                <option value="gemini">Gemini</option>
                                <option value="local">Local Model</option>
                            </select>
                        </div>
                        {controlFlowProvider === 'local' && (
                            <div>
                                <label htmlFor="base-url-input" className="block text-sm font-medium text-brand-text-primary mb-1">
                                    Custom Base URL
                                </label>
                                <input
                                    id="base-url-input"
                                    type="text"
                                    value={customBaseUrl}
                                    onChange={(e) => setCustomBaseUrl(e.target.value)}
                                    placeholder="e.g., http://localhost:8080/v1"
                                    className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none text-white"
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>
            
            <div className="flex border-b border-brand-border flex-shrink-0">
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
