"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { useStore } from "@/lib/store"
import { getTranslation } from "@/lib/translations"
import { ChatMessage } from "@/components/chat-message"
import { PromptSuggestions } from "@/components/prompt-suggestions"

export function ChatPanel() {
  const {
    language,
    messages,
    addMessage,
    saveChatHistory,
    setSaveChatHistory,
    setModelThoughts,
    hasSentFirstPrompt,
    setHasSentFirstPrompt,
    rightOpen,
    setRightOpen,
  } = useStore()
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMessage = input.trim()
    setInput("")
    addMessage({ role: "user", content: userMessage })

    if (!hasSentFirstPrompt) {
      setHasSentFirstPrompt(true)
      if (!rightOpen) {
        setRightOpen(true)
      }
    }

    // Mock streaming response
    setIsStreaming(true)

    // Mock model thoughts
    setModelThoughts(
      "Analyzing the question...\n\nSearching through PDF index...\n\nFound relevant sections in documents...\n\nFormulating response based on context...",
    )

    // Simulate streaming delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const mockResponse =
      "This is a mock response. In production, this would be replaced with actual AI-generated content based on your PDF documents. The response would stream in character by character for a better user experience."

    addMessage({ role: "assistant", content: mockResponse })
    setIsStreaming(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
    textareaRef.current?.focus()
  }

  return (
    <div className="flex flex-1 flex-col bg-background">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <Sparkles className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <h2 className="mb-2 text-xl font-semibold text-foreground">
                {language === "en" ? "Start a conversation" : "Bắt đầu cuộc trò chuyện"}
              </h2>
              <p className="text-sm text-muted-foreground">
                {language === "en" ? "Ask questions about your PDF documents" : "Đặt câu hỏi về tài liệu PDF của bạn"}
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="flex gap-1">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                </div>
                <span>{language === "en" ? "Thinking..." : "Đang suy nghĩ..."}</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-card/80 p-4 backdrop-blur-sm">
        <div className="mx-auto max-w-3xl space-y-4">
          <PromptSuggestions onSuggestionClick={handleSuggestionClick} />

          {/* Save Chat History Toggle */}
          <div className="flex items-center gap-2">
            <Switch id="save-history" checked={saveChatHistory} onCheckedChange={setSaveChatHistory} />
            <Label htmlFor="save-history" className="text-xs text-muted-foreground">
              {t("saveChatHistory")}
            </Label>
          </div>

          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("typeMessage")}
              className="min-h-[60px] resize-none rounded-2xl bg-background/80 backdrop-blur-sm"
              disabled={isStreaming}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              size="icon"
              className="h-[60px] w-[60px] shrink-0 rounded-2xl bg-gradient-primary hover:opacity-90"
            >
              <Send className="h-5 w-5" />
              <span className="sr-only">{t("send")}</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
