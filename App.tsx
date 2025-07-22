import React, { useEffect } from 'react';
import { useStore } from './store';
import SidePanel from './components/SidePanel';
import ChatPanel from './components/ChatPanel';
import ApiKeyModal from './components/ApiKeyModal';
import Notification from './components/Notification';

const App: React.FC = () => {
  const { 
    geminiApiKey, 
    notification, 
    setNotification, 
    chatMessages, 
    addChatMessage, 
    isLoading, 
    setIsLoading 
  } = useStore();

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification, setNotification]);

  const handleSendMessage = async (message: string) => {
    addChatMessage('user', message);
    setIsLoading(true);
    // TODO: Add logic to send message to the backend
    // and receive a response.
    // For now, we'll just simulate a response.
    setTimeout(() => {
      addChatMessage('ai', 'This is a simulated response.');
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {!geminiApiKey && <ApiKeyModal onClose={() => {}} />}
      <SidePanel />
      <div className="flex flex-col flex-grow">
        <header className="bg-gray-800 p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold">Multi-Agent AI</h1>
        </header>
        <main className="flex-grow p-4 overflow-auto">
          <ChatPanel 
            chatMessages={chatMessages} 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading} 
          />
        </main>
      </div>
      {notification && (
        <Notification 
          type={notification.type} 
          message={notification.message} 
          onClose={() => setNotification(null)} 
        />
      )}
    </div>
  );
};

export default App;