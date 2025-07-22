import React, { useState } from 'react';
import { useApiKeyStore } from '../store';
import SparklesIcon from './icons/SparklesIcon';

const ApiKeyModal: React.FC = () => {
  const [gemini, setGemini] = useState('');
  const [alphaVantage, setAlphaVantage] = useState('');
  const [fred, setFred] = useState('');
  const { setKeys } = useApiKeyStore();

  const handleSave = () => {
    if (gemini.trim()) {
      setKeys({ gemini, alphaVantage, fred });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center animate-fade-in">
      <div className="bg-brand-surface p-8 rounded-lg shadow-2xl w-full max-w-lg border border-brand-border">
        <div className="flex flex-col items-center text-center mb-6">
            <div className="p-3 bg-brand-primary/10 rounded-full mb-3">
                <SparklesIcon className="w-8 h-8 text-brand-primary" />
            </div>
            <h2 className="text-2xl font-bold text-white">FINTEL API Keys</h2>
            <p className="text-brand-text-secondary mt-2">
                Please provide your API keys to activate the application's features.
                Keys are stored in memory for your session only and are never saved.
            </p>
        </div>

        <div className="space-y-4">
          <div>
            <label htmlFor="gemini-key" className="block text-sm font-medium text-brand-text-primary mb-1">
              Google Gemini API Key <span className="text-brand-danger">*</span>
            </label>
            <input
              id="gemini-key"
              type="password"
              value={gemini}
              onChange={(e) => setGemini(e.target.value)}
              placeholder="Enter your Gemini API key"
              className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="alpha-vantage-key" className="block text-sm font-medium text-brand-text-primary mb-1">
              Alpha Vantage API Key (Optional)
            </label>
            <input
              id="alpha-vantage-key"
              type="password"
              value={alphaVantage}
              onChange={(e) => setAlphaVantage(e.target.value)}
              placeholder="For live market data"
              className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="fred-key" className="block text-sm font-medium text-brand-text-primary mb-1">
              FRED API Key (Optional)
            </label>
            <input
              id="fred-key"
              type="password"
              value={fred}
              onChange={(e) => setFred(e.target.value)}
              placeholder="For live US economic data"
              className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none"
            />
             <p className="text-xs text-brand-text-secondary mt-1">If optional keys are omitted, the system will use mock data for those tools.</p>
          </div>
        </div>

        <div className="mt-8">
          <button
            onClick={handleSave}
            disabled={!gemini.trim()}
            className="w-full py-3 bg-brand-primary text-white font-bold rounded-lg hover:bg-brand-secondary disabled:bg-brand-text-secondary disabled:cursor-not-allowed transition-colors"
          >
            Save & Start Analysis
          </button>
        </div>
      </div>
      <style>{`
        @keyframes fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .animate-fade-in {
            animation: fade-in 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default ApiKeyModal;
