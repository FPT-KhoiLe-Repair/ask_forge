"use client"

import { FileText, Lightbulb, MessageSquare, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useStore } from "@/lib/store"

interface PromptSuggestionsProps {
  onSuggestionClick: (suggestion: string) => void
}

const suggestions = {
  en: [
    { icon: FileText, text: "Summarize the main points" },
    { icon: Search, text: "What are the key findings?" },
    { icon: Lightbulb, text: "Explain this concept" },
    { icon: MessageSquare, text: "Compare these sections" },
  ],
  vn: [
    { icon: FileText, text: "Tóm tắt các điểm chính" },
    { icon: Search, text: "Những phát hiện chính là gì?" },
    { icon: Lightbulb, text: "Giải thích khái niệm này" },
    { icon: MessageSquare, text: "So sánh các phần này" },
  ],
}

export function PromptSuggestions({ onSuggestionClick }: PromptSuggestionsProps) {
  const { language, indexStatus } = useStore()
  const currentSuggestions = suggestions[language]

  if (indexStatus !== "ready") {
    return null
  }

  return (
    <div className="relative">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-card to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-card to-transparent" />

      <ScrollArea className="w-full">
        <div className="flex gap-2 px-1 py-1">
          {currentSuggestions.map((suggestion, index) => {
            const Icon = suggestion.icon
            return (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => onSuggestionClick(suggestion.text)}
                className="shrink-0 gap-2 rounded-2xl bg-glass text-xs hover:bg-primary/10"
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="max-w-[200px] truncate">{suggestion.text}</span>
              </Button>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}
