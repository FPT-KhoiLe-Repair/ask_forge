"use client"

import { motion, AnimatePresence } from "framer-motion"
import { ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { useStore } from "@/lib/store"

export function FollowupPills({
  items,
  onPick,
}: {
  items: string[]
  onPick: (text: string) => void
}) {
  const isDarkMode = useStore((state) => state.isDarkMode)

  if (!items?.length) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 6, scale: 0.98 }}
        transition={{ type: "spring", stiffness: 320, damping: 24 }}
        className="w-full"
      >
        <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Suggested Follow-ups
        </div>

        <div className="relative">
          {/* <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-background to-transparent pointer-events-none z-10" /> */}

          <div className="flex flex-col gap-2 overflow-y-auto max-h-60 pb-4 scroll-smooth snap-y snap-mandatory">
            {items.map((q, i) => (
              <motion.button
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => onPick(q)}
                title={q}
                className={cn(
                  "flex items-center gap-2 snap-start px-4 py-2.5 rounded-full w-full",
                  "border transition-all duration-200 font-medium text-sm",
                  "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring",
                  isDarkMode
                    ? "border-accent/40 bg-card/50 hover:bg-card hover:border-accent/80 text-foreground hover:shadow-lg hover:shadow-accent/20 active:scale-95"
                    : "border-primary/30 bg-background hover:bg-card hover:border-primary/60 text-foreground hover:shadow-md hover:shadow-primary/10 active:scale-95",
                )}
              >
                <span
                  className={cn(
                    isDarkMode ? "text-muted-foreground group-hover:text-foreground" : "text-muted-foreground",
                    "truncate flex-1 text-left"
                  )}
                >
                  {q}
                </span>
                <ChevronRight
                  className={cn("h-4 w-4 transition-colors shrink-0", isDarkMode ? "text-accent/60" : "text-primary/60")}
                />
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}