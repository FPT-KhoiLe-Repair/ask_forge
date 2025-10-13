"use client"

import type React from "react"

import { useEffect } from "react"
import { useStore } from "@/lib/store"

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const isDarkMode = useStore((state) => state.isDarkMode)

  useEffect(() => {
    const root = document.documentElement
    if (isDarkMode) {
      root.classList.add("dark")
    } else {
      root.classList.remove("dark")
    }
  }, [isDarkMode])

  return <>{children}</>
}
