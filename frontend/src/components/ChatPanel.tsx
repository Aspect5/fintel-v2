// components/ChatPanel.tsx
import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import MarkdownRenderer from './MarkdownRenderer';
import SpinnerIcon from './icons/SpinnerIcon';
import { useWorkflowStatus } from '../hooks/useWorkflowStatus';
import { useStore } from '../stores/store';
import { useWorkflowStore } from '../stores/workflowStore'; // Import the workflow store

interface ChatPanelProps {
  chatMessages: ChatMessage[];
  onAddMessage: (message: ChatMessage) => void;
  // onWorkflowStart is no longer needed as the panel will trigger the store directly
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  chatMessages,
  onAddMessage,
}) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const hasAddedResult = useRef(false);
  
  // Get state and actions from the stores
  const { controlFlowProvider, clearChatMessages } = useStore();
  const { 
      workflowId, 
      status: workflowStatus, 
      result: workflowResult, 
      error: workflowError,
      trace: workflowTrace,
      current_task: workflowCurrentTask,
      executionTime: workflowExecutionTime,
      startWorkflow, // Get the startWorkflow action
      resetWorkflow,
  } = useWorkflowStore();

  // This hook now just initiates polling when workflowId changes
  useWorkflowStatus(workflowId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    hasAddedResult.current = false;
    
    const userMessage: ChatMessage = { role: 'user', content: query };
    onAddMessage(userMessage);
    
    try {
      const response = await fetch('/api/run-workflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          provider: controlFlowProvider
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        // Start the workflow via the store
        startWorkflow(data.workflow_id, query, data.workflow_status);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to start analysis'}`
      };
      onAddMessage(errorMessage);
      setIsLoading(false);
    }
    
    setQuery('');
  };

  const handleClearChat = () => {
    clearChatMessages();
    resetWorkflow();
    hasAddedResult.current = false;
  };

  // Update result when workflow completes
  useEffect(() => {
    if (!workflowId || hasAddedResult.current) return;

    if (workflowStatus === 'completed' && workflowResult) {
      hasAddedResult.current = true;
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: `✅ Analysis complete! View the final report by clicking the last node.`,
        trace: workflowTrace,
      };
      onAddMessage(assistantMessage);
    } else if (workflowStatus === 'failed') {
      hasAddedResult.current = true;
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Analysis failed: ${workflowError || 'Unknown error'}`
      };
      onAddMessage(errorMessage);
    }
  }, [workflowStatus, workflowId, workflowResult, workflowError, workflowTrace, onAddMessage]);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  useEffect(() => {
      setIsLoading(workflowStatus === 'running' || workflowStatus === 'initializing');
  }, [workflowStatus]);

  return (
    <div className="flex flex-col h-full bg-brand-bg">
      {chatMessages.length > 0 && (
        <div className="p-3 border-b border-brand-border bg-brand-surface flex justify-between items-center">
          <h3 className="text-sm font-medium text-brand-text-primary">Chat History</h3>
          <button
            onClick={handleClearChat}
            className="text-xs text-brand-text-secondary hover:text-brand-text-primary px-2 py-1 rounded hover:bg-brand-bg transition-colors"
          >
            Clear Chat
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {chatMessages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-full p-3 rounded-lg ${
                msg.role === 'user' 
                  ? 'bg-brand-primary text-white' 
                  : 'bg-brand-surface text-brand-text-primary'
              }`}>
                <MarkdownRenderer content={msg.content} />
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-brand-surface p-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <SpinnerIcon className="w-5 h-5 text-brand-primary" />
                  <span className="text-brand-text-primary">
                    {workflowStatus === 'running' 
                      ? `Analyzing... ${workflowCurrentTask || ''}`
                      : 'Starting analysis...'}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {workflowStatus && workflowStatus !== 'idle' && (
        <div className="p-3 border-t border-brand-border bg-brand-surface">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <span className="text-brand-text-secondary">Status: </span>
              <span className={`font-semibold ${
                workflowStatus === 'completed' ? 'text-green-400' :
                workflowStatus === 'failed' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {workflowStatus}
              </span>
            </div>
            {workflowExecutionTime && (
              <div className="text-sm text-brand-text-secondary">
                Time: {workflowExecutionTime.toFixed(1)}s
              </div>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="p-4 border-t border-brand-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'Should I invest in AAPL?'"
            className="flex-1 px-3 py-2 bg-brand-surface border-brand-border rounded"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-4 py-2 bg-brand-primary text-white rounded hover:bg-brand-secondary disabled:opacity-50"
          >
            {isLoading ? <SpinnerIcon /> : 'Analyze'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatPanel;