
import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import SparklesIcon from './icons/SparklesIcon';
import SendIcon from './icons/SendIcon';
import SpinnerIcon from './icons/SpinnerIcon';
import MarkdownRenderer from './MarkdownRenderer';

interface ChatPanelProps {
  chatMessages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const suggestions: { label: string; query: string }[] = [
    { label: "Auto Tariffs", query: "What is the impact of a 10% tariff on the automotive industry in the USA and Eurozone?" },
    { label: "Tech Stocks", query: "Analyze the market performance of 'NVDA' and 'AMD' over the last quarter." },
    { label: "US Economy", query: "Forecast the US macroeconomic outlook using current CPI and GDP data." },
];


const ChatPanel: React.FC<ChatPanelProps> = ({ chatMessages, onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    // Use a small timeout to ensure the DOM has been updated before scrolling
    setTimeout(scrollToBottom, 0);
  }, [chatMessages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const handleSuggestionClick = (suggestionQuery: string) => {
    if (!isLoading) {
      onSendMessage(suggestionQuery);
    }
  };

  return (
    <div className="flex flex-col h-full bg-brand-surface">
      {/* Message Display Area */}
      <div ref={messagesContainerRef} className="flex-grow p-4 overflow-y-auto space-y-4">
        {chatMessages.map(msg => (
          <div key={msg.id} className={`flex items-start gap-3 animate-fade-in ${msg.sender === 'user' ? 'justify-end' : ''}`}>
            {msg.sender === 'ai' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-secondary flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
            )}
            <div className={`max-w-md p-3 rounded-lg ${msg.sender === 'user' ? 'bg-brand-primary text-white' : 'bg-brand-bg'}`}>
              <MarkdownRenderer content={msg.content} />
            </div>
          </div>
        ))}
         {isLoading && chatMessages.length > 1 && (
            <div className="flex items-start gap-3 animate-fade-in">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-secondary flex items-center justify-center">
                    <SpinnerIcon className="w-5 h-5 text-white animate-spin" />
                </div>
                <div className="max-w-md p-3 rounded-lg bg-brand-bg italic text-brand-text-secondary">
                    Thinking...
                </div>
            </div>
         )}
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t border-brand-border flex-shrink-0">
         {/* Prompt Suggestions */}
        <div className="mb-4">
            <p className="text-xs text-brand-text-secondary mb-2">Or try an example:</p>
            <div className="flex flex-wrap gap-2">
                {suggestions.map((s, i) => (
                    <button
                        key={i}
                        onClick={() => handleSuggestionClick(s.query)}
                        disabled={isLoading}
                        className="px-3 py-1 bg-brand-bg text-sm text-brand-text-primary rounded-full border border-brand-border hover:bg-brand-primary/20 hover:border-brand-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        title={s.query}
                    >
                        {s.label}
                    </button>
                ))}
            </div>
        </div>
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={isLoading ? "Processing..." : "Ask FINTEL to build a workflow..."}
            className="w-full p-3 pr-12 bg-brand-bg border border-brand-border rounded-lg resize-none focus:ring-2 focus:ring-brand-primary focus:outline-none transition-shadow"
            rows={2}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute bottom-3 right-3 flex items-center justify-center w-8 h-8 bg-brand-primary text-white font-semibold rounded-full hover:bg-brand-secondary disabled:bg-brand-text-secondary disabled:cursor-not-allowed transition-all duration-300 ease-in-out transform hover:scale-110 disabled:scale-100"
            aria-label="Send message"
          >
            {isLoading && chatMessages.length > 1 ? <SpinnerIcon className="w-4 h-4" /> : <SendIcon className="w-4 h-4" />}
          </button>
        </form>
      </div>
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
            opacity: 0;
            animation: fade-in 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default ChatPanel;