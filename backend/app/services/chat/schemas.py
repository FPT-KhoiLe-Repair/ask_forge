from pydantic import BaseModel, Field
from typing import List, Optional

class ChatBody(BaseModel):
    query_text: str = Field(..., description="Câu hỏi của người dùng")
    index_name: str = Field(..., description="Tên index trong Chroma")
    lang: str = Field(default="vi", description="Ngôn ngữ đầu ra (vi/en)")
    n_results: int = Field(default=3)
    min_rel: float = Field(default=0.5)
    # TODO: Xử lý lang theo origin_language của query

class ContextChunk(BaseModel):
    text: str
    preview: str = ""
    source: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    score: Optional[float] = None

class ChatResponse(BaseModel):
    ok: bool = True
    answer: str
    contexts: List[ContextChunk] = Field(default_factory=list)
    followup_questions: List[str]
    model_name: str
