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
import { chatStreamAPI, type ChatContext } from "@/app/api/chat"
import { useToast } from "@/hooks/use-toast"
import { API_BASE } from "@/lib/config"

export function ChatPanel() {
  const {
    language,
    indexName,
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

  // when user types, clear stale followups
  const onInputChange = (v: string) => {
    setInput(v)
    if (followupQuestions.length > 0) setFollowupQuestions([])
  }

  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
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
  // STREAMING HANDLER (SSE)
  // ============================================================
  const handleSendStreaming = async (userMessage: string) => {
    try {
      setIsStreaming(true)
      setStreamingContent("")

      // loading thoughts
      setModelThoughts(
        language === "en"
          ? "Searching through documents...\n\nAnalyzing context...\n\nFormulating response..."
          : "Đang tìm kiếm trong tài liệu...\n\nPhân tích ngữ cảnh...\n\nĐang xây dựng câu trả lời...",
      )

      // helper để poll qg_job - KHÔNG CÓ TIMEOUT
      const pollQG = async (pollUrl: string, tries = 0) => {
        try {
          const url = new URL(pollUrl, API_BASE).toString();
          console.log(`🔄 Polling QG at (attempt ${tries + 1}):`, url);
          const res = await fetch(url);
          
          if (!res.ok) {
            console.warn("⚠️ QG poll failed:", res.status);
            return;
          }
          
          const data = await res.json();
          console.log("📊 QG poll response:", data);
          
          // Nếu status là "done" và có followup_questions
          if (data?.status === "done" && Array.isArray(data?.followup_questions)) {
            console.log("✅ QG complete, questions:", data.followup_questions);
            setFollowupQuestions(data.followup_questions);
            return;
          }
          
          // Nếu status là "pending", tiếp tục poll
          if (data?.status === "pending") {
            console.log("⏳ QG pending, retrying in 1.5s...");
            setTimeout(() => pollQG(pollUrl, tries + 1), 1500);
            return;
          }
          
          // Nếu có error từ backend
          if (data?.status === "error") {
            console.error("❌ QG error from backend:", data.error);
            return;
          }
          
        } catch (e) {
          console.warn("❌ QG polling error:", e);
        }
      }

      let fullContent = "";

      await chatStreamAPI(userMessage, indexName!, {
        onToken: (token) => {
          console.log("📝 Token:", token.substring(0, 50))
          fullContent += token;
          setStreamingContent((prev) => prev + token)
        },

        onContexts: (ctxs) => {
          console.log("📚 Contexts:", ctxs.length)
          const summary = ctxs
            .map(
              (ctx: ChatContext, idx: number) =>
                `[${idx + 1}] ${ctx.source} (page ${ctx.page}) - Score: ${ctx.score.toFixed(2)}\n${ctx.preview}`,
            )
            .join("\n\n")
          setModelThoughts(
            (language === "en"
              ? "Streaming... Found relevant contexts:\n\n"
              : "Đang truyền... Đã tìm thấy ngữ cảnh liên quan:\n\n") + summary,
          )
        },

        onQGJob: (jobId, pollUrl) => {
          console.log("🔄 QG Job received:", jobId, pollUrl)
          const current = (useStore.getState() as any).modelThoughts ?? ""
          const extra =
            "\n" +
            (language === "en"
              ? `Generating follow-up questions (job: ${jobId})...`
              : `Đang tạo câu hỏi gợi ý (job: ${jobId})...`)
          setModelThoughts(current + extra)
          void pollQG(pollUrl)
        },

        onComplete: () => {
          console.log("✅ Stream complete, saving message...")
          // Lưu message từ fullContent đã tích lũy
          if (fullContent.trim()) {
            console.log("💾 Saving message, length:", fullContent.length)
            addMessage({ role: "assistant", content: fullContent })
          }
          // Giữ nguyên streamingContent để hiển thị cho đến khi clear
          setIsStreaming(false)
          // Clear sau 100ms để tránh flickering
          setTimeout(() => {
            setStreamingContent("")
          }, 100)
        },

        onError: (error) => {
          console.error("❌ Stream error:", error)
          toast({
            title: language === "en" ? "Error" : "Lỗi",
            description: error.message,
            variant: "destructive",
          })
          setIsStreaming(false)
          setStreamingContent("")
        },
      })
    } catch (error: any) {
      console.error("🔥 Fatal error:", error)
      toast({
        title: language === "en" ? "Error" : "Lỗi",
        description: error?.message || "An unexpected error occurred",
        variant: "destructive",
      })
      setIsStreaming(false)
      setStreamingContent("")
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    if (!indexName) {
      toast({
        title: language === "en" ? "No index selected" : "Chưa chọn chỉ mục",
        description:
          language === "en" ? "Please select or build an index first." : "Vui lòng chọn hoặc xây dựng chỉ mục trước.",
        variant: "destructive",
      })
      return
    }

    const userMessage = input.trim()
    setInput("")
    addMessage({ role: "user", content: userMessage })

    if (!hasSentFirstPrompt) {
      setHasSentFirstPrompt(true)
      if (!rightOpen) setRightOpen(true)
    }

    await handleSendStreaming(userMessage)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
    textareaRef.current?.focus()
  }

  return (
    <div className="flex flex-1 flex-col bg-background">
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

            {/* Streaming preview - chỉ hiện khi đang stream */}
            {streamingContent && (
              <div className="flex gap-3 rounded-lg border border-border bg-card p-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent">
                  <Sparkles className={`h-5 w-5 text-accent-foreground ${isStreaming ? 'animate-pulse' : ''}`} />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="text-sm font-medium">Assistant</div>
                  <div className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                    {streamingContent}
                    {isStreaming && <span className="animate-pulse">▊</span>}
                  </div>
                </div>
              </div>
            )}

            {/* Thinking indicator */}
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

      <div className="border-t border-border bg-card/80 p-4 backdrop-blur-sm">
        <div className="mx-auto max-w-3xl space-y-4">
          {followupQuestions.length > 0 && (
            <FollowupPills
              items={followupQuestions}
              onPick={(q) => {
                setInput(q)
                textareaRef.current?.focus()
              }}
            />
          )}
          
          {messages.length === 0 && <PromptSuggestions onSuggestionClick={handleSuggestionClick} />}

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch id="save-history" checked={saveChatHistory} onCheckedChange={setSaveChatHistory} />
              <Label htmlFor="save-history" className="text-xs text-muted-foreground">
                {t("saveChatHistory")}
              </Label>
            </div>
          </div>

          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("typeMessage")}
              className="min-h-[60px] resize-none rounded-2xl bg-background/80 backdrop-blur-sm"
              disabled={isStreaming}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming || !indexName}
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