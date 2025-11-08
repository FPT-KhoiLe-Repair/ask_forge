from __future__ import annotations
from typing import List, Dict, Iterable, Tuple, AsyncIterable, AsyncIterator, Any, Coroutine

from ask_forge.backend.app.core.app_state import AppState
from ask_forge.backend.app.services.chat.schemas import ChatTurn, ContextChunk
import logging
logger = logging.getLogger(__name__)

def build_history_context(chat_turns: List[ChatTurn]) -> str:
    """
    Đưa last_k lượt chat thành 1 block, gọn và có cấu trúc
    """
    lines = []
    for t in chat_turns:
        if t.role == "user" and t.question:
            lines.append(f"<q>{t.question}</q>")
        elif t.role == "assistant" and t.answer_text:
            lines.append(f"<a>{t.answer_text}</a>")
    return "\n".join(lines)

def build_system_memory_block(rolling_summary: str) -> str:
    if not rolling_summary:
        return ""
    return f"<learning_summary>{rolling_summary}\n</learning_summary>"


def _render_prompt(template: str, *,
                   question:str,
                   contexts: Iterable[Dict],
                   lang: str,
                   history_block: str = "",
                   summary_block: str = "") -> str:
    joined_ctx = "\n---\n".join(
        f"[score={c.get('score', 0)}] {c.get('text', '')}\n(source={c.get('source', '')}, page={c.get('page', '')})"
        for c in contexts
    )

    return (
        template.replace("{{LANG}}", lang)
                .replace("{{QUESTION}}", question)
                .replace("{{CONTEXT}}", joined_ctx)
                .replace("{{HISTORY_BLOCK}}", history_block)
                .replace("{{SUMMARY_BLOCK}}", summary_block)
    )

def _normalize_contexts(contexts: List[Dict]) -> List[Dict]:
    # Đảm bảo các key có tồn tại để serialize ra response
    normalized_contexts = []
    for c in contexts:
        normalized_contexts.append({
            "text": c.get("text", ""),
            "source": c.get("source"),
            "page": c.get("page"),
            "chunk_id": c.get("chunk_id"),
            "score": c.get("score"),
        })
    return normalized_contexts

async def answer_once_gemini(*, prompt: str, app_state: AppState) -> Tuple[str, str]:
    gemini_service = app_state.llm_registry.get("gemini_service")
    model_name = gemini_service.model_name

    text: str = await gemini_service.generate(prompt=prompt)  # await → str
    # logger.debug("resp type=%s len=%d", type(text).__name__, len(text))  # optional

    return (text or "").strip(), model_name

def build_chat_prompt_from_template(*, question: str, contexts: List[Dict], lang: str, history_block: str = "", summary_block: str = "") -> str:
    # Đọc template từ file (đọc mỗi lần cho đơn giản; nếu muốn có thể cache)
    from pathlib import Path
    TPL = Path(__file__).resolve().parent / "prompts" / "chat_prompt.txt"
    template = TPL.read_text(encoding="utf-8")
    return _render_prompt(template, question=question, contexts=contexts, lang=lang, history_block=history_block, summary_block=summary_block)

async def stream_answer_llm(
    *,
    prompt: str,
    app_state: AppState,
    task: str = "chat",
    **context
) -> AsyncIterator[str]:
    """Streaming qua Router"""

    provider = await app_state.llm_router.route({
        "task": task,
        **context
    }) # M có thể vào trong route để kiểm `tra và xem các thông số đầu vào có thể nhận, ở đây ta nhận task

    async for chunk in provider.generate_stream(prompt):
        yield chunk

def prepare_contexts_for_response(contexts: List[Dict]) -> List[Dict]:
    return _normalize_contexts(contexts)
