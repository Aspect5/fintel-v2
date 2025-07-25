// components/ChatPanel.tsx
import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage, WorkflowStatus } from '../frontend/src/types';
import MarkdownRenderer from './MarkdownRenderer';
import SpinnerIcon from './icons/SpinnerIcon';
import { useWorkflowStatus } from '../frontend/src/hooks/useWorkflowStatus';
import { useStore } from '../store';

interface ChatPanelProps {
  chatMessages: ChatMessage[];
  onSendMessage: (message: string) => void;
  onAddMessage: (message: ChatMessage) => void;
  isLoading: boolean;
  onWorkflowStart?: (status: WorkflowStatus) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  chatMessages,
  onAddMessage,
  onWorkflowStart
}) => {
  const [query, setQuery] = useState('');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [initialStateSet, setInitialStateSet] = useState(false);
  const hasAddedResult = useRef(false);
  
  const { workflowStatus } = useWorkflowStatus(workflowId, initialStateSet);
  const { controlFlowProvider } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    setWorkflowId(null);
    setInitialStateSet(false);
    hasAddedResult.current = false;
    
    // Add user message
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
        setWorkflowId(data.workflow_id);
        
        // Notify parent component with the full initial status
        if (onWorkflowStart) {
          onWorkflowStart(data.workflow_status);
        }
        setInitialStateSet(true);

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

  // Update result when workflow completes
  useEffect(() => {
    if (!workflowStatus || !workflowId || hasAddedResult.current) return;

    // Make sure this is the current workflow
    if (workflowStatus.workflow_id !== workflowId) return;
    
    if (workflowStatus.status === 'completed' && workflowStatus.result) {
      hasAddedResult.current = true;
      setIsLoading(false);
      
      // Add assistant message with result
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: workflowStatus.result,
        trace: workflowStatus.trace
      };
      onAddMessage(assistantMessage);
    } else if (workflowStatus.status === 'failed') {
      hasAddedResult.current = true;
      setIsLoading(false);
      
      // Add error message
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Analysis failed: ${workflowStatus.error || 'Unknown error'}`
      };
      onAddMessage(errorMessage);
    }
  }, [workflowStatus, workflowId, onAddMessage]);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  return (
    <div className="flex flex-col h-full bg-brand-bg">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {chatMessages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xl p-3 rounded-lg ${
                msg.role === 'user' 
                  ? 'bg-brand-primary text-white' 
                  : 'bg-brand-surface text-brand-text-primary'
              }`}>
                <MarkdownRenderer content={msg.content} />
                {msg.trace && (
                  <details className="mt-2 text-xs text-brand-text-secondary">
                    <summary className="cursor-pointer hover:text-brand-text-primary">
                      View execution details
                    </summary>
                    <pre className="mt-2 p-2 bg-brand-bg rounded overflow-x-auto">
                      {JSON.stringify(msg.trace, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {isLoading && workflowStatus && workflowStatus.status !== 'completed' && workflowStatus.status !== 'failed' && (
            <div className="flex justify-start">
              <div className="bg-brand-surface p-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <SpinnerIcon className="w-5 h-5 text-brand-primary" />
                  <span className="text-brand-text-primary">
                    {workflowStatus.status === 'running' 
                      ? `Analyzing... ${workflowStatus.current_task || ''}`
                      : 'Starting analysis...'}
                  </span>
                </div>
                {workflowStatus.execution_time && (
                  <div className="text-xs text-brand-text-secondary mt-1">
                    Time elapsed: {workflowStatus.execution_time.toFixed(1)}s
                  </div>
                )}
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Workflow status bar */}
      {workflowStatus && (
        <div className="p-3 border-t border-brand-border bg-brand-surface">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <span className="text-brand-text-secondary">Status: </span>
              <span className={`font-semibold ${
                workflowStatus.status === 'completed' ? 'text-green-400' :
                workflowStatus.status === 'failed' ? 'text-red-400' :
                workflowStatus.status === 'running' ? 'text-yellow-400' :
                'text-blue -400'
              }`}>
                {workflowStatus.status}
              </span>
            </div>
            {workflowStatus.execution_time && (
              <div className="text-sm text-brand-text-secondary">
                Completed in {workflowStatus.execution_time.toFixed(1)}s
              </div>
            )}
          </div>
        </div>
      )}

      {/* Input form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-brand-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about investments (e.g., 'Should I invest in AAPL?')"
            className="flex-1 px-3 py-2 bg-brand-surface border border-brand-border rounded text-brand-text-primary placeholder-brand-text-secondary focus:outline-none focus:ring-2 focus:ring-brand-primary"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-4 py-2 bg-brand-primary text-white rounded hover:bg-brand-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? <SpinnerIcon className="w-5 h-5" /> : 'Analyze'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatPanel;