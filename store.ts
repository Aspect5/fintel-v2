import { create } from 'zustand';

interface ApiKeyState {
  geminiApiKey: string | null;
  alphaVantageApiKey: string | null;
  fredApiKey: string | null;
  areKeysSet: boolean;
  keysJustSet: boolean; // Flag to indicate keys were just successfully set
  setKeys: (keys: { gemini: string; alphaVantage: string; fred: string }) => void;
  acknowledgeKeysSet: () => void; // Action to reset the flag
}

export const useApiKeyStore = create<ApiKeyState>((set) => ({
  geminiApiKey: null,
  alphaVantageApiKey: null,
  fredApiKey: null,
  areKeysSet: false,
  keysJustSet: false,
  setKeys: ({ gemini, alphaVantage, fred }) => {
    // The Gemini key is required to consider the keys "set".
    // Other tools can fall back to mock data if their keys are missing.
    const areSet = !!(gemini && gemini.trim());
    set({
      geminiApiKey: gemini,
      alphaVantageApiKey: alphaVantage,
      fredApiKey: fred,
      areKeysSet: areSet,
      keysJustSet: areSet, // Set the flag to true on successful save
    });
  },
  acknowledgeKeysSet: () => set({ keysJustSet: false }),
}));