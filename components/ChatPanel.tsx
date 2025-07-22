import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../types';
import MarkdownRenderer from './MarkdownRenderer';
// FIX: Changed to default imports for the icon components
import SendIcon from './icons/SendIcon';
import SpinnerIcon from './icons/SpinnerIcon';
import ReportDisplay from './report/ReportDisplay';

interface ChatPanelProps {
  chatMessages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  chatMessages,
  onSendMessage,
  isLoading,
}) => {
  const [input, setInput] = React.useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
                {/* Conditionally render the ReportDisplay or the standard markdown content */}
                {msg.trace ? (
                   <ReportDisplay trace={msg.trace} />
                ) : (
                  <MarkdownRenderer content={msg.content} />
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
        </div>
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-gray-700">
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about a stock, company, or financial concept..."
            className="w-full p-2 pr-10 bg-gray-700 border border-gray-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-indigo-400 disabled:text-gray-600"
            disabled={isLoading || !input.trim()}
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;