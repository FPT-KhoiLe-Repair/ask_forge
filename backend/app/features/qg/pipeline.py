from typing import List, Dict
import torch, json
from ask_forge.backend.app.core.app_state import app_state
from ask_forge.backend.app.features.qg.prompt.templates import build_queries_prompt

class HFQueryGenerator:
    async def generate(self, seed_question: str, contexts: str, n: int = 5, lang: str = "vi") -> Dict:
        tok, model = await app_state.ensure_hf_model()

        prompt = build_queries_prompt(seed_question=seed_question, contexts=contexts, n=n, lang=lang)
        messages = [
            {"role": "system", "content": f"Always answer in {lang}."},
            {"role": "user", "content": prompt},
        ]

        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tok([text], return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **model_inputs,
                max_new_tokens=300,
                temperature=0.2,
                do_sample=True,
                pad_token_id=tok.eos_token_id,
                repetition_penalty=1.1
            )

        resp_ids = outputs[0][len(model_inputs["input_ids"][0]):]
        raw = tok.decode(resp_ids, skip_special_tokens=True).replace("<think>", "").strip()

        # Try parse JSON first
        try:
            parsed = json.loads(raw)
            questions = parsed.get("questions", parsed)
        except Exception:
            questions = [ln.strip("-• ") for ln in raw.split("\n") if ln.strip()]

        return {
            "raw": raw,
            "questions": questions,
            "count": len(questions)
        }
