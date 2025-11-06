from typing import Dict, Iterable, List
import re
def _render_prompt(template: str, *,
                   question:str,
                   contexts: str,
                   lang: str,
                   n: int,
                   history_block: str = "",
                   summary_block: str = "") -> str:
    return (
        template.replace("{{QUESTION}}", history_block + question)
                .replace("{{LANG}}", lang)
                # .replace("{{CONTEXT}}", contexts)
                # .replace("{{N}}", str(n))
                # .replace("{{HISTORY_BLOCK}}", history_block)
                # .replace("{{SUMMARY_BLOCK}}", summary_block)
    )

def _extract_questions_from_history(history_block: str) -> List[str]:
    """
    Lấy danh sách câu hỏi nằm trong <q>...</q> trong history_block
    """
    if not history_block:
        return []
    # Dùng regex để bắt nội dung giữa <q> và </q>
    questions = re.findall(r"<q>(.*?)</q>", history_block, flags=re.DOTALL)

    # Làm sạch từng câu
    cleaned = [q.strip() for q in questions if q.strip()]
    return cleaned

def build_queries_prompt_from_template(
        *,
        seed_question: str,
        contexts: str,
        n:int,
        lang: str,
        history_block:str= "", summary_block:str= "") -> str:
    # Đọc template từ file (đọc mỗi lần cho đơn giản; nếu muốn có thể cache)
    from pathlib import Path

    # Parse <q>...</q> -> danh sách câu hỏi
    history_questions = _extract_questions_from_history(history_block)


    # Nếu có câu hỏi thì nối thành khối gọn gàng
    if history_questions:
        formatted_history = "\n".join(
            f" {q}" for q in history_questions[:]
        )
    else:
        formatted_history = ""
    with open("qg_prompt.txt", "w", encoding="utf-8") as f:
        f.write(formatted_history)

    return formatted_history
    return _render_prompt(template,
                          question=seed_question,
                          contexts=contexts,
                          lang=lang,
                          n=n,
                          history_block=formatted_history,
                          summary_block=summary_block)

