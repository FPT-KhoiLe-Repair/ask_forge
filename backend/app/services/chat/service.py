from __future__ import annotations

import asyncio
import json
from typing import List, Dict

from ask_forge.backend.app.core.app_state import AppState
from ask_forge.backend.app.services.qg.service import QGService
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.services.chat.schemas import ChatBody, ChatResponse, ContextChunk, ChatTurn
from ask_forge.backend.app.services.chat.pipeline import (
    generate_answer_non_stream,
    generate_answer_stream,
    prepare_contexts_for_response,
    build_history_context,
    build_system_memory_block, build_chat_prompt_from_template, stream_answer_llm
)
from ask_forge.backend.app.services.queue.redis_queue import BackgroundQueue
from ask_forge.backend.app.services.chat_history.summary import generate_session_summary

import hashlib
import secrets

import logging
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self,app_state : AppState, repo: ChromaRepo):
        self.repo = repo
        self.app_state = app_state
        self.question_generator_service = app_state.llm_registry.get("question_generator_service") # llm_registered ở app_state
        self.chat_history = app_state.history_repo
        self.bq_queue = BackgroundQueue()

    def _retrieve(self, *, index_name: str, query_text: str, n_results: int = 3, min_rel: float = 0.5) -> List[Dict]:
        return self.repo.get_context_for_chat(
            index_name=index_name,
            query_text=query_text,
            n_results=n_results,
            min_relevance=min_rel,
        )

    async def chat_stream_sse(self, body: ChatBody):
        """Generator trả SSE chunks"""

        # ===== 1. Retrieve contexts (non-blocking) =====
        contexts = await asyncio.to_thread(
            self._retrieve,
            index_name=body.index_name,
            query_text=body.query_text,
            n_results=body.n_results,
            min_rel=body.min_rel,
        )

        logger.info(f"📚 Retrieved {len(contexts)} contexts for streaming")

        # ===== 2. Build prompt =====
        prompt = build_chat_prompt_from_template(
            question=body.query_text,
            contexts=contexts,
            lang=body.lang
        )

        # ===== 3. Stream answer tokens =====
        try:
            async for chunk in stream_answer_llm(
                    prompt=prompt,
                    app_state=self.app_state,
                    task="chat"
            ):
                if chunk:  # Skip empty chunks
                    yield json.dumps({
                        "type": "token",
                        "content": chunk
                    })
        except Exception as e:
            logger.exception("Streaming error")
            yield json.dumps({
                "type": "error",
                "content": str(e)
            })
            return

        # ===== 4. Send contexts (after answer complete) =====
        yield json.dumps({
            "type": "contexts",
            "data": [
                {
                    "source": c.get("source"),
                    "page": c.get("page"),
                    "preview": c.get("text", "")[:200],
                    "score": c.get("score")
                }
                for c in contexts
            ]
        })

        # ===== 5. Trigger QG background job =====
        try:
            job_id = await self.bq_queue.enqueue_qg(
                seed_question=body.query_text,
                contexts=contexts,
                lang=body.lang,
                session_id=getattr(body, "session_id", "default"),
            )

            yield json.dumps({
                "type": "qg_job",
                "job_id": job_id,
                "poll_url": f"/api/chat/qg/{job_id}"
            })
        except Exception as e:
            logger.warning(f"QG job enqueue failed: {e}")
            # Không crash stream nếu QG fail

    async def chat_with_followup_pipeline(self, body: ChatBody):
        """
        Chat system logic: retrieve, answer, generate follow-ups.
        """
        # Generate a random salt
        salt = secrets.token_bytes(16)

        # Data to be hashed (can be anything)
        data = b"my secret message"

        # Combine data and salt, then hash
        hashed_data = hashlib.sha256(salt + data).hexdigest()

        session_id = getattr(body, "session_id", hashed_data) #TODO: trong tương lai có thể dùng chat_session_id để lưu nhiều chat_session
        user_id = getattr(body, "user_id", hashed_data) #TODO: tương tự, cái này để dành cho tương lai, còn cái này dùng các default option cho dễ

        current_session = self.chat_history.get_or_create(session_id=session_id, user_id=user_id)


        logger.info(f"🗣️ Chat request: {body.query_text} | index={body.index_name}")

        # ---- Step 0: Build memory blocks ----
        history_block = build_history_context(current_session.recent_pairs(current_session.last_k))
        summary_block = build_system_memory_block(current_session.rolling_summary)

        # ---- Step 1: Retrieve Context ----
        contexts = self._retrieve(
            index_name=body.index_name,
            query_text=body.query_text,
            n_results=body.n_results,
            min_rel=body.min_rel,
        )
        logger.info(f"📚 Retrieved {len(contexts)} context chunks")

        # ---- Step 2: Build prompts & Generate Answer ----
        try:
            # TODO: Important! Không dùng chat/pipline nữa mà tích hợp thẳng sử dụng LLMProvider, lấy GeminiAdapter luôn, hoặc nếu cần gọi vào pipeline thì phải gọi LLMProvider trong pipeline.
            answer_text, model_name = await generate_answer_non_stream(
                question=body.query_text,
                contexts=contexts,
                lang=body.lang,
                app_state=self.app_state,
                history_block=history_block,
                summary_block=summary_block
            )
        except Exception as e:
            logger.exception(e)
            answer_text = f"Xin lỗi, có lỗi khi truy vẫn mô hình:{e}"
            model_name = ""

        # ---- Step 3: Generate follow-up questions ----
        if self.question_generator_service: # Xem generate ở question_generator.py
            followup_questions = await self.question_generator_service.generate(
                prompt=body.query_text,
                contexts=contexts,
                n=5,
                lang=body.lang,
                history_block=history_block,
                summary_block=summary_block
            )
            seed_question = body.query_text  # Keep original question
        else:
            followup_questions = []
            seed_question = body.query_text

        # ---- Step 4: Append USER turn to history (question) ----
        self.chat_history.append(
            session_id=session_id,
            chat_turn=ChatTurn(
                role="user",
                question=seed_question,
                index_name=body.index_name,
                contexts=None
        ))

        # ---- Step 5: Append ASSISTANT turn (answer) ----
        self.chat_history.append(
            session_id=session_id,
            chat_turn=ChatTurn(
                role="assistant",
                answer_text=answer_text,
                model_name=model_name,
                index_name=body.index_name,
                contexts=[ContextChunk(
                    source=c.get("source"),
                    page=c.get("page"),
                    chunk_id=c.get("chunk_id"),
                    preview=c.get("text","")[:240],
                    text=c.get("text",""),
                    score=c.get("score"),
                ) for c in contexts],
            )
        )

        # ---- (Optional) Update rolling summary mỗi N lượt ----
        try:
            if len(current_session.chat_turn) % 6 ==0:
                # Tạo prompt tóm tắt lũy tiến từ history gần đây + summary cũ
                new_summary = await self._summarize_learning_flow(current_session)
                if new_summary:
                    self.chat_history.set_summary(
                        session_id=session_id,
                        new_summary=new_summary
                    )
        except Exception as e:
            logger.exception(f"Rolling summary update failed: {e}")

        # ---- Step 6: Merge Response ---
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

    async def _summarize_learning_flow(self, sess) -> str:
        """
        Gọi LLM tạo tóm tắt lũy tiến:
        - Mục tiêu của Học Sinh đang theo đuổi là gì
        - Các khái niệm đã cover
        - Lỗ hổng/hiểu sai
        - Gợi ý bước kế tiếp
        """
        # TODO: Tôi muốn sau này ta sẽ đi sâu vào flow summarize, phần summarize này sẽ phản ánh kiến thức hiện tại của học sinh. Summarize có thể là review lại chất lượng đặt câu hỏi của người dùng để xem xét gợi ý cho người dùng những cái cần thiết.
        # Lấy một đoạn nhỏ lịch sử + summary cũ
        history_block = build_history_context(sess.recent_pairs(sess.last_k + 3))
        # Bạn có thể dùng cùng `generate_answer_non_stream` với 0 contexts, hoặc tách ra hàm call LLM đơn giản
        try:
            summary_text, _ = generate_session_summary(app_state=self.app_state, history_block=history_block)
            return summary_text.strip()
        except Exception as e:
            return ""

    async def chat_once(self, body: ChatBody):
        contexts = self._retrieve(
            index_name=body.index_name,
            query_text=body.query_text,
            n_results=body.n_results,
            min_rel=body.min_rel,
        )
        answer_text, model_name = generate_answer_non_stream(
            question=body.query_text,
            contexts=contexts,
            lang=body.lang,
            app_state=self.app_state,
        )
        return ChatResponse(
            ok=True,
            answer=answer_text or "Xin lỗi, mình chưa tìm được câu trả lời phù hợp từ context hiện có.",
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