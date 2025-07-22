import { create } from 'zustand';

// Types for the different backend engines and providers
export type ExecutionEngine = "Gemini (Visual)" | "ControlFlow (Python)";
export type ControlFlowProvider = "openai" | "gemini" | "local";

interface AppState {
  // --- UI & Execution State ---
  executionEngine: ExecutionEngine;
  setExecutionEngine: (engine: ExecutionEngine) => void;
  
  controlFlowProvider: ControlFlowProvider;
  setControlFlowProvider: (provider: ControlFlowProvider) => void;
  
  customBaseUrl: string;
  setCustomBaseUrl: (url: string) => void;
  
  // --- API Key State (for display purposes only) ---
  // This no longer controls API calls but can be used to show status
  areKeysSet: boolean; 
  keysJustSet: boolean;
  setKeys: (keys: { gemini: string; alphaVantage: string; fred: string }) => void;
  acknowledgeKeysSet: () => void;
}

export const useStore = create<AppState>((set) => ({
  // --- UI & Execution State ---
  executionEngine: "Gemini (Visual)",
  setExecutionEngine: (engine) => set({ executionEngine: engine }),

  controlFlowProvider: "openai", // Default provider for the Python backend
  setControlFlowProvider: (provider) => set({ controlFlowProvider: provider }),

  customBaseUrl: "",
  setCustomBaseUrl: (url) => set({ customBaseUrl: url }),

  // --- API Key State (for display purposes only) ---
  areKeysSet: false, // This is now a "display-only" flag
  keysJustSet: false,
  setKeys: (keys) => {
    // This action can be repurposed to check key status from the backend in the future
    const areSet = !!(keys.gemini && keys.gemini.trim());
    set({ areKeysSet: areSet, keysJustSet: areSet });
  },
  acknowledgeKeysSet: () => set({ keysJustSet: false }),
}));
