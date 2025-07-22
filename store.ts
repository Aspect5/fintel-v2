import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Notification } from './types';

// Define types for the execution engines and providers
export type ExecutionEngine = 'Gemini (Visual)' | 'ControlFlow (Python)';
export type ControlFlowProvider = 'openai' | 'gemini' | 'local';

// Define the shape of the application's global state
export interface AppState {
  // --- UI & Execution Configuration ---
  executionEngine: ExecutionEngine;
  setExecutionEngine: (engine: ExecutionEngine) => void;
  
  controlFlowProvider: ControlFlowProvider;
  setControlFlowProvider: (provider: ControlFlowProvider) => void;
  
  customBaseUrl: string;
  setCustomBaseUrl: (url: string) => void;

  // --- UI State ---
  isApiKeyModalOpen: boolean;
  setIsApiKeyModalOpen: (isOpen: boolean) => void;

  // --- Notification State ---
  notification: Notification | null;
  setNotification: (notification: Notification | null) => void;
}

// Create the Zustand store with persistence for configuration
export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // --- Default State Values ---
      executionEngine: 'Gemini (Visual)',
      controlFlowProvider: 'openai',
      customBaseUrl: '',
      isApiKeyModalOpen: false,
      notification: null,

      // --- State Setters ---
      setExecutionEngine: (engine) => set({ executionEngine: engine }),
      setControlFlowProvider: (provider) => set({ controlFlowProvider: provider }),
      setCustomBaseUrl: (url) => set({ customBaseUrl: url }),
      setIsApiKeyModalOpen: (isOpen) => set({ isApiKeyModalOpen: isOpen }),
      setNotification: (notification) => set({ notification }),
    }),
    {
      name: 'fintel-app-storage', // Name for persisting to localStorage
      // Select which parts of the state to persist. 
      // Transient UI state like modals and notifications are not persisted.
      partialize: (state) => ({
        executionEngine: state.executionEngine,
        controlFlowProvider: state.controlFlowProvider,
        customBaseUrl: state.customBaseUrl,
      }),
    }
  )
);
