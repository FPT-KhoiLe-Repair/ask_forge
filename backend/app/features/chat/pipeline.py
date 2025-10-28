from __future__ import annotations
from typing import List, Dict, Iterable, Tuple
from ask_forge.backend.app.core.app_state import app_state

def _render_prompt(template: str, *, question:str, contexts: Iterable[Dict], lang: str) -> str:
    joined_ctx = "\n---\n".join(
        f"[score={c.get('score', 0)}] {c.get('text', '')}\n(source={c.get('source', '')}, page={c.get('page', '')})"
        for c in contexts
    )

    return (
        template.replace("{{LANG}}", lang)
                .replace("{{QUESTION}}", question)
                .replace("{{CONTEXT}}", joined_ctx)
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

def answer_once_gemini(*, prompt: str) -> Tuple[str, str]:
    """
    Trả (answer_text, model_name) bằng Gemini. Dùng AppState để lấy client/model.
    """
    client = app_state.ensure_gemini_client()
    model_name = app_state.get_gemini_model_name()
    response = client.models.generate_content(model=model_name, contents=prompt)
    text = getattr(response, "text", "") or ""
    return text.strip(), model_name

def stream_answer_gemini(*, prompt:str):
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

def build_prompt_from_template(*, question: str, contexts: List[Dict], lang: str) -> str:
    # Đọc template từ file (đọc mỗi lần cho đơn giản; nếu muốn có thể cache)
    from pathlib import Path
    TPL = Path(__file__).resolve().parent / "prompts" / "chat_prompt.txt"
    template = TPL.read_text(encoding="utf-8")
    return _render_prompt(template, question=question, contexts=contexts, lang=lang)

def generate_answer_nonstream(*, question: str, contexts: List[Dict], lang: str) -> Tuple[str, str]:
    prompt = build_prompt_from_template(
        question=question,
        contexts=contexts,
        lang=lang,
    )
    return answer_once_gemini(prompt=prompt)

def generate_answer_stream(*, question: str, contexts: List[Dict], lang: str):
    prompt = build_prompt_from_template(
        question=question,
        contexts=contexts,
        lang=lang,
    )
    return stream_answer_gemini(prompt=prompt)

def prepare_contexts_for_response(contexts: List[Dict]) -> List[Dict]:
    return _normalize_contexts(contexts)

