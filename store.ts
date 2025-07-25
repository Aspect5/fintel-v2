import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Notification } from './frontend/src/types';

export type ControlFlowProvider = 'openai' | 'google' | 'local';

export interface AppState {
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
      controlFlowProvider: 'openai',
      customBaseUrl: '',
      isApiKeyModalOpen: false,
      notification: null,

      setControlFlowProvider: (provider) => set({ controlFlowProvider: provider }),
      setCustomBaseUrl: (url) => set({ customBaseUrl: url }),
      setIsApiKeyModalOpen: (isOpen) => set({ isApiKeyModalOpen: isOpen }),
      setNotification: (notification) => set({ notification }),
    }),
    {
      name: 'fintel-app-storage',
      partialize: (state) => ({
        controlFlowProvider: state.controlFlowProvider,
        customBaseUrl: state.customBaseUrl,
      }),
    }
  )
);