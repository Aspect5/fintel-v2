import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Notification, ChatMessage } from '../types';

export type ControlFlowProvider = 'openai' | 'google' | 'local';

export interface WorkflowSuggestion {
  workflow_type: string;
  query: string;
}

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

  // Suggested workflow confirmation
  workflowSuggestion: WorkflowSuggestion | null;
  setWorkflowSuggestion: (suggestion: WorkflowSuggestion | null) => void;

  // Selected workflow for Workflow tab synchronization
  selectedWorkflow: string | null;
  setSelectedWorkflow: (workflow: string | null) => void;
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

      workflowSuggestion: null,
      setWorkflowSuggestion: (suggestion) => set({ workflowSuggestion: suggestion }),

      selectedWorkflow: 'quick_stock_analysis',
      setSelectedWorkflow: (workflow) => set({ selectedWorkflow: workflow }),
    }),
    {
      name: 'fintel-app-storage',
      partialize: (state) => ({
        controlFlowProvider: state.controlFlowProvider,
        customBaseUrl: state.customBaseUrl,
        chatMessages: state.chatMessages,
        workflowSuggestion: state.workflowSuggestion,
        selectedWorkflow: state.selectedWorkflow,
      }),
    }
  )
);