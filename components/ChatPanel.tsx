import React, { useRef, useEffect, useState } from 'react';
import { ChatMessage, Provider, Workflow } from '../types';
import MarkdownRenderer from './MarkdownRenderer';
import SendIcon from './icons/SendIcon';
import SpinnerIcon from './icons/SpinnerIcon';
import ReportDisplay from './report/ReportDisplay';

interface ChatPanelProps {
  chatMessages: ChatMessage[];
  onSendMessage: (message: string, provider: Provider, workflow: Workflow) => void;
  isLoading: boolean;
  selectedProvider: Provider;
  selectedWorkflow: Workflow;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  chatMessages,
  onSendMessage,
  isLoading,
  selectedProvider,
  selectedWorkflow,
}) => {
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setError(null);
    onSendMessage(input, selectedProvider, selectedWorkflow);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-gray-800 text-white">
      <div className="flex-grow p-4 overflow-y-auto">
        <div className="space-y-4">
          {chatMessages.map((msg, index) => (
            <div key={`msg-${index}`} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-xl p-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-indigo-500 text-white'
                    : 'bg-gray-700'
                }`}
              >
                {msg.trace && typeof msg.trace === 'object' && msg.trace.fintelQueryAnalysis ? (
                   <ReportDisplay trace={msg.trace} />
                ) : (
                  <div>
                    <MarkdownRenderer content={msg.content} />
                    {msg.trace && typeof msg.trace === 'string' && (
                      <div className="mt-2 text-xs text-gray-400 italic">
                        Source: {msg.trace}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
             <div className="flex justify-start">
               <div className="bg-gray-700 p-3 rounded-lg flex items-center space-x-2">
                 <SpinnerIcon />
                 <span>Thinking...</span>
               </div>
             </div>
          )}
          {error && (
            <div className="flex justify-start">
              <div className="bg-red-700 p-3 rounded-lg flex items-center space-x-2">
                <span>Error: {error}</span>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-gray-700">
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask a question about a stock, company, or financial concept..."
              className="w-full p-2 pr-10 bg-gray-700 border border-gray-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
              rows={2}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-indigo-400 disabled:text-gray-600"
              disabled={isLoading || !input.trim()}
            >
              <SendIcon />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;