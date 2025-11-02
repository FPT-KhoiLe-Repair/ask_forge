from ask_forge.backend.app.services.chat.pipeline import answer_once_gemini
from ask_forge.backend.app.core.app_state import AppState


def _render_prompt(template:str, *, history_block: str="") -> str:
    return (
        template.replace("{{HISTORY_BLOCK}}", history_block)
    )

def build_session_summary_prompt_from_template(*,
                                    history_block:str="")->str:
    from pathlib import Path
    TPL = Path(__file__).resolve().parent / "prompts" / "session_summary_prompt.txt"
    template = TPL.read_text(encoding="utf-8")
    return _render_prompt(template, history_block=history_block)


def generate_session_summary(*,
                             app_state:AppState,
                             history_block:str="",
                             ):
    prompt = build_session_summary_prompt_from_template(
        history_block=history_block
    )
    return answer_once_gemini(prompt=prompt, app_state=app_state)