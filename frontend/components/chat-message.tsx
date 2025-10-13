"use client"

import { User, Bot } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Message } from "@/lib/store"

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex gap-3 rounded-lg p-4", isUser ? "bg-muted/50" : "bg-card border border-border")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser ? "bg-primary" : "bg-accent",
        )}
      >
        {isUser ? (
          <User className="h-5 w-5 text-primary-foreground" />
        ) : (
          <Bot className="h-5 w-5 text-accent-foreground" />
        )}
      </div>
      <div className="flex-1 space-y-2">
        <div className="text-sm font-medium">{isUser ? "You" : "Assistant"}</div>
        <div className="text-sm leading-relaxed text-foreground">{message.content}</div>
      </div>
    </div>
  )
}
