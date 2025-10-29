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
import { FollowupPills } from "@/components/followup_questions_pill"
import { PromptSuggestions } from "@/components/prompt-suggestions"
import { chatAPI, chatStreamAPI, type ChatContext } from "@/app/api/chat"
import { useToast } from "@/hooks/use-toast"
import { ca } from "date-fns/locale"
import { set } from "date-fns"

export function ChatPanel() {
  const {
    language,
    indexName,
    indexStatus,
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
  const { toast } = useToast()
  const [input, setInput] = useState("")
  const [followupQuestions, setFollowupQuestions] = useState<string[]>([])
  
  // khi người dùng gõ, clear gợi ý (tránh cũ dính sang câu sau)
  const onInputChange = (v: string) => {
    setInput(v)
    if (followupQuestions.length > 0) setFollowupQuestions([])
  }
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [useStreaming, setUseStreaming] = useState(false) // Toggle streaming mode
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // ============================================================
  // NON-STREAMING HANDLER
  // ============================================================

  const handleSendNonStreaming = async (userMessage: string) => {
    try {
      setIsStreaming(true)

      // Show loading thoughts
      setModelThoughts(
        language === "en"
          ? "Searching through documents...\n\nAnalyzing context...\n\nFormulating response..."
          : "Đang tìm kiếm trong tài liệu...\n\nPhân tích ngữ cảnh...\n\nĐang xây dựng câu trả lời...",
      )

      const response = await chatAPI(userMessage, indexName)

      // Set follow-up questions
      setFollowupQuestions(response.followup_questions ?? [])

      // Format contets for thoughts panel
      const contextSummary = response.contexts
        .map(
          (ctx: ChatContext, idx: number) =>
            `[${idx + 1}]${ctx.source} (page ${ctx.page}) - Score: ${ctx.score.toFixed(2)}\n${ctx.preview}`,
        ).join("\n\n")
        
      setModelThoughts(
        `Model: ${response.model}` +
        `Found ${response.contexts.length} relevant contexts: \n\n`+
        contextSummary
      )

      // Add assistant response
      addMessage({
        role: "assistant",
        content: response.answer,
      })
    } catch (error: any) {
      console.error("Chat error:", error)
      toast({
        title: language === "en" ? "Error" : "Lỗi",
        description: error.message || "Failed to get response",
        variant: "destructive",
      })

      // Add error message
      addMessage({
        role: "assistant",
        content:
          language === "en"
            ? `❌ Sorry, I encountered an error: ${error.message}`
            : `❌ Xin lỗi, đã xảy ra lỗi: ${error.message}`,
      })
    } finally {
      setIsStreaming(false)
    }
  }
  
  // ============================================================
  // STREAMING HANDLER
  // ============================================================
  const handleSendStreaming = async (userMessage: string) => {
    try {
      setIsStreaming(true)
      setStreamingContent("")

      // Show loading thoughts
      setModelThoughts(
        language === "en"
          ? "Searching through documents...\n\nAnalyzing context...\n\nFormulating response..."
          : "Đang tìm kiếm trong tài liệu...\n\nPhân tích ngữ cảnh...\n\nĐang xây dựng câu trả lời..."
      )
      await chatStreamAPI(
        userMessage,
        indexName,
        // onChunk: accumulate streaming content
        (chunk) => {
          setStreamingContent((prev) => prev + chunk)
        },
        // onComplete: save the full message
        () => {
          addMessage({
            role: "assistant",
            content: streamingContent,
          })
          setStreamingContent("")
          setIsStreaming(false)
        },
        // onError: handle errors
        (error) => {
          console.error("Streaming chat error:", error)
          toast({
            title: language === "en" ? "Error" : "Lỗi",
            description: error.message,
            variant: "destructive",
          })
          setStreamingContent("")
          setIsStreaming(false)
        }
      )
    } catch (error: any) {
      console.error("Stream Chat error:", error)
      toast({
        title: language === "en" ? "Error" : "Lỗi",
        description: error.message,
        variant: "destructive",
      })
      setIsStreaming(false)
    }
  }

  // ============================================================
  // UNIFIED SEND HANDLER
  // ============================================================
  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    // Check if index is ready
    if (indexStatus === "ready") {
      toast({
        title: language === "en" ? "Index not ready" : "Chỉ mục chưa sẵn sàng",
        description: language === "en"
          ? "Please build or load an index first before chatting."
          : "Vui lòng xây dựng hoặc tải một chỉ mục trước khi trò chuyện.",
        variant: "destructive",
      })
      return
    }
    
    const userMessage = input.trim()
    setInput("")

    // Add user message
    addMessage({ role: "user", content: userMessage })

    // Open right panel on first prompt
    if (!hasSentFirstPrompt) {
      setHasSentFirstPrompt(true)
      if (!rightOpen) setRightOpen(true)
    }

    // Choose streaming or non-streaming handler
    if (useStreaming) {
      await handleSendStreaming(userMessage)
    } else {
      await handleSendNonStreaming(userMessage)
    }
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
                {language === "en" 
                  ? "Ask questions about your PDF documents" 
                  : "Đặt câu hỏi về tài liệu PDF của bạn"}
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            
            {/* Streaming message preview */}
            {isStreaming && streamingContent && (
              <div className="flex gap-3 rounded-lg border border-border bg-card p-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent">
                  <Sparkles className="h-5 w-5 animate-pulse text-accent-foreground" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="text-sm font-medium">Assistant</div>
                  <div className="text-sm leading-relaxed text-foreground">
                    {streamingContent}
                    <span className="animate-pulse">▊</span>
                  </div>
                </div>
              </div>
            )}

            {/* Loading indicator for non-streaming */}
            {isStreaming && !streamingContent && (
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
          {/* Follow-up Question Pills */}
          <FollowupPills 
          items={followupQuestions} 
          onPick={(q) => {
            setInput(q)
            textareaRef.current?.focus()
          }} />
          <PromptSuggestions onSuggestionClick={handleSuggestionClick} />

          {/* Settings */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch id="save-history" checked={saveChatHistory} onCheckedChange={setSaveChatHistory} />
              <Label htmlFor="save-history" className="text-xs text-muted-foreground">
                {t("saveChatHistory")}
              </Label>
            </div>

            <div className="flex items-center gap-2">
              <Switch id="use-streaming" checked={useStreaming} onCheckedChange={setUseStreaming} />
              <Label htmlFor="use-streaming" className="text-xs text-muted-foreground">
                {language === "en" ? "Stream response" : "Truyền phản hồi"}
              </Label>
            </div>
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
              disabled={!input.trim() || isStreaming || indexStatus === "ready"}
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
