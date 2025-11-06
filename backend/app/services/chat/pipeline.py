from __future__ import annotations
from typing import List, Dict, Iterable, Tuple, AsyncIterable, AsyncIterator

from ask_forge.backend.app.core.app_state import AppState
from ask_forge.backend.app.services.chat.schemas import ChatTurn, ContextChunk

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

def answer_once_gemini(*, prompt: str, app_state:AppState) -> Tuple[str, str]:
    """
    Trả (answer_text, model_name) bằng Gemini. Dùng AppState để lấy client/model.
    """
    client = app_state.ensure_gemini_client()
    model_name = app_state.get_gemini_model_name()
    response = client.models.generate_content(model=model_name, contents=prompt)
    text = getattr(response, "text", "") or "" # Text is answer_text
    return text.strip(), model_name

def stream_answer_gemini(*, prompt:str, app_state:AppState) -> Iterable[str]:
    """
    Generator stream text dần dần (chunked plain text)
    """
    client = app_state.ensure_gemini_client()
    model_name = app_state.get_gemini_model_name()
    stream = client.models.generate_content_stream(model=model_name, contents=prompt)
    for event in stream:
        # google.genai trả nhiều loại sự kiện; text thường nằm ở event.text
        chunk = getattr(event, "text", None)
        if chunk:
            yield chunk

    # Kết thúc
    yield ""

def build_chat_prompt_from_template(*, question: str, contexts: List[Dict], lang: str, history_block: str = "", summary_block: str = "") -> str:
    # Đọc template từ file (đọc mỗi lần cho đơn giản; nếu muốn có thể cache)
    from pathlib import Path
    TPL = Path(__file__).resolve().parent / "prompts" / "chat_prompt.txt"
    template = TPL.read_text(encoding="utf-8")
    return _render_prompt(template, question=question, contexts=contexts, lang=lang, history_block=history_block, summary_block=summary_block)

def generate_answer_non_stream(*,
                               question: str,
                               contexts: List[Dict],
                               lang: str,
                               app_state: AppState,
                               history_block: str = "",
                               summary_block: str = "",
                               ) -> Tuple[str, str]:
    prompt = build_chat_prompt_from_template(
        question=question,
        contexts=contexts,
        lang=lang,
        history_block=history_block,
        summary_block=summary_block
    )
    return answer_once_gemini(prompt=prompt,app_state=app_state)

async def answer_once_llm(
    *,
    prompt: str,
    app_state: AppState,
    task: str = "chat",
    **context
) -> Tuple[str, str]:
    """Dùng Router chọn LLM provider"""
    provider = await app_state.llm_router.route({
        "task": task,
        **context
    })
    text = await provider.generate(prompt)
    return text.strip(), provider.model_name

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
    })
    async for chunk in provider.generate_stream(prompt):
        yield chunk

def generate_answer_stream(*, question: str, contexts: List[Dict], lang: str, app_state: AppState) -> Iterable[str]:
    prompt = build_chat_prompt_from_template(
        question=question,
        contexts=contexts,
        lang=lang,
    )
    return stream_answer_gemini(prompt=prompt, app_state=app_state)

def prepare_contexts_for_response(contexts: List[Dict]) -> List[Dict]:
    return _normalize_contexts(contexts)

