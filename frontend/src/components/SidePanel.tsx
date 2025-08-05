// components/SidePanel.tsx
import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, WorkflowStatus } from '../types';
import ChatPanel from './ChatPanel';
import CodeBracketIcon from './icons/CodeBracketIcon';
import DocumentTextIcon from './icons/DocumentTextIcon';
import SparklesIcon from './icons/SparklesIcon';
import ToolkitPanel from './ToolkitPanel';
import AgentPanel from './AgentPanel';
import WorkflowConfigPanel from './WorkflowConfigPanel';
import { useStore } from '../stores/store';
import { useKeyStatus } from '../hooks/useKeyStatus';

const SidePanel: React.FC<{
    chatMessages: ChatMessage[];
    onSendMessage: (message: string) => void;
    onAddMessage: (message: ChatMessage) => void;
    isLoading: boolean;
    onWorkflowStart?: (status: WorkflowStatus) => void;
}> = ({ chatMessages, onSendMessage, onAddMessage, isLoading, onWorkflowStart }) => {
    const [activeTab, setActiveTab] = useState<'chat' | 'toolkit' | 'agents' | 'workflows'>('chat');
    const [isResizing, setIsResizing] = useState(false);
    const [panelWidth, setPanelWidth] = useState(450);
    const resizeRef = useRef<HTMLDivElement>(null);
    
    const {
        controlFlowProvider,
        setControlFlowProvider,
        customBaseUrl,
        setCustomBaseUrl,
    } = useStore();

    const { backendKeys, isLoading: areKeysLoading, error, isBackendAvailable, refetch } = useKeyStatus();

    const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setControlFlowProvider(e.target.value as 'openai' | 'google' | 'local');
    };

    const isKeyMissing = (() => {
        if (controlFlowProvider === 'openai') return !backendKeys.openai;
        if (controlFlowProvider === 'google') return !backendKeys.google;
        return false;
    })();

    // Handle resizing
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isResizing && resizeRef.current) {
                const newWidth = e.clientX;
                if (newWidth >= 300 && newWidth <= 800) {
                    setPanelWidth(newWidth);
                }
            }
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);

    const TabButton: React.FC<{ tabName: 'chat' | 'toolkit' | 'agents' | 'workflows'; label: string; children: React.ReactNode }> = ({ tabName, label, children }) => (
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
        <>
            <aside 
                className="flex-shrink-0 border-r border-brand-border flex flex-col bg-brand-surface text-white relative"
                style={{ width: `${panelWidth}px` }}
            >
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
                    {!areKeysLoading && !isBackendAvailable && error && (
                        <div className="mt-2 text-xs text-red-300 bg-red-900/50 p-2 rounded-md animate-fade-in">
                            <strong>Backend Unavailable:</strong> {error}
                            <button 
                                onClick={refetch}
                                className="ml-2 text-blue-300 hover:text-blue-200 underline"
                            >
                                Retry
                            </button>
                        </div>
                    )}
                    {!areKeysLoading && isBackendAvailable && isKeyMissing && (
                         <div className="mt-2 text-xs text-yellow-300 bg-yellow-900/50 p-2 rounded-md animate-fade-in">
                            <strong>Warning:</strong> The required API key is not set on the backend.
                        </div>
                    )}
                </div>
                
                {/* --- Tab Navigation --- */}
                <div className="flex border-b border-brand-border flex-shrink-0">
                    <TabButton tabName="chat" label="Chat">
                        <DocumentTextIcon className="w-5 h-5" />
                    </TabButton>
                    <TabButton tabName="toolkit" label="Tools">
                        <CodeBracketIcon className="w-5 h-5" />
                    </TabButton>
                    <TabButton tabName="agents" label="Agents">
                        <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-xs font-bold">A</span>
                        </div>
                    </TabButton>
                    <TabButton tabName="workflows" label="Workflows">
                        <SparklesIcon className="w-5 h-5" />
                    </TabButton>
                </div>

                {/* --- Tab Content --- */}
                <div className="flex-grow overflow-hidden">
                    {/* Always render ChatPanel but hide it when not active */}
                    <div className={`h-full ${activeTab === 'chat' ? 'block' : 'hidden'}`}>
                        <ChatPanel
                            chatMessages={chatMessages}
                            onSendMessage={onSendMessage}
                            onAddMessage={onAddMessage}
                            isLoading={isLoading}
                            onWorkflowStart={onWorkflowStart}
                        />
                    </div>
                    
                    {/* Always render ToolkitPanel but hide it when not active */}
                    <div className={`h-full ${activeTab === 'toolkit' ? 'block' : 'hidden'}`}>
                        <ToolkitPanel />
                    </div>

                    {/* Always render AgentPanel but hide it when not active */}
                    <div className={`h-full ${activeTab === 'agents' ? 'block' : 'hidden'}`}>
                        <AgentPanel />
                    </div>

                    {/* Always render WorkflowConfigPanel but hide it when not active */}
                    <div className={`h-full ${activeTab === 'workflows' ? 'block' : 'hidden'}`}>
                        <div className="h-full overflow-y-auto p-4">
                            <WorkflowConfigPanel />
                        </div>
                    </div>
                </div>
            </aside>

            {/* Resize handle */}
            <div
                ref={resizeRef}
                className="w-1 bg-brand-border hover:bg-brand-primary cursor-col-resize transition-colors"
                onMouseDown={() => setIsResizing(true)}
                style={{ cursor: 'col-resize' }}
            />

            <style>{`
                @keyframes fade-in {
                from { opacity: 0; transform: translateY(-5px); }
                to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in {
                    animation: fade-in 0.3s ease-out forwards;
                }
            `}</style>
        </>
    );
};

export default SidePanel;