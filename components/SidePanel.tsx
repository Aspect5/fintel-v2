
import React, { useState } from 'react';
import { ChatMessage } from '../types';
import ChatPanel from './ChatPanel';
import CodeBracketIcon from './icons/CodeBracketIcon';
import DocumentTextIcon from './icons/DocumentTextIcon';
import ToolkitPanel from './ToolkitPanel';

interface SidePanelProps {
    chatMessages: ChatMessage[];
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}

type Tab = 'chat' | 'toolkit';

const SidePanel: React.FC<SidePanelProps> = ({ chatMessages, onSendMessage, isLoading }) => {
    const [activeTab, setActiveTab] = useState<Tab>('chat');

    const TabButton: React.FC<{ tabName: Tab; label: string; children: React.ReactNode }> = ({ tabName, label, children }) => (
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