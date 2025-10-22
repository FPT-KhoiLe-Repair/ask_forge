"""
Chat/Query routes - sử dụng ChromaDB để retrieve context cho RAG.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional

from pydantic import BaseModel, Field

from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.api.dependencies import get_chroma_repo

from ask_forge.backend.app.services.llm.gemini_client import (
    get_gemini_client, get_gemini_model_name
)
from ask_forge.backend.app.services.rag_service import (
    build_chat_prompt, answer_once_gemini, stream_answer_gemini
)

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)

# TODO: rewrite the chat, this is just a sample usage of get_context_for_chat
@router.post("/chat")
async def chat(
        query_text: str = Query(..., description="Câu hỏi của người dùng"),
        index_name: str = Query(..., description="Tên index Chroma"),
        repo: ChromaRepo = Depends(get_chroma_repo)  # Inject singleton
):

    try:
        contexts = repo.get_context_for_chat(
            index_name=index_name,
            query_text=query_text,
            n_results=3,
            min_relevance=0.7
        )

        # Contexts rỗng
        if not contexts:
            msg = ("Không tìm thấy đonạ context liên quan. "
                   "Hãy thử câu hỏi khác hoặc nạp thêm tài liệu cho index này")
            return JSONResponse(status_code=400, content={"ok": False, "error": msg})

        # 2. Build prompt (giới hạn 3 chunk tốt nhất)
        prompt = build_chat_prompt(query_text=query_text, contexts=contexts)

        # 3. Call Gemini (non-stream)
        client = get_gemini_client()
        model_name = get_gemini_model_name()
        answer_text = answer_once_gemini(client=client, model=model_name, prompt=prompt) or \
            "Xin lỗi, mình chưa thể tạo câu trả lời phù hợp từ context hiện có."

        # 4. Return
        return {
            "ok": True,
            "answer": answer_text,
            "contexts": [
                {
                    "source": c.get("source"),
                    "page": c.get("page"),
                    "chunk_id": c.get("chunk_id"),
                    "score": c.get("score"),
                    "preview": c.get("text", "")[:240]
                } for c in contexts
            ],
            "model": model_name
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False,
                     "error": str(e)}
        )
@router.post("/chat/stream")
async def chat_stream(
        query_text:str,
        index_name: str,
        repo: ChromaRepo = Depends(get_chroma_repo),
):
    """Endpoint streaming (có thể bật sau). Frontend sẽ nhận text dần dần."""
    # Lấy context & prompt như non-stream
    contexts = repo.get_context_for_chat(
        index_name=index_name,
        query_text=query_text,
        n_results=3,
        min_relevance=0.7
    )
    prompt = build_chat_prompt(query_text=query_text, contexts=contexts)
    client = get_gemini_client()
    model_name = get_gemini_model_name()
    stream_gen = stream_answer_gemini(client=client, model=model_name, prompt=prompt)
    return StreamingResponse(stream_gen, media_type="text/plain")

# ============================================================
# Request/Response Models
# ============================================================

class QueryRequest(BaseModel):
    """Request model cho query/search."""
    query: str = Field(..., description="User query text")
    n_results: int = Field(default=5, ge=1, le=20, description="Number of results",)
    min_relevance: float = Field(default=0.5, ge=0, le=1, description="Minimum relevance source")
    filter_source: Optional[str] = Field(default=None, description="Filter by source file")


class ContextChunk(BaseModel):
    """Model cho một context chunk."""
    text: str
    source: str
    page: int
    chunk_id: str
    score: float


class QueryResponse(BaseModel):
    """Response model cho query."""
    ok: bool
    query: str
    index_name: str
    contexts: List[ContextChunk]
