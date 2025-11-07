import { API_BASE } from "@/lib/config"

// ============================================================
// Types
// ============================================================

export interface ChatContext {
  source: string
  page: number
  chunk_id: string
  score: number
  preview: string
}

export interface ChatRequest {
  ok: boolean
  answer: string
  contexts: ChatContext[]
  model: string
  followup_questions?: string[]
}

export interface ChatErrorResponse {
  ok: false
  error: string
}

// ============================================================
// SSE Event Types
// ============================================================

export type SSETokenEvent = {
  type: "token"
  content: string
}

export type SSEContextsEvent = {
  type: "contexts"
  data: ChatContext[]
}

export type SSEQGJobEvent = {
  type: "qg_job"
  job_id: string
  poll_url: string
}

export type SSEErrorEvent = {
  type: "error"
  content: string
}

export type SSEEvent = SSETokenEvent | SSEContextsEvent | SSEQGJobEvent | SSEErrorEvent

// ============================================================
// Streaming chat API với SSE parsing
// ============================================================

export interface StreamCallbacks {
  onToken?: (token: string) => void
  onContexts?: (contexts: ChatContext[]) => void
  onQGJob?: (jobId: string, pollUrl: string) => void
  onComplete?: () => void
  onError?: (error: Error) => void
  setFollowupQuestions?: (questions: string[]) => void
}

export async function chatStreamAPI(query: string, indexName: string, callbacks: StreamCallbacks): Promise<void> {
  const url = new URL(`${API_BASE}/api/chat/stream`)

  console.log("🚀 Starting stream request to:", url.toString())

  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_text: query, index_name: indexName }),
    })

    console.log("📡 Response status:", response.status)
    console.log("📡 Response headers:", Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error("Response body is not readable")
    }

    const decoder = new TextDecoder("utf-8")
    let buffer = ""
    let eventCount = 0

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        console.log("✅ Stream completed (done=true)")
        callbacks.onComplete?.()
        break
      }

      // Decode chunk và thêm vào buffer
      const chunk = decoder.decode(value, { stream: true })
      console.log("📦 Raw chunk received:", chunk.substring(0, 200) + "...")
      buffer += chunk

      // Parse SSE events (format: "data: {json}\n\n")
      const events = buffer.split("\n\n")

      // Giữ lại phần chưa đủ 1 event
      buffer = events.pop() || ""

      for (const eventStr of events) {
        if (!eventStr.trim()) continue

        eventCount++
        console.log(`\n🎯 Event #${eventCount}:`, eventStr.substring(0, 150) + "...")

        // Parse "data: {json}"
        const match = eventStr.match(/^data:\s*(.+)$/m)
        if (!match) {
          console.warn("⚠️ No 'data:' prefix found:", eventStr)
          continue
        }

        const dataStr = match[1]

        // Check for [DONE] signal
        if (dataStr === "[DONE]") {
          console.log("🏁 Received [DONE] signal")
          callbacks.onComplete?.()
          return
        }

        try {
          const event: SSEEvent = JSON.parse(dataStr)
          console.log("✨ Parsed event type:", event.type)

          switch (event.type) {
            case "token":
              console.log("📝 Token:", event.content.substring(0, 50))
              callbacks.onToken?.(event.content)
              break
            case "contexts":
              console.log("📚 Contexts count:", event.data?.length)
              callbacks.onContexts?.(event.data)
              break
            case "qg_job":
              console.log("🔄 QG Job:", event.job_id)
              callbacks.onQGJob?.(event.job_id, event.poll_url)
              const pollQG = async (pollUrl: string, tries = 0) => {
                try {
                  const url = new URL(pollUrl, API_BASE).toString()
                  console.log(`🔄 Polling QG at (attempt ${tries + 1}):`, url)
                  const res = await fetch(url)

                  if (!res.ok) {
                    console.warn("⚠️ QG poll failed:", res.status)
                    return
                  }

                  const data = await res.json()
                  console.log("📊 QG poll response:", data)

                  if (data?.status === "completed" && Array.isArray(data?.questions)) {
                    console.log("✅ QG complete, questions:", data.questions)
                    callbacks.setFollowupQuestions?.(data.questions)
                    return
                  }

                  if (data?.status === "pending") {
                    console.log("⏳ QG pending, retrying in 1.5s...")
                    setTimeout(() => pollQG(pollUrl, tries + 1), 1500)
                    return
                  }

                  if (data?.status === "error") {
                    console.error("❌ QG error from backend:", data.error)
                    return
                  }
                } catch (e) {
                  console.warn("❌ QG polling error:", e)
                }
              }
              pollQG(event.poll_url)
              break
            case "error":
              console.error("❌ Error event:", event.content)
              callbacks.onError?.(new Error(event.content))
              return
          }
        } catch (parseError) {
          console.error("💥 Failed to parse SSE event:", dataStr, parseError)
        }
      }
    }
  } catch (error) {
    console.error("🔥 Stream error:", error)
    callbacks.onError?.(error as Error)
  }
}
