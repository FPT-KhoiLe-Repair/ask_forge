"use client"

import { motion, AnimatePresence } from "framer-motion"

export function FollowupPills({
  items,
  onPick,
}: {
  items: string[]
  onPick: (text: string) => void
}) {
  if (!items?.length) return null
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 6, scale: 0.98 }}
        transition={{ type: "spring", stiffness: 320, damping: 24 }}
        className="flex flex-wrap gap-2 rounded-2xl border border-border bg-card/80 p-2"
      >
        {items.map((q, i) => (
          <button
            key={i}
            onClick={() => onPick(q)}
            className="rounded-full border border-border px-3 py-1 text-sm hover:bg-accent"
            title={q}
          >
            {q}
          </button>
        ))}
      </motion.div>
    </AnimatePresence>
  )
}