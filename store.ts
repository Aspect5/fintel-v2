import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Notification } from './types';

// PRESERVE both execution engines
export type ExecutionEngine = 'Gemini (Visual)' | 'ControlFlow (Python)';
export type ControlFlowProvider = 'openai' | 'google' | 'local';

export interface AppState {
  // KEEP executionEngine - it's still needed for dual-engine support
  executionEngine: ExecutionEngine;
  setExecutionEngine: (engine: ExecutionEngine) => void;

  controlFlowProvider: ControlFlowProvider;
  setControlFlowProvider: (provider: ControlFlowProvider) => void;

  customBaseUrl: string;
  setCustomBaseUrl: (url: string) => void;

  isApiKeyModalOpen: boolean;
  setIsApiKeyModalOpen: (isOpen: boolean) => void;

  notification: Notification | null;
  setNotification: (notification: Notification | null) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      executionEngine: 'Gemini (Visual)', // Keep default
      controlFlowProvider: 'openai',
      customBaseUrl: '',
      isApiKeyModalOpen: false,
      notification: null,

      setExecutionEngine: (engine) => set({ executionEngine: engine }),
      setControlFlowProvider: (provider) => set({ controlFlowProvider: provider }),
      setCustomBaseUrl: (url) => set({ customBaseUrl: url }),
      setIsApiKeyModalOpen: (isOpen) => set({ isApiKeyModalOpen: isOpen }),
      setNotification: (notification) => set({ notification }),
    }),
    {
      name: 'fintel-app-storage',
      partialize: (state) => ({
        executionEngine: state.executionEngine, // PRESERVE in localStorage
        controlFlowProvider: state.controlFlowProvider,
        customBaseUrl: state.customBaseUrl,
      }),
    }
  )
);