import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { ChatMessage, Notification } from './types';

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
  
  // --- Frontend-Only Key State ---
  geminiApiKey: string | null;
  setGeminiApiKey: (key: string) => void;

  // --- Chat & Notification State ---
  chatMessages: ChatMessage[];
  addChatMessage: (sender: 'user' | 'ai', content: string) => void;
  
  notification: Notification | null;
  setNotification: (notification: Notification | null) => void;
  
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  // --- UI & Execution State ---
  executionEngine: "Gemini (Visual)",
  setExecutionEngine: (engine) => set({ executionEngine: engine }),

  controlFlowProvider: "openai",
  setControlFlowProvider: (provider) => set({ controlFlowProvider: provider }),

  customBaseUrl: "",
  setCustomBaseUrl: (url) => set({ customBaseUrl: url }),

  // --- Frontend-Only Key State ---
  geminiApiKey: null,
  setGeminiApiKey: (key) => set({ geminiApiKey: key }),

  // --- Chat & Notification State ---
  chatMessages: [],
  addChatMessage: (sender, content) => {
    const newMessage: ChatMessage = {
      id: uuidv4(),
      sender,
      content,
      timestamp: new Date().toISOString(),
    };
    set((state) => ({ chatMessages: [...state.chatMessages, newMessage] }));
  },
  
  notification: null,
  setNotification: (notification) => set({ notification }),
  
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}));
