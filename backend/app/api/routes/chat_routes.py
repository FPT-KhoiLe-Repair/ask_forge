"""
Chat/Query routes - sử dụng ChromaDB để retrieve context cho RAG.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from ask_forge.backend.app.api.dependencies import get_chroma_repo, get_current_index
from ask_forge.backend.app.core.app_state import app_state
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)

# TODO: rewrite the chat, this is just a sample usage of get_context_for_chat
@router.post("/chat")
async def chat(
        query: str,
        index: str,
        repo: ChromaRepo = Depends(get_chroma_repo)  # Inject singleton
):
    # 1. Retrieve contexts
    contexts = repo.get_context_for_chat(index, query)

    # 2. Build prompt
    prompt = f"""
    Context:
    {contexts[0]['text']}
    {contexts[1]['text']}

    Question: {query}
    Answer:
    """

    # 3. Call LLM (từ app_state.loaded_models['llm'])
    llm = app_state.get_model('llm')
    answer = llm.generate(prompt)

    return {"answer": answer, "sources": contexts}

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
