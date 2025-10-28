from __future__ import annotations
from typing import List, Dict, Tuple
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.features.chat.schemas import ChatBody, ChatResponse, ContextChunk
from ask_forge.backend.app.features.chat.pipeline import (
    generate_answer_nonstream,
    generate_answer_stream,
    prepare_contexts_for_response
)

class ChatService:
    def __init__(self, repo: ChromaRepo):
        self.repo = repo

    def _retrieve(self, *, index_name: str, query_text: str, n_results: int = 3, min_rel: float = 0.5) -> List[Dict]:
        return self.repo.get_context_for_chat(
            index_name=index_name,
            query_text=query_text,
            n_results=n_results,
            min_relevance=min_rel,
        )

    async def chat_once(self, body: ChatBody):
        contexts = self._retrieve(
            index_name=body.index_name,
            query_text=body.query_text,
            n_results=body.n_results,
            min_rel=body.min_rel,
        )
        answer, model_name = generate_answer_nonstream(
            question=body.query_text,
            contexts=contexts,
            lang=body.lang,
        )
        return ChatResponse(
            ok=True,
            answer=answer or "Xin lỗi, mình chưa tìm được câu trả lời phù hợp từ context hiện có.",
            contexts=[ContextChunk(**c,
                                   preview=c.get("text", "")[:240])
                      for c in prepare_contexts_for_response(contexts)],
            model_name=model_name,
        )

    def chat_stream(self, body: ChatBody):
        contexts = self._retrieve(
            index_name=body.index_name,
            query_text=body.query_text,
            n_results=body.n_results,
            min_rel=body.min_rel,
        )
        return generate_answer_stream(
            question=body.query_text,
            contexts=contexts,
            lang=body.lang,
        )

chat_service = ChatService(ChromaRepo())