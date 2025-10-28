from typing import List
import torch
from ..prompts.templates import build_queries_prompt
from ...core.app_state import app_state

class __QueryGenerator:
    def generate(self,
                 seed_question: str,
                 contexts: str,
                 n: int = 5,
                 lang: str = "vn",
                 model_repo: str = "Qwen/Qwen2.5-0.5B") -> List[str]:
        raise NotImplementedError

class HFQueryGenerator(__QueryGenerator):
    async def generate(self,
                 seed_question: str,
                 contexts: str,
                 n: int = 5,
                 lang: str = "vn",
                 model_repo: str ="Qwen/Qwen2.5-0.5B") -> List[str]:
        tok, model = await app_state.ensure_hf_model(model_repo)

        user_prompt = build_queries_prompt(
            seed_question=seed_question,
            contexts=contexts,
            n=n,
            lang=lang,
        )
        messages = [
            {"role": "system", "content": f"Always answer in {lang}."},
            {"role": "system", "content": user_prompt},
        ]

        text = tok.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        model_inputs = tok([text], return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **model_inputs,
                max_new_tokens=300,
                do_sample=True,
                temperature=0.2,
                pad_token_id=tok.eos_token_id,
                repetition_penalty=1.1
            )

        resp_ids = outputs[0][len(model_inputs["input_ids"][0]):]
        raw = tok.decode(resp_ids, skip_special_tokens=True).replace("<think>","")

        # Kỳ vọng model trả về dạng danh sách; nếu không thì tách dòng:
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
        return lines