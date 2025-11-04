from typing import List
import torch, json
from ask_forge.backend.app.core.app_state import app_state
from ask_forge.backend.app.services.qg.prompts.templates import build_queries_prompt_from_template
from ask_forge.backend.app.core.app_state import logger
class __QueryGenerator:
    def generate(self,
                 seed_question: str,
                 contexts: str,
                 n: int = 5,
                 lang: str = "vn",) -> List[str]:
        raise NotImplementedError

class HFQueryGenerator(__QueryGenerator):
    def __init__(self, model_repo: str):
        self.model_repo = model_repo
    async def generate(self,
                 seed_question: str,
                 contexts: str,
                 n: int = 5,
                 lang: str = "vn",
                 history_block: str = "",
                 summary_block: str = "") -> List[str]:
        tok, model = app_state._hf_tok, app_state._hf_model

        user_prompt = build_queries_prompt_from_template(
            seed_question=seed_question,
            contexts=contexts,
            n=n,
            lang=lang,
            history_block=history_block,
            summary_block=summary_block
        )

        model_inputs = tok([seed_question], return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **model_inputs,
                max_new_tokens=1000,
                do_sample=True,
                temperature=0.2,
                pad_token_id=tok.eos_token_id,
                repetition_penalty=1.1
            )


        resp_ids = outputs[0]
        raw = tok.decode(resp_ids, skip_special_tokens=True).replace("<think>","")


        # ✂️ Cắt ngay khi gặp <EOS> đầu tiên
        if "<EOS>" in raw:
            raw = raw.split("<EOS>")[0]

        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
        logger.info(f"Generated: {"\n".join(lines)}")

        return lines