// components/SidePanel.tsx
import React, { useState } from 'react';
import { ChatMessage } from '../types';
import ChatPanel from './ChatPanel';
import CodeBracketIcon from './icons/CodeBracketIcon';
import DocumentTextIcon from './icons/DocumentTextIcon';
import ToolkitPanel from './ToolkitPanel';
import { useStore } from '../store';
import { useKeyStatus } from '../hooks/useKeyStatus';

const SidePanel: React.FC<{
    chatMessages: ChatMessage[];
    onSendMessage: (message: string) => void;
    onAddMessage: (message: ChatMessage) => void;
    isLoading: boolean;
    onWorkflowStart?: (workflowId: string) => void;
}> = ({ chatMessages, onSendMessage, onAddMessage, isLoading, onWorkflowStart }) => {
    const [activeTab, setActiveTab] = useState<'chat' | 'toolkit'>('chat');
    
    const {
        controlFlowProvider,
        setControlFlowProvider,
        customBaseUrl,
        setCustomBaseUrl,
    } = useStore();

    const { backendKeys, isLoading: areKeysLoading } = useKeyStatus();

    const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setControlFlowProvider(e.target.value as 'openai' | 'google' | 'local');
    };

    const isKeyMissing = (() => {
        if (controlFlowProvider === 'openai') return !backendKeys.openai;
        if (controlFlowProvider === 'google') return !backendKeys.google;
        return false;
    })();

    const TabButton: React.FC<{ tabName: 'chat' | 'toolkit'; label: string; children: React.ReactNode }> = ({ tabName, label, children }) => (
        <button
            onClick={() => setActiveTab(tabName)}
            className={`flex-1 flex items-center justify-center p-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tabName
                    ? 'text-brand-primary border-brand-primary'
                    : 'text-brand-text-secondary border-transparent hover:bg-brand-surface'
            }`}
            aria-label={`Switch to ${label} tab`}
        >
            {children}
            <span className="ml-2">{label}</span>
        </button>
    );

    return (
        <aside className="w-[450px] flex-shrink-0 border-r border-brand-border flex flex-col bg-brand-surface text-white">
            {/* --- Configuration Section --- */}
            <div className="p-4 border-b border-brand-border space-y-4">
                <div className="p-3 bg-brand-bg rounded-md space-y-4 animate-fade-in">
                    <div>
                        <label htmlFor="provider-select" className="block text-sm font-medium text-brand-text-secondary mb-1">
                            LLM Provider
                        </label>
                        <select
                            id="provider-select"
                            value={controlFlowProvider}
                            onChange={handleProviderChange}
                            className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none text-brand-text-primary"
                        >
                            <option value="openai">OpenAI</option>
                            <option value="google">Gemini</option>
                            <option value="local">Local Model</option>
                        </select>
                    </div>
                    {controlFlowProvider === 'local' && (
                        <div>
                            <label htmlFor="base-url-input" className="block text-sm font-medium text-brand-text-secondary mb-1">
                                Custom Base URL
                            </label>
                            <input
                                id="base-url-input"
                                type="text"
                                value={customBaseUrl}
                                onChange={(e) => setCustomBaseUrl(e.target.value)}
                                placeholder="e.g., http://localhost:8080/v1"
                                className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none text-brand-text-primary"
                            />
                        </div>
                    )}
                </div>
                {!areKeysLoading && isKeyMissing && (
                     <div className="mt-2 text-xs text-yellow-300 bg-yellow-900/50 p-2 rounded-md animate-fade-in">
                        <strong>Warning:</strong> The required API key is not set on the backend.
                    </div>
                )}
            </div>
            
            {/* --- Tab Navigation --- */}
            <div className="flex border-b border-brand-border flex-shrink-0">
                <TabButton tabName="chat" label="Chat"><DocumentTextIcon className="w-5 h-5" /></TabButton>
                <TabButton tabName="toolkit" label="Toolkit"><CodeBracketIcon className="w-5 h-5" /></TabButton>
            </div>

            {/* --- Tab Content --- */}
            <div className="flex-grow overflow-hidden">
                {activeTab === 'chat' && (
                    <ChatPanel
                        chatMessages={chatMessages}
                        onSendMessage={onSendMessage}
                        onAddMessage={onAddMessage}
                        isLoading={isLoading}
                        onWorkflowStart={onWorkflowStart}
                    />
                )}
                {activeTab === 'toolkit' && <ToolkitPanel />}
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