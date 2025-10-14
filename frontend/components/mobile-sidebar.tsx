"use client"

import type React from "react"

import { useState, useCallback } from "react"
import { Menu, FileText, Brain, Upload, FolderOpen, Plus, Trash2, LibraryBig } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useStore } from "@/lib/store"
import { getTranslation } from "@/lib/translations"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { buildIndexAPI, addToIndexAPI } from "@/lib/api"
import { Spinner } from "@/components/ui/spinner"

export function MobileSidebar() {
  const [open, setOpen] = useState(false)
  const { language, indexName, setIndexName, pdfFiles, addPdfFiles, clearPdfFiles, setIndexStatus, modelThoughts } =
    useStore()
  const { toast } = useToast()
  const [isDragging, setIsDragging] = useState(false)

  const [isLoadingBuild, setIsLoadingBuild] = useState(false)
  const [isLoadingAdd, setIsLoadingAdd] = useState(false)

  const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files).filter((file) => file.type === "application/pdf")

      if (files.length > 0) {
        addPdfFiles(files)
        toast({
          title: t("pdfImported"),
          description: `${files.length} PDF file(s) added`,
        })
      }
    },
    [addPdfFiles, toast],
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []).filter((file) => file.type === "application/pdf")

      if (files.length > 0) {
        addPdfFiles(files)
        toast({
          title: t("pdfImported"),
          description: `${files.length} PDF file(s) added`,
        })
      }
    },
    [addPdfFiles, toast],
  )

const handleBuildIndex = async () => {
    if (!pdfFiles.length) {
    toast({
      title: "No PDFs Found",
      description: "Please import PDF files before building the index.",
      variant: "destructive",});
    return;
  }
  try {
    setIsLoadingBuild(true);
    const result = await buildIndexAPI(pdfFiles, indexName);
    setIsLoadingBuild(false);
    // Update status and notify user
    setIndexStatus("ready");
    toast({
      title: "Index Built Successfully",
      description: `Index '${result.index_name}' created with ${result.n_files} files.`,
    });
  } catch (error: any) {
    toast({
      title: "Error Building Index",
      description: error.message || "An unknown error occurred.",
      variant: "destructive",});
  }
  }

  const handleAddToIndex = async () => {
    if (!pdfFiles.length) {
    toast({
      title: "No PDFs Found",
      description: "Please import PDF files before adding to the index.",
      variant: "destructive",});
    return;}
    try {
      setIsLoadingAdd(true);
      const result = await buildIndexAPI(pdfFiles, indexName);
      setIsLoadingAdd(false);
      // Update status and notify user
      setIndexStatus("ready");
      toast({
        title: "Files Added to Index Successfully",
        description: `Added ${result.n_files} files to index '${result.index_name}'.`,
      });
    } catch (error: any) {
      toast({
        title: "Error Adding to Index",
        description: error.message || "An unknown error occurred.",
        variant: "destructive",});
}
  }
  const handleLoadIndex = () => {
    setIndexStatus("ready")
    toast({
      title: language === "en" ? "Index Loaded" : "Đã tải chỉ mục",
      description: language === "en" ? `Loaded saved index "${indexName}"` : `Đã tải chỉ mục "${indexName}"`,
    })
  }

  const handleClearIndex = () => {
    clearPdfFiles()
    toast({
      title: t("indexCleared"),
    })
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Open menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-full p-0 sm:max-w-md">
        <Tabs defaultValue="index" className="h-full">
          <SheetHeader className="border-b border-border bg-card/80 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <SheetTitle>Menu</SheetTitle>
              <TabsList className="grid w-[200px] grid-cols-2">
                <TabsTrigger value="index" className="text-xs">
                  <FileText className="mr-1 h-3 w-3" />
                  {language === "en" ? "Index" : "Chỉ mục"}
                </TabsTrigger>
                <TabsTrigger value="thoughts" className="text-xs">
                  <Brain className="mr-1 h-3 w-3" />
                  {language === "en" ? "Thoughts" : "Suy nghĩ"}
                </TabsTrigger>
              </TabsList>
            </div>
          </SheetHeader>

          <TabsContent value="index" className="m-0 h-[calc(100%-5rem)] overflow-y-auto p-4">
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <LibraryBig className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold">{language === "en" ? "Index" : "Chỉ mục"}</h2>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mobile-index-name" className="text-sm font-medium">
                  {t("indexName")}
                </Label>
                <Input
                  id="mobile-index-name"
                  value={indexName}
                  onChange={(e) => setIndexName(e.target.value)}
                  className="bg-background/80 backdrop-blur-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <Button variant="outline" size="sm" className="w-full bg-transparent" asChild>
                  <label htmlFor="mobile-file-upload" className="cursor-pointer">
                    <Upload className="mr-2 h-4 w-4" />
                    {t("importPDF")}
                    <input
                      id="mobile-file-upload"
                      type="file"
                      accept=".pdf"
                      multiple
                      className="hidden"
                      onChange={handleFileInput}
                    />
                  </label>
                </Button>
                <Button
                  size="sm"
                  className="w-full bg-gradient-primary hover:opacity-90"
                  onClick={handleBuildIndex}
                  disabled={pdfFiles.length === 0}
                >
                  {isLoadingBuild ? <Spinner className="mr-2 h-4 w-4" /> : <Plus className="mr-2 h-4 w-4" />}
                  {t("buildIndex")}
                </Button>
                <Button variant="outline" size="sm" className="w-full bg-transparent" onClick={handleLoadIndex}>
                  <FolderOpen className="mr-2 h-4 w-4" />
                  {t("loadSavedIndex")}
                </Button>
                <Button 
                variant="outline" 
                size="sm" 
                className="w-full bg-transparent" 
                disabled={pdfFiles.length === 0}
                onClick={handleAddToIndex}>
                  {isLoadingAdd ? <Spinner className="mr-2 h-4 w-4" /> : <Plus className="mr-2 h-4 w-4" />}
                  {t("addToIndex")}
                </Button>
              </div>

              <Button
                variant="destructive"
                size="sm"
                className="w-full"
                onClick={handleClearIndex}
                disabled={pdfFiles.length === 0}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t("clearIndex")}
              </Button>

              <Card
                className={cn(
                  "flex min-h-[200px] flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition-colors",
                  isDragging
                    ? "border-primary bg-primary/5"
                    : "border-border bg-muted/30 hover:border-muted-foreground/50",
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
                <p className="mb-1 text-sm font-medium text-foreground">{t("dragDropArea")}</p>
                <p className="text-xs text-muted-foreground">{t("orClick")}</p>
              </Card>

              {pdfFiles.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Imported PDFs ({pdfFiles.length})</Label>
                  <div className="max-h-[300px] space-y-1 overflow-y-auto rounded-2xl border border-border bg-background/80 p-2 backdrop-blur-sm">
                    {pdfFiles.map((file, index) => (
                      <div key={index} className="flex items-center gap-2 rounded-lg bg-muted/50 p-2 text-xs">
                        <FileText className="h-4 w-4 shrink-0 text-primary" />
                        <span className="flex-1 truncate" title={file.name}>
                          {file.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="thoughts" className="m-0 h-[calc(100%-5rem)] overflow-y-auto p-4">
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-accent" />
                <h2 className="text-lg font-semibold">{t("modelThoughts")}</h2>
              </div>

              <Card className="flex-1 rounded-2xl border-border bg-muted/30 backdrop-blur-sm">
                <ScrollArea className="h-[calc(100vh-16rem)] p-4">
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
            </div>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  )
}
