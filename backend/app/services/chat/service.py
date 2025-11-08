from __future__ import annotations

import asyncio
import json
from typing import List, Dict

from ask_forge.backend.app.core.app_state import AppState
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.services.chat.schemas import ChatBody
from ask_forge.backend.app.services.chat.pipeline import (
    prepare_contexts_for_response,
    build_history_context,
    build_system_memory_block, build_chat_prompt_from_template, stream_answer_llm,
)
# from ask_forge.backend.app.services.queue.redis_queue import BackgroundQueueUsingRedis
from ask_forge.backend.app.services.chat_history.summary import generate_session_summary

from fastapi.responses import StreamingResponse
import logging
logger = logging.getLogger(__name__)

def _sse(payload: dict | str, event: str | None = None) -> str:
    """SSE format: data: {json}\n\n"""
    if isinstance(payload, dict):
        data = json.dumps(payload, ensure_ascii=False)
    else:
        data = payload

    if event:
        return f"event: {event}\ndata: {data}\n\n"
    return f"data: {data}\n\n"

class ChatService:
    def __init__(self,app_state : AppState, repo: ChromaRepo):
        self.repo = repo
        self.app_state = app_state
        self.question_generator_service = app_state.llm_registry.get("question_generator_service") # llm_registered ở app_state
        self.chat_history = app_state.history_repo

    def _retrieve(self, *, index_name: str, query_text: str, n_results: int = 3, min_rel: float = 0.5) -> List[Dict]:
        return self.repo.get_context_for_chat(
            index_name=index_name,
            query_text=query_text,
            n_results=n_results,
            min_relevance=min_rel,
        )

    async def chat_stream_sse(self, body: ChatBody):
        """Generator trả SSE chunks theo chuẩn"""
        async def event_gen():
            try:
                # ===== 1. Retrieve contexts (non-blocking) =====
                contexts = await asyncio.to_thread(
                    self._retrieve,
                    index_name=body.index_name,
                    query_text=body.query_text,
                    n_results=body.n_results,
                    min_rel=body.min_rel,
                )


                logger.info(f"📚 Retrieved {len(contexts)} contexts for streaming")
                # Optional ping connection

                # yield _sse({
                #     "type": "ping",
                #     "content": "start"
                # })

                # ===== 2. Build prompt =====
                prompt = build_chat_prompt_from_template(
                    question=body.query_text,
                    contexts=contexts,
                    lang=body.lang
                )

                # ===== 3. Stream answer tokens =====
                async for chunk in stream_answer_llm(
                        prompt=prompt,
                        app_state=self.app_state,
                        task="chat"
                ):
                    if chunk:  # Skip empty chunks
                        yield _sse({
                            "type": "token",
                            "content": chunk,
                        })

                # ===== 4. Send contexts (after answer complete) =====
                yield _sse({
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
                    job_id = await self.app_state.bq.enqueue_qg(
                        seed_question=body.query_text,
                        contexts=contexts,
                        lang=body.lang,
                        session_id=getattr(body, "session_id", "default"),
                        app_state=self.app_state,
                    )
                    logger.info(job_id)
                    # Yield for client to know where the job located (job_id), then the client need to call an API with the job_id
                    # to get the question generate result
                    yield _sse({
                        "type": "qg_job",
                        "job_id": job_id,
                        "poll_url": f"/api/chat/qg/{job_id}"
                    })
                except Exception as e:
                    logger.warning(f"QG job enqueue failed: {e}")
                    # Không crash stream nếu QG fail

            except Exception as e:
                logger.exception("Streaming error")
                yield _sse({
                    "type": "error",
                    "content": str(e)
                })
            finally:
                yield _sse("[DONE]")

        # ==== HTTP response (bắt buộc cho SSE) ====
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no", # tránh Nginx/nginx-ingress buffer
        }
        return StreamingResponse(event_gen(), media_type="text/event-stream", headers=headers)
        # StreamingResponse Receive AsyncIterable object to return streaming response.

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