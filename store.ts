import { create } from 'zustand';

type ExecutionEngine = "Gemini (In-Browser)" | "ControlFlow (Python)";

interface ApiKeyState {
  geminiApiKey: string | null;
  alphaVantageApiKey: string | null;
  fredApiKey: string | null;
  areKeysSet: boolean;
  keysJustSet: boolean; // Flag to indicate keys were just successfully set
  setKeys: (keys: { gemini: string; alphaVantage: string; fred: string }) => void;
  acknowledgeKeysSet: () => void; // Action to reset the flag
}

interface AppState extends ApiKeyState {
  executionEngine: ExecutionEngine;
  setExecutionEngine: (engine: ExecutionEngine) => void;
}

export const useStore = create<AppState>((set) => ({
  // API Key State
  geminiApiKey: null,
  alphaVantageApiKey: null,
  fredApiKey: null,
  areKeysSet: false,
  keysJustSet: false,
  setKeys: ({ gemini, alphaVantage, fred }) => {
    const areSet = !!(gemini && gemini.trim());
    set({
      geminiApiKey: gemini,
      alphaVantageApiKey: alphaVantage,
      fredApiKey: fred,
      areKeysSet: areSet,
      keysJustSet: areSet,
    });
  },
  acknowledgeKeysSet: () => set({ keysJustSet: false }),

  // Execution Engine State
  executionEngine: "Gemini (In-Browser)", // Default engine
  setExecutionEngine: (engine) => set({ executionEngine: engine }),
}));
