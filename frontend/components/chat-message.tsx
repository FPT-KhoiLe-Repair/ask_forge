"use client"

import { User, Bot, Copy, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Message } from "@/lib/store"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useState } from "react"
import { useStore } from "@/lib/store"

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const isDarkMode = useStore((state) => state.isDarkMode)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCode(text)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  return (
    <div
      className={cn(
        "animate-fade-in-up flex gap-3 rounded-lg p-4 transition-all duration-200",
        isUser
          ? isDarkMode
            ? "bg-primary/15 border border-primary/30 ml-auto max-w-2xl hover:border-primary/50"
            : "bg-primary/8 border border-primary/20 ml-auto max-w-2xl hover:border-primary/40"
          : isDarkMode
            ? "bg-card border border-accent/20 hover:border-accent/40"
            : "bg-background border border-primary/10 hover:border-primary/20",
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg font-semibold",
          isUser
            ? "bg-primary text-primary-foreground"
            : isDarkMode
              ? "bg-accent text-accent-foreground"
              : "bg-primary text-primary-foreground",
        )}
      >
        {isUser ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
      </div>

      <div className="flex-1 space-y-2">
        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {isUser ? "You" : "Assistant"}
        </div>

        <div className="prose-custom max-w-none text-sm leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || "")
                const language = match ? match[1] : "code"
                const codeString = String(children).replace(/\n$/, "")

                if (inline) {
                  return (
                    <code
                      className={cn(
                        "px-2 py-1 rounded text-sm font-mono",
                        isDarkMode ? "bg-muted text-accent" : "bg-muted text-primary",
                      )}
                    >
                      {children}
                    </code>
                  )
                }

                return (
                  <div
                    className={cn(
                      "relative mb-3 rounded-lg overflow-hidden",
                      isDarkMode ? "bg-muted border border-border/50" : "bg-muted/50 border border-primary/10",
                    )}
                  >
                    <div
                      className={cn(
                        "flex items-center justify-between px-4 py-2 border-b",
                        isDarkMode ? "bg-muted/50 border-border/50" : "bg-muted/30 border-primary/10",
                      )}
                    >
                      <span className="text-xs font-mono text-muted-foreground">{language}</span>
                      <button
                        onClick={() => copyToClipboard(codeString)}
                        className={cn(
                          "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors",
                          isDarkMode
                            ? "text-muted-foreground hover:text-foreground hover:bg-accent/10"
                            : "text-muted-foreground hover:text-foreground hover:bg-primary/10",
                        )}
                      >
                        {copiedCode === codeString ? (
                          <>
                            <Check className="h-4 w-4" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" /> Copy
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="p-4 overflow-x-auto">
                      <code className="text-sm font-mono text-foreground" {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                )
              },
              table({ children }: any) {
                return (
                  <div
                    className={cn(
                      "mb-3 overflow-x-auto rounded-lg border",
                      isDarkMode ? "border-border/50" : "border-primary/10",
                    )}
                  >
                    <table className="w-full">{children}</table>
                  </div>
                )
              },
              th({ children }: any) {
                return (
                  <th
                    className={cn(
                      "px-4 py-2 text-left text-sm font-semibold border-b",
                      isDarkMode ? "bg-muted border-border/50" : "bg-muted/50 border-primary/10",
                    )}
                  >
                    {children}
                  </th>
                )
              },
              td({ children }: any) {
                return (
                  <td
                    className={cn("px-4 py-2 text-sm border-b", isDarkMode ? "border-border/50" : "border-primary/10")}
                  >
                    {children}
                  </td>
                )
              },
              a({ href, children }: any) {
                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn("font-medium hover:underline", isDarkMode ? "text-accent" : "text-primary")}
                  >
                    {children}
                  </a>
                )
              },
              blockquote({ children }: any) {
                return (
                  <blockquote
                    className={cn(
                      "border-l-2 pl-4 py-2 mb-3 italic",
                      isDarkMode ? "border-accent/50 text-muted-foreground" : "border-primary/30 text-muted-foreground",
                    )}
                  >
                    {children}
                  </blockquote>
                )
              },
              ul({ children }: any) {
                return <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>
              },
              ol({ children }: any) {
                return <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>
              },
              h1({ children }: any) {
                return <h1 className="text-lg font-bold mt-4 mb-2 text-foreground">{children}</h1>
              },
              h2({ children }: any) {
                return <h2 className="text-base font-bold mt-3 mb-2 text-foreground">{children}</h2>
              },
              h3({ children }: any) {
                return <h3 className="text-base font-semibold mt-3 mb-2 text-foreground">{children}</h3>
              },
            }}
          >
            {message.content?.replace(/\r\n/g, "\n") ?? ""}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
