import { API_BASE } from "@/lib/config";

// ============================================================
// Types
// ============================================================

export interface ChatContext {
    source: string;
    page: number;
    chunk_id: string;
    score: number;
    preview: string;
}

export interface ChatRequest {
    ok: boolean;
    answer: string;
    contexts: ChatContext[];
    model: string;
    followup_questions?: string[];
}

export interface ChatErrorResponse {
    ok: false;
    error: string;
}

// ============================================================
// SSE Event Types
// ============================================================

export type SSETokenEvent = {
    type: "token";
    content: string;
};

export type SSEContextsEvent = {
    type: "contexts";
    data: ChatContext[];
};

export type SSEFollowupQuestionsEvent = {
    type: "followup_questions";
    questions: string[];
};

export type SSEQGJobEvent = {
    type: "qg_job";
    job_id: string;
    poll_url: string;
};

export type SSEErrorEvent = {
    type: "error";
    content: string;
};

export type SSEEvent = SSETokenEvent | SSEContextsEvent | SSEFollowupQuestionsEvent | SSEQGJobEvent | SSEErrorEvent;

// ============================================================
// Non-streaming chat API
// ============================================================

export async function chatAPI(
    query: string,
    indexName: string,
): Promise<ChatRequest> {
    const url = new URL(`${API_BASE}/api/chat`);
    const response = await fetch(url.toString(), {
        method: "POST",
        headers: {"Content-Type": "application/json",},
        body: JSON.stringify({ query_text: query, index_name: indexName }),
    });

    if (!response.ok) {
        const errorData: ChatErrorResponse = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
}

// ============================================================
// Streaming chat API với SSE parsing
// ============================================================

export interface StreamCallbacks {
    onToken?: (token: string) => void;
    onContexts?: (contexts: ChatContext[]) => void;
    onQGJob?: (jobId: string, pollUrl: string) => void;
    onFollowupQuestions?(questions: string[]): void; // <— thêm dòng này
    onComplete?: () => void;
    onError?: (error: Error) => void;
}

export async function chatStreamAPI(
    query: string,
    indexName: string,
    callbacks: StreamCallbacks
): Promise<void> {
    const url = new URL(`${API_BASE}/api/chat/stream`);

    try {
        const response = await fetch(url.toString(), {
            method: "POST",
            headers: {"Content-Type": "application/json",},
            body: JSON.stringify({ query_text: query, index_name: indexName }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error("Response body is not readable");
        }

        const decoder = new TextDecoder("utf-8");
        
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                callbacks.onComplete?.();
                break;
            }

            // Decode chunk và thêm vào buffer
            buffer += decoder.decode(value, { stream: true });

            // Parse SSE events (format: "data: {json}\n\n")
            const events = buffer.split("\n\n");
            
            // Giữ lại phần chưa đủ 1 event
            buffer = events.pop() || "";

            for (const eventStr of events) {
                if (!eventStr.trim()) continue;

                // Parse "data: {json}"
                const match = eventStr.match(/^data:\s*(.+)$/);
                if (!match) continue;

                const dataStr = match[1];
                
                // Check for [DONE] signal
                if (dataStr === "[DONE]") {
                    callbacks.onComplete?.();
                    return;
                }

                try {
                    const event: SSEEvent = JSON.parse(dataStr);

                    switch (event.type) {
                        case "token":
                            callbacks.onToken?.(event.content);
                            break;
                        case "contexts":
                            callbacks.onContexts?.(event.data);
                            break;
                        case "qg_job":
                            callbacks.onQGJob?.(event.job_id, event.poll_url);
                            break;
                        case "error":
                            callbacks.onError?.(new Error(event.content));
                            return;
                    }
                } catch (parseError) {
                    console.error("Failed to parse SSE event:", dataStr, parseError);
                }
            }
        }
    } catch (error) {
        callbacks.onError?.(error as Error);
    }
}