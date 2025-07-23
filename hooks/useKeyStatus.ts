// hooks/useKeyStatus.ts

import { useState, useEffect } from 'react';

// Define the shape of the key status object
type BackendKeyStatus = {
  openai: boolean;
  google: boolean;
  alpha_vantage: boolean;
};

/**
 * A custom hook to fetch the status of API keys from the backend.
 * This helps the UI determine which LLM providers and tools are available.
 */
export const useKeyStatus = () => {
  // State to hold the key status data
  const [backendKeys, setBackendKeys] = useState<BackendKeyStatus>({
    openai: false,
    google: false,
    alpha_vantage: false,
  });

  // State to track the loading status of the API call
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // State to hold any potential error messages
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // An async function to perform the fetch operation
    const fetchKeyStatus = async () => {
      try {
        // (FIX) Fetch directly from the relative API endpoint.
        // This will be properly routed by the Vite proxy.
        const response = await fetch('/api/key-status');

        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
        }
        
        const data: BackendKeyStatus = await response.json();
        setBackendKeys(data);

      } catch (err: any) {
        // If an error occurs, update the error state
        console.error("Error fetching API key status:", err);
        setError(err.message || 'An unknown error occurred.');

      } finally {
        // Set loading to false once the fetch is complete (either success or fail)
        setIsLoading(false);
      }
    };

    fetchKeyStatus();
  }, []); // The empty dependency array ensures this effect runs only once on mount

  // Return the state values for the component to use
  return { backendKeys, isLoading, error };
};