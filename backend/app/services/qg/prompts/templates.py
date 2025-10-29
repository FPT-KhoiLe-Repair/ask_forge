from typing import Dict, Iterable, List

def _render_prompt(template: str, *, question:str, contexts: str, lang: str, n: int) -> str:
    return (
        template.replace("{{LANG}}", lang)
                .replace("{{QUESTION}}", question)
                .replace("{{CONTEXT}}", contexts)
                .replace("{{N}}", str(n))
    )

def build_queries_prompt(*, seed_question: str, contexts: str,n:int, lang: str) -> str:
    # Đọc template từ file (đọc mỗi lần cho đơn giản; nếu muốn có thể cache)
    from pathlib import Path
    TPL = Path(__file__).resolve().parent / "qg_prompt.txt"
    template = TPL.read_text(encoding="utf-8")
    return _render_prompt(template, question=seed_question, contexts=contexts, lang=lang, n=n)

# Answer in {lang}
# Question: {seed_question}
# Context: {ctx}
# Answer:"""