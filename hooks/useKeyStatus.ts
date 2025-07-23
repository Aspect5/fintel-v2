import { useState, useEffect } from 'react';

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

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchKeyStatus = async () => {
      try {
        // Use the correct endpoint that exists in the backend
        const response = await fetch('/api/key-status');

        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
        }
        
        const data: BackendKeyStatus = await response.json();
        setBackendKeys(data);

      } catch (err: any) {
        console.error("Error fetching API key status:", err);
        setError(err.message || 'An unknown error occurred.');

      } finally {
        setIsLoading(false);
      }
    };

    fetchKeyStatus();
  }, []);

  return { backendKeys, isLoading, error };
};
