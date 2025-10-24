"use client"

import { Moon, Sun, Languages, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useStore } from "@/lib/store"
import { getTranslation } from "@/lib/translations"
import { MobileSidebar }  from "@/components/mobile-sidebar"

export function Topbar() {
  const { language, isDarkMode, setLanguage, toggleDarkMode } = useStore()
  const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key)

  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-sm">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <MobileSidebar />
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-primary">
            <span className="font-mono text-sm font-bold text-primary-foreground">AI</span>
          </div>
          <h1 className="text-lg font-semibold">PDF Chatbot</h1>
          <Sparkles className="h-4 w-4 text-accent transition-transform hover:scale-110" />
        </div>

        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <Languages className="h-5 w-5" />
                <span className="sr-only">{t("language")}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setLanguage("en")}>English {language === "en" && "✓"}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setLanguage("vn")}>
                Tiếng Việt {language === "vn" && "✓"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button variant="ghost" size="icon" onClick={toggleDarkMode}>
            {isDarkMode ? (
              <>
                <Sun className="h-5 w-5" />
                <span className="sr-only">{t("lightMode")}</span>
              </>
            ) : (
              <>
                <Moon className="h-5 w-5" />
                <span className="sr-only">{t("darkMode")}</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </header>
  )
}
