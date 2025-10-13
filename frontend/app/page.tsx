"use client"

import { PanelLeftOpen, PanelRightOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Topbar } from "@/components/topbar"
import { ThemeProvider } from "@/components/theme-provider"
import { IndexPanel } from "@/components/index-panel"
import { ChatPanel } from "@/components/chat-panel"
import { ModelThoughtsPanel } from "@/components/model-thoughts-panel"
import { useStore } from "@/lib/store"

export default function Home() {
  const { leftOpen, rightOpen, setLeftOpen, setRightOpen } = useStore()

  return (
    <ThemeProvider>
      <div className="flex h-screen flex-col">
        <Topbar />
        <main className="relative flex flex-1 overflow-hidden">
          {!leftOpen && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setLeftOpen(true)}
              className="absolute left-2 top-2 z-20 h-8 w-8 rounded-lg bg-card/80 backdrop-blur-sm hover:bg-card"
            >
              <PanelLeftOpen className="h-4 w-4" />
              <span className="sr-only">Open left panel</span>
            </Button>
          )}

          {!rightOpen && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setRightOpen(true)}
              className="absolute right-2 top-2 z-20 h-8 w-8 rounded-lg bg-card/80 backdrop-blur-sm hover:bg-card"
            >
              <PanelRightOpen className="h-4 w-4" />
              <span className="sr-only">Open right panel</span>
            </Button>
          )}

          <IndexPanel />
          <ChatPanel />
          <ModelThoughtsPanel />
        </main>
      </div>
    </ThemeProvider>
  )
}
