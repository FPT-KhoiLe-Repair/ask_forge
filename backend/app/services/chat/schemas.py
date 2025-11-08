from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"] = "user"
    question: Optional[str] = None
    answer_text: Optional[str] = None
    model_name: Optional[str] = None
    index_name: Optional[str] = None
    contexts: Optional[List[ContextChunk]] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    meta: dict = Field(default_factory=dict)


class ChatSession(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    # Tóm tắt lũy tiến để "giữ mạch học tập" + giảm bớt số lượng token

    rolling_summary: str = ""
    # cache ngắn hạn: chỉ giữ last_k turn gần nhất để chèn vào prompt
    last_k: int = 6
    chat_turn: List[ChatTurn] = Field(default_factory=list)

    def recent_pairs(self, k: Optional[int] = None) -> List[ChatTurn]:
        k = k or self.last_k
        # Lấy k ChatTurn gần nhất
        return self.chat_turn[-k:]

class ChatBody(BaseModel):
    query_text: str = Field(..., description="Câu hỏi của người dùng")
    index_name: str = Field(..., description="Tên index trong Chroma")
    lang: str = Field(default="vietnamese", description="Ngôn ngữ đầu ra (vietnamese/english)")
    n_results: int = Field(default=75)
    min_rel: float = Field(default=0.2)
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
