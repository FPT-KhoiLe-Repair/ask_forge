"use client"

import { Brain, PanelRightClose } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useStore } from "@/lib/store"
import { getTranslation } from "@/lib/translations"

export function ModelThoughtsPanel() {
  const { language, modelThoughts, rightOpen, setRightOpen } = useStore()
  const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key)

  return (
    <AnimatePresence mode="wait">
      {rightOpen && (
        <motion.aside
          initial={{ x: 320, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 320, opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="hidden w-80 flex-col border-l border-border bg-glass p-4 lg:flex"
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold">{t("modelThoughts")}</h2>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setRightOpen(false)} className="h-8 w-8">
              <PanelRightClose className="h-4 w-4" />
              <span className="sr-only">Close panel</span>
            </Button>
          </div>

          <Card className="flex-1 rounded-2xl border-border bg-muted/30 backdrop-blur-sm">
            <ScrollArea className="h-full p-4">
              {modelThoughts ? (
                <div className="space-y-2">
                  {modelThoughts.split("\n\n").map((paragraph, index) => (
                    <div key={index} className="text-sm leading-relaxed text-foreground">
                      {paragraph}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-center">
                  <p className="text-sm text-muted-foreground">{t("noThoughts")}</p>
                </div>
              )}
            </ScrollArea>
          </Card>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
