from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatBody(BaseModel):
    index_name: Optional[str] = None
    query_text: str

    # Retrieval options
    top_k: int = Field(3, ge=1, le=10)
    min_relevance: float = Field(0.5, ge=0, le=1)

    # Query Generation (follow-ups)
    generate_queries: bool = False
    num_queries: int = Field(5, ge=1, le=10)
    query_use_context: bool = True
    query_language: Optional[str] = ["en", "vn"]

class ChatResponse(BaseModel):
    ok: bool
    answer: str
    model: str
    contexts: List[Dict[str, Any]]
    followup_queries: Optional[List[Dict[str, Any]]] = None
    debug: Optional[Dict[str, Any]] = None
