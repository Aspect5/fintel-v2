import { useState, useEffect } from 'react';

type BackendKeyStatus = {
  openai: boolean;
  google: boolean;
  alpha_vantage: boolean;
  fred: boolean;
};

export const useKeyStatus = () => {
  const [backendKeys, setBackendKeys] = useState<BackendKeyStatus>({
    openai: false,
    google: false,
    alpha_vantage: false,
    fred: false,
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isBackendAvailable, setIsBackendAvailable] = useState<boolean>(false);

  const fetchKeyStatus = async (retryCount = 0) => {
    const maxRetries = 5;
    const retryDelay = 1000; // 1 second

    try {
      const response = await fetch('/api/status/keys', {
        // Add timeout to prevent hanging requests
        signal: AbortSignal.timeout(5000)
      });

      if (!response.ok) {
        throw new Error(`Backend responded with status ${response.status}`);
      }
      
      const data: BackendKeyStatus = await response.json();
      setBackendKeys(data);
      setIsBackendAvailable(true);
      setError(null);

    } catch (err: any) {
      console.warn(`Attempt ${retryCount + 1}/${maxRetries + 1}: Failed to fetch key status:`, err.message);
      
      if (retryCount < maxRetries) {
        // Retry with exponential backoff
        const delay = retryDelay * Math.pow(2, retryCount);
        setTimeout(() => fetchKeyStatus(retryCount + 1), delay);
        return;
      }

      // After all retries failed, set error state
      setError('Backend is not available. Please check if the server is running.');
      setIsBackendAvailable(false);
      
      // Set all keys to false to show warnings
      setBackendKeys({
        openai: false,
        google: false,
        alpha_vantage: false,
        fred: false,
      });

    } finally {
      if (retryCount === 0) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchKeyStatus();
  }, []);

  return { 
    backendKeys, 
    isLoading, 
    error, 
    isBackendAvailable,
    refetch: () => {
      setIsLoading(true);
      setError(null);
      fetchKeyStatus();
    }
  };
};
