from typing import List, Dict, Any, Generator
from google.genai import types

SYSTEM_INSTRUCTION = (
    "Bạn là trợ giảng RAG. Luôn chính xác, không bịa. "
    "Chỉ sử dụng thông tin trong context; nếu thiếu, nói rõ là thiếu."
)

def build_chat_prompt(query_text: str, contexts: List[Dict[str, Any]]) -> str:
    ctx_lines = []
    for i, c in enumerate(contexts, 1):
        src = f"{c.get('source','')}#p{c.get('page','?')}"
        ctx_lines.append(f"[{i}] ({src})\n{c['text']}\n")
    ctx_block = "\n".join(ctx_lines)

    return f"""Bạn là trợ giảng trả lời dựa trên context đã cho.
Nếu thông tin không có trong context, hãy nói không chắc và đề nghị cung cấp thêm tài liệu.

# Context
{ctx_block}

# Câu hỏi
{query_text}

# Yêu cầu trả lời
- Ngắn gọn, súc tích, đúng trọng tâm.
- Khi khẳng định chi tiết từ context, ghi chú nguồn như [1], [2].
- Nếu nhiều nguồn mâu thuẫn, chỉ ra và giải thích.
"""

def stream_answer_gemini(client, model: str, prompt: str) -> Generator[str, None, None]:
    """Streaming generator (nâng cấp lên stream chỉ cần dùng hàm này)."""
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    cfg = types.GenerateContentConfig(
        response_modalities=["TEXT"],
        system_instruction=[types.Part.from_text(text=SYSTEM_INSTRUCTION)],
    )
    for chunk in client.models.generate_content_stream(model=model, contents=contents, config=cfg):
        if hasattr(chunk, "text") and chunk.text:
            yield chunk.text

def answer_once_gemini(client, model: str, prompt: str) -> str:
    """Non-stream: gộp các chunk lại thành một chuỗi."""
    return "".join(stream_answer_gemini(client, model, prompt))
