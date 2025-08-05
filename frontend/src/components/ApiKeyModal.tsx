import React, { useState, useEffect } from 'react';
import { useStore } from '../stores/store';
import CheckCircleIcon from './icons-solid/CheckCircleIcon'; // Corrected: Default import
import XCircleIcon from './icons-solid/XCircleIcon'; // Corrected: Default import
import KeyIcon from './icons/KeyIcon'; // Corrected: Default import

type BackendKeyStatus = {
    openai: boolean;
    google: boolean;
    alpha_vantage: boolean;
    fred: boolean;
};

// A helper component for displaying the status of a single key
const KeyStatusRow = ({ name, isSet, children }: { name: string; isSet: boolean; children?: React.ReactNode }) => (
    <div className="flex items-center justify-between p-2 my-1 bg-gray-700/50 rounded">
        <span className="text-gray-300">{name}</span>
        <div className="flex items-center space-x-2">
            {isSet ? (
                <CheckCircleIcon className="h-6 w-6 text-green-400" />
            ) : (
                <XCircleIcon className="h-6 w-6 text-red-400" />
            )}
            {children}
        </div>
    </div>
);

export const ApiKeyModal = () => {
    const { isApiKeyModalOpen, setIsApiKeyModalOpen } = useStore(); // Corrected: useStore
    const [backendKeys, setBackendKeys] = useState<BackendKeyStatus>({
        openai: false,
        google: false,
        alpha_vantage: false,
        fred: false,
    });

    useEffect(() => {
        if (isApiKeyModalOpen) {
            // Fetch the status of keys configured on the backend
            fetch('/api/status/keys')
                .then(res => res.json())
                .then(data => setBackendKeys(data))
                .catch(console.error);
        }
    }, [isApiKeyModalOpen]);

    if (!isApiKeyModalOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm">
            <div className="bg-gray-800 border border-gray-600 rounded-lg shadow-xl p-6 w-full max-w-md text-white">
                <div className="flex items-center mb-4">
                    <KeyIcon className="h-8 w-8 text-yellow-400 mr-3" />
                    <h2 className="text-2xl font-bold">API Key Configuration</h2>
                </div>
                <p className="text-gray-400 mb-6">
                    Manage keys for both backend services and financial data tools. All keys are configured securely on the server via environment variables.
                </p>

                {/* Backend Keys Status */}
                <div className="space-y-2">
                    <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2 mb-3">Backend Service Status <span className='text-sm text-gray-500'>(from .env)</span></h3>
                    <KeyStatusRow name="OpenAI Key (for Agents)" isSet={backendKeys.openai} />
                    <KeyStatusRow name="Google Key (for Gemini)" isSet={backendKeys.google} />
                </div>
                
                <div className="space-y-2 mt-6">
                     <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2 mb-3">Financial Tool Status <span className='text-sm text-gray-500'>(Handled by Proxy)</span></h3>
                     <KeyStatusRow name="Alpha Vantage Key" isSet={backendKeys.alpha_vantage} />
                     <KeyStatusRow name="FRED Key" isSet={backendKeys.fred} />
                </div>

                <div className="mt-8 text-center">
                    <button
                        onClick={() => setIsApiKeyModalOpen(false)}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};
