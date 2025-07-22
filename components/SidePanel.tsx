
import React, { useState } from 'react';
import { ChatMessage } from '../types';
import ChatPanel from './ChatPanel';
import CodeBracketIcon from './icons/CodeBracketIcon';
import DocumentTextIcon from './icons/DocumentTextIcon';
import ToolkitPanel from './ToolkitPanel';
import { useStore } from '../store'; // Updated import

const SidePanel: React.FC<{
    chatMessages: ChatMessage[];
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}> = ({ chatMessages, onSendMessage, isLoading }) => {
    const [activeTab, setActiveTab] = useState<'chat' | 'toolkit'>('chat');
    const { executionEngine, setExecutionEngine } = useStore(); // Get state and action from the store

    const handleEngineChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setExecutionEngine(e.target.value as "Gemini (In-Browser)" | "ControlFlow (Python)");
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
            {/* Engine Selector Dropdown */}
            <div className="p-2 border-b border-brand-border">
                <label htmlFor="engine-select" className="block text-xs font-medium text-brand-text-secondary mb-1">
                    Execution Engine
                </label>
                <select
                    id="engine-select"
                    value={executionEngine}
                    onChange={handleEngineChange}
                    className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none text-white"
                >
                    <option value="Gemini (In-Browser)">Gemini (In-Browser)</option>
                    <option value="ControlFlow (Python)">ControlFlow (Python)</option>
                </select>
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
        </aside>
    );
};

export default SidePanel;
