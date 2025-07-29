import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Notification, ChatMessage } from './frontend/src/types';

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

  // Chat persistence
  chatMessages: ChatMessage[];
  addChatMessage: (message: ChatMessage) => void;
  clearChatMessages: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      controlFlowProvider: 'openai',
      customBaseUrl: '',
      isApiKeyModalOpen: false,
      notification: null,
      chatMessages: [],

      setControlFlowProvider: (provider) => set({ controlFlowProvider: provider }),
      setCustomBaseUrl: (url) => set({ customBaseUrl: url }),
      setIsApiKeyModalOpen: (isOpen) => set({ isApiKeyModalOpen: isOpen }),
      setNotification: (notification) => set({ notification }),
      addChatMessage: (message) => set((state) => ({ 
        chatMessages: [...state.chatMessages, message] 
      })),
      clearChatMessages: () => set({ chatMessages: [] }),
    }),
    {
      name: 'fintel-app-storage',
      partialize: (state) => ({
        controlFlowProvider: state.controlFlowProvider,
        customBaseUrl: state.customBaseUrl,
        chatMessages: state.chatMessages,
      }),
    }
  )
);