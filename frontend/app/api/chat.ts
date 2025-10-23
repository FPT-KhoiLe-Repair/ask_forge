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
}

export interface ChatErrorResponse {
    ok: false;
    error: string;
}
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
// Streaming chat API
// ============================================================

export async function chatStreamAPI(
    query: string,
    indexName: string,
    onChunk: (chunk: string) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void,
): Promise<void> {
    const url = new URL(`${API_BASE}/api/chat/stream`);

    try {
        const response = await fetch(url.toString(), {
            method: "POST",
        headers: {"Content-Type": "application/json",},
        body: JSON.stringify({ query_text: query, index_name: indexName }),
    });

    if (!response.ok) {throw new Error(`HTTP ${response.status}: ${response.statusText}`);}

    const reader = response.body?.getReader();
    if (!reader) {throw new Error("Response body is not readable");}

    const decoder = new TextDecoder("utf-8");

    while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
            onComplete?.();
            break;
        }

        const chunk = decoder.decode(value, { stream: true });
        onChunk(chunk);
        }
    } catch (error) {
        onError?.(error as Error);
    }
}