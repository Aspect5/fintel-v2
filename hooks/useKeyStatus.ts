import { useState, useEffect } from 'react';

// Make sure this is the correct public URL for your backend service
const BACKEND_URL = "https://5001-firebase-fintel-v2-1753205806440.cluster-2xid2zxbenc4ixa74rpk7q7fyk.cloudworkstations.dev";

type BackendKeyStatus = {
    openai: boolean;
    google: boolean;
    alpha_vantage: boolean;
};

export const useKeyStatus = () => {
    const [backendKeys, setBackendKeys] = useState<BackendKeyStatus>({
        openai: false,
        google: false,
        alpha_vantage: false,
    });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchKeyStatus = async () => {
            try {
                // This now points to the correct, full URL for the API endpoint
                const response = await fetch(`${BACKEND_URL}/api/key-status`, {
                    credentials: 'include', // Required for Cloud Workstations
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                setBackendKeys(data);
            } catch (error) {
                console.error("Error fetching API key status:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchKeyStatus();
    }, []);

    return { backendKeys, isLoading };
};