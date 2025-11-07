"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Send, Sparkles, Zap } from "lucide-react"
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
import { motion, AnimatePresence } from "framer-motion"
import { set } from "date-fns"

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
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key)

  const scrollRef = useRef<HTMLDivElement>(null)
  const lastYRef = useRef(0)
  const [showPills, setShowPills] = useState(true) // true: hiện, false: ẩn

  const [qgLoading, setQGLoading] = useState(false)

  const scrollToBottom = () => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
  }


  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    if (isStreaming) {
      // Đang stream → ẩn pills để UI thoáng
      setShowPills(false)
      return
    }
    lastYRef.current = el.scrollTop
    const THRESH = 6
    const BOTTOM_PAD = 0

    const onScroll = () => {
      const y = el.scrollTop
      const delta = y - lastYRef.current
      lastYRef.current = y

      const atBottom = el.scrollHeight - el.clientHeight - y <= BOTTOM_PAD

      if (delta < -THRESH) {
        // đang cuộn lên
        setShowPills(false)
      } else if (atBottom) {
        // đang cuộn xuống hoặc đã về gần đáy
        setShowPills(true)
      }
    }

    el.addEventListener("scroll", onScroll, { passive: true })
    return () => el.removeEventListener("scroll", onScroll)
  }, [])

  const onInputChange = (v: string) => {
    setInput(v)
    if (followupQuestions.length > 0) setFollowupQuestions([])
  }

  const handleSendStreaming = async (userMessage: string) => {
    try {
      setIsStreaming(true)
      setStreamingContent("")

      setModelThoughts(
        language === "en"
          ? "Searching through documents...\n\nAnalyzing context...\n\nFormulating response..."
          : "Đang tìm kiếm trong tài liệu...\n\nPhân tích ngữ cảnh...\n\nĐang xây dựng câu trả lời...",
      )

      let fullContent = ""

      await chatStreamAPI(userMessage, indexName!, {
        onToken: (token) => {
          fullContent += token
          setStreamingContent((prev) => prev + token)
        },

        onContexts: (ctxs) => {
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

        // CHỈ hiển thị trạng thái; KHÔNG poll ở đây (chat.ts đã lo)
        onQGJob: (jobId) => {
          setQGLoading(true)
          const current = (useStore.getState() as any).modelThoughts ?? ""
          const extra =
            "\n" +
            (language === "en"
              ? `Generating follow-up questions (job: ${jobId})...`
              : `Đang tạo câu hỏi gợi ý (job: ${jobId})...`)
          setModelThoughts(current + extra)
        },

        onComplete: () => {
          if (fullContent.trim()) {
            addMessage({ role: "assistant", content: fullContent })
          }
          setIsStreaming(false)
          setTimeout(() => setStreamingContent(""), 100)
        },

        onError: (error) => {
          toast({
            title: language === "en" ? "Error" : "Lỗi",
            description: error.message,
            variant: "destructive",
          })
          setIsStreaming(false)
          setStreamingContent("")
        },

        // Nhận câu hỏi gợi ý từ chat.ts (sau khi poll xong)
        setFollowupQuestions: (qs) => {
          setFollowupQuestions(qs),
            setQGLoading(false)
        },
      })
    } catch (error: any) {
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
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="mx-auto mb-6 w-16 h-16 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h2 className="mb-3 text-2xl font-bold text-foreground">
                {language === "en" ? "Start a Conversation" : "Bắt đầu cuộc trò chuyện"}
              </h2>
              <p className="text-sm text-muted-foreground max-w-sm">
                {language === "en" ? "Ask questions about your PDF documents" : "Đặt câu hỏi về tài liệu PDF của bạn"}
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {streamingContent && (
              <div className="flex gap-3 rounded-lg border border-accent/20 bg-accent/5 p-4 animate-fade-in-up">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <Zap className={`h-5 w-5 ${isStreaming ? "animate-pulse" : ""}`} />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Assistant</div>
                  <div className="text-sm leading-relaxed text-foreground whitespace-pre-wrap prose-custom">
                    {streamingContent}
                    {isStreaming && <span className="animate-pulse ml-1">▊</span>}
                  </div>
                </div>
              </div>
            )}

            {isStreaming && !streamingContent && (
              <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-card border border-border">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                  <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                  <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-primary" />
                </div>
                <span className="text-sm font-medium text-muted-foreground">
                  {language === "en" ? "Thinking..." : "Đang suy nghĩ..."}
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="border-t border-border bg-card/50 backdrop-blur-sm p-4 sm:p-6">
        <div className="mx-auto max-w-3xl space-y-4">

          <AnimatePresence mode="popLayout">
            {qgLoading || (isStreaming && followupQuestions.length === 0) ? (
              // ===== Loader ở vị trí của FollowupPills =====
              <motion.div
                key="followup-loader"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ type: "spring", stiffness: 320, damping: 28 }}
                className="flex items-center justify-between rounded-xl border border-border bg-card/60 backdrop-blur-sm px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                    <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                    <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-primary" />
                  </div>
                  <span className="text-sm font-medium text-muted-foreground">
                    {language === "en" ? "Generating Follow up Questions..." : "Đang suy nghĩ..."}
                  </span>
                </div>

                {/* shimmer bar */}
                <div className="hidden sm:block h-2 w-28 rounded-full bg-muted overflow-hidden">
                  <div className="h-full w-1/3 animate-[pulse_1.2s_ease-in-out_infinite]" />
                </div>
              </motion.div>
            ) : (
              followupQuestions.length > 0 &&
              showPills && (
                <motion.div
                  key="followup-pills"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 12 }}
                  transition={{ type: "spring", stiffness: 320, damping: 28 }}
                >
                  <FollowupPills
                    items={followupQuestions}
                    onPick={(q) => {
                      setInput(q)
                      textareaRef.current?.focus()
                    }}
                  />
                </motion.div>
              )
            )}
          </AnimatePresence>

          {messages.length === 0 && <PromptSuggestions onSuggestionClick={handleSuggestionClick} />}

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 px-2">
            <div className="flex items-center gap-3">
              <Switch id="save-history" checked={saveChatHistory} onCheckedChange={setSaveChatHistory} />
              <Label htmlFor="save-history" className="text-sm font-medium cursor-pointer">
                {t("saveChatHistory")}
              </Label>
            </div>
          </div>

          <div className="flex gap-3 items-end">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("typeMessage")}
              className="min-h-[52px] max-h-[200px] resize-none rounded-xl bg-input/50 backdrop-blur-sm border-border text-sm leading-relaxed"
              disabled={isStreaming}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming || !indexName}
              size="icon"
              className="h-[52px] w-[52px] shrink-0 rounded-xl bg-gradient-primary hover:opacity-90 button-hover"
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
