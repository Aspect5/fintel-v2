import React, { useState, useEffect } from 'react';
import { useStore } from '../store';
import SparklesIcon from './icons/SparklesIcon';
import CheckCircleIcon from './icons/CheckCircleIcon';
import XCircleIcon from './icons/XCircleIcon';

interface KeyStatus {
    openai: boolean;
    google: boolean;
    alpha_vantage: boolean;
    fred: boolean;
}

const ApiKeyModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
    const [status, setStatus] = useState<KeyStatus | null>(null);
    const [geminiKey, setGeminiKey] = useState(useStore.getState().geminiApiKey || '');
    const setFrontendGeminiKey = useStore((s) => s.setGeminiApiKey);

    useEffect(() => {
        const fetchKeyStatus = async () => {
            try {
                const response = await fetch('/api/key-status');

                // --- Start of debugging code ---
                // Clone the response so we can read it twice (once as text, once as JSON)
                const responseForText = response.clone();
                const rawText = await responseForText.text();
                console.log("DEBUG: Raw response from backend:", rawText);
                // --- End of debugging code ---

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                
                const data = await response.json();
                setStatus(data);

            } catch (err) {
                console.error("Failed to fetch key status:", err);
            }
        };

        fetchKeyStatus();
    }, []);

    const handleSave = () => {
        setFrontendGeminiKey(geminiKey);
        onClose();
    };

    const StatusIndicator: React.FC<{ isSet: boolean; name: string }> = ({ isSet, name }) => (
        <div className={`flex items-center justify-between p-3 rounded-md ${isSet ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
            <span className={`font-medium ${isSet ? 'text-green-300' : 'text-red-300'}`}>{name}</span>
            {isSet ? <CheckCircleIcon className="w-6 h-6 text-green-400" /> : <XCircleIcon className="w-6 h-6 text-red-400" />}
        </div>
    );

    return (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center animate-fade-in">
            <div className="bg-brand-surface p-8 rounded-lg shadow-2xl w-full max-w-2xl border border-brand-border">
                <div className="text-center mb-6">
                    <SparklesIcon className="w-10 h-10 text-brand-primary mx-auto mb-3" />
                    <h2 className="text-2xl font-bold text-white">API Key Configuration</h2>
                    <p className="text-brand-text-secondary mt-2">Manage keys for both backend and frontend execution engines.</p>
                </div>

                <div className="grid grid-cols-2 gap-6">
                    {/* Backend Key Status */}
                    <div className="space-y-4">
                        <h3 className="font-semibold text-white border-b border-brand-border pb-2">Backend Status (from .env)</h3>
                        {status ? (
                            <>
                                <StatusIndicator isSet={status.openai} name="OpenAI Key" />
                                <StatusIndicator isSet={status.google} name="Google Key (for Gemini)" />
                                <StatusIndicator isSet={status.alpha_vantage} name="Alpha Vantage Key" />
                                <StatusIndicator isSet={status.fred} name="FRED Key" />
                            </>
                        ) : (
                            <p className="text-brand-text-secondary">Loading backend status...</p>
                        )}
                    </div>

                    {/* Frontend-Only Gemini Key */}
                    <div className="space-y-4">
                        <h3 className="font-semibold text-white border-b border-brand-border pb-2">Frontend Engine Key</h3>
                        <div>
                            <label htmlFor="gemini-key" className="block text-sm font-medium text-brand-text-primary mb-1">
                                Gemini API Key (for Visual Engine)
                            </label>
                            <input
                                id="gemini-key"
                                type="password"
                                value={geminiKey}
                                onChange={(e) => setGeminiKey(e.target.value)}
                                placeholder="Required for 'Gemini (Visual)' only"
                                className="w-full p-2 bg-brand-bg border border-brand-border rounded-md focus:ring-2 focus:ring-brand-primary focus:outline-none"
                            />
                            <p className="text-xs text-brand-text-secondary mt-1">This key is stored in your browser's state and is never sent to the backend.</p>
                        </div>
                    </div>
                </div>

                <div className="mt-8 flex justify-end">
                    <button
                        onClick={handleSave}
                        className="py-2 px-6 bg-brand-primary text-white font-bold rounded-lg hover:bg-brand-secondary transition-colors"
                    >
                        Save & Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ApiKeyModal;