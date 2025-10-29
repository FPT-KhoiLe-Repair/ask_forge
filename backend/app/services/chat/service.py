from __future__ import annotations
from typing import List, Dict

from ask_forge.backend.app.core.app_state import logger, AppState
from ask_forge.backend.app.services.qg.service import QGService
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.services.chat.schemas import ChatBody, ChatResponse, ContextChunk
from ask_forge.backend.app.services.chat.pipeline import (
    generate_answer_nonstream,
    generate_answer_stream,
    prepare_contexts_for_response
)


class ChatService:
    def __init__(self,app_state:AppState, repo: ChromaRepo):
        self.repo = repo
        self.app_state = app_state
        self.qg_service = QGService()

    def _retrieve(self, *, index_name: str, query_text: str, n_results: int = 3, min_rel: float = 0.5) -> List[Dict]:
        return self.repo.get_context_for_chat(
            index_name=index_name,
            query_text=query_text,
            n_results=n_results,
            min_relevance=min_rel,
        )

    async def chat_with_followup(self, body: ChatBody):
        """
        Chat system logic: retrieve, answer, generate follow-ups.
        """

        logger.info(f"🗣️ Chat request: {body.query_text} | index={body.index_name}")

        # ---- Step 1: Retrieve Context ----
        contexts = self._retrieve(
            index_name=body.index_name,
            query_text=body.query_text,
            n_results=body.n_results,
            min_rel=body.min_rel,
        )
        logger.info(f"📚 Retrieved {len(contexts)} context chunks")

        # ---- Step 2: Build prompts ----
        try:
            answer_text, model_name = generate_answer_nonstream(
                question=body.query_text,
                contexts=contexts,
                lang=body.lang,
                app_state=self.app_state,
            )
        except Exception as e:
            logger.exception(e)
            answer_text = f"Xin lỗi, có lỗi khi truy vẫn mô hình:{e}"
            model_name = ""

        # ---- Step 4: Generate follow-up questions ----
        try:
            followup_questions = await self.qg_service.generate_questions(
                seed_question=body.query_text,
                contexts=contexts,
                lang=body.lang
            )
        except Exception as e:
            logger.exception(e)
            followup_questions = []

        # ---- Step 5: Merge Response ---
        contexts_serialized = [
            ContextChunk(
                source=c.get("source"),
                page=c.get("page"),
                chunk_id=c.get("chunk_id"),
                preview=c.get("text", "")[:240],
                text=c.get("text",""),
                score=c.get("score"),
            )
            for c in contexts
        ]
        results = ChatResponse(
            ok=True,
            answer=answer_text or "Xin lỗi, mình chưa tìm được câu trả lời phù hợp từ context hiện có.",
            contexts=contexts_serialized,
            followup_questions=followup_questions,
            model_name=model_name,
        )
        logger.info(f"✅ Chat complete | model={model_name} | followups={len(followup_questions)}")
        return results


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
            app_state=self.app_state,
        )
        return ChatResponse(
            ok=True,
            answer=answer or "Xin lỗi, mình chưa tìm được câu trả lời phù hợp từ context hiện có.",
            contexts=[ContextChunk(**c,
                                   preview=c.get("text", "")[:240])
                      for c in prepare_contexts_for_response(contexts)],
            followup_questions=[],
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
            app_state=self.app_state,
        )