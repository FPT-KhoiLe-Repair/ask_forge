import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { Language } from "./translations"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: number
}

export type IndexStatus = "idle" | "building" | "ready" | "error"

interface AppState {
  // Language & Theme
  language: Language
  isDarkMode: boolean
  setLanguage: (lang: Language) => void
  toggleDarkMode: () => void

  leftOpen: boolean
  rightOpen: boolean
  hasSentFirstPrompt: boolean
  indexStatus: IndexStatus
  setLeftOpen: (open: boolean) => void
  setRightOpen: (open: boolean) => void
  setHasSentFirstPrompt: (sent: boolean) => void
  setIndexStatus: (status: IndexStatus) => void

  // Index Management
  indexName: string
  setIndexName: (name: string) => void
  pdfFiles: File[]
  addPdfFiles: (files: File[]) => void
  clearPdfFiles: () => void

  // Chat
  messages: Message[]
  addMessage: (message: Omit<Message, "id" | "timestamp">) => void
  clearMessages: () => void
  saveChatHistory: boolean
  setSaveChatHistory: (save: boolean) => void

  // Model Thoughts
  modelThoughts: string
  setModelThoughts: (thoughts: string) => void
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Language & Theme
      language: "en",
      isDarkMode: true,
      setLanguage: (lang) => set({ language: lang }),
      toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),

      leftOpen: true,
      rightOpen: false,
      hasSentFirstPrompt: false,
      indexStatus: "idle",
      setLeftOpen: (open) => set({ leftOpen: open }),
      setRightOpen: (open) => set({ rightOpen: open }),
      setHasSentFirstPrompt: (sent) => set({ hasSentFirstPrompt: sent }),
      setIndexStatus: (status) => set({ indexStatus: status }),

      // Index Management
      indexName: "MyIndex",
      setIndexName: (name) => set({ indexName: name }),
      pdfFiles: [],
      addPdfFiles: (files) => set((state) => ({ pdfFiles: [...state.pdfFiles, ...files] })),
      clearPdfFiles: () => set({ pdfFiles: [], indexStatus: "idle" }),

      // Chat
      messages: [],
      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: Math.random().toString(36).substring(7),
              timestamp: Date.now(),
            },
          ],
        })),
      clearMessages: () => set({ messages: [] }),
      saveChatHistory: false,
      setSaveChatHistory: (save) => set({ saveChatHistory: save }),

      // Model Thoughts
      modelThoughts: "",
      setModelThoughts: (thoughts) => set({ modelThoughts: thoughts }),
    }),
    {
      name: "pdf-chatbot-storage",
      partialize: (state) => ({
        language: state.language,
        isDarkMode: state.isDarkMode,
        indexName: state.indexName,
        messages: state.saveChatHistory ? state.messages : [],
        saveChatHistory: state.saveChatHistory,
        leftOpen: state.leftOpen,
        rightOpen: state.rightOpen,
      }),
    },
  ),
)
