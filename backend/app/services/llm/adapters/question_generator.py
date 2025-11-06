# backend/app/services/llm/adapters/question_generator.py
import asyncio
import torch
from typing import AsyncIterator, Optional, Dict, List
from transformers import AutoTokenizer, AutoModelForCausalLM

import logging
from ask_forge.backend.app.services.llm.base import LLMProvider
from ask_forge.backend.app.core.config import settings
import re  # Thêm vào đầu file

from ask_forge.backend.app.services.qg.prompts.templates import build_queries_prompt_from_template

logger = logging.getLogger(__name__)

class QuestionGeneratorAdapter(LLMProvider): # Không dùng LLMProvider nữa vì nhu cầu sử dụng tham số khác
    # TODO: Tương lai có thể update thêm các base khi mà hệ thống định hình được các Apdapter gống nhau
    def __init__(self, model_repo: str):
        self.model_repo = model_repo
        self._tokenizer: Optional[AutoTokenizer] = None
        self._model: Optional[AutoModelForCausalLM] = None
        self._load_lock = asyncio.Lock()

    async def _ensure_loaded(self):
        """Lazy load model (non-blocking)"""
        if self._model is not None:
            return

        async with self._load_lock:
            if self._model is not None:
                return

            loop = asyncio.get_running_loop()
            dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

            def _load():
                tok = AutoTokenizer.from_pretrained(self.model_repo)
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_repo,
                    dtype=dtype,  # FIX lỗi chính tả 'dtye'
                    device_map=settings.HF_DEVICE_MAP,
                ).eval()
                return tok, model

            self._tokenizer, self._model = await loop.run_in_executor(None, _load)

    async def generate(
            self,
            prompt: str,
            **kwargs
    ) -> str:
        """Generates answer from question"""
        await self._ensure_loaded()
        contexts = kwargs.get("contexts")
        n = kwargs.get("n")
        lang = kwargs.get("lang")
        history_block = kwargs.get("history_block")
        summary_block = kwargs.get("summary_block")

        user_prompt = build_queries_prompt_from_template(
            seed_question=prompt,
            contexts=contexts,
            n=n,
            lang=lang,
            history_block=history_block,
            summary_block=summary_block,
        )
        model_inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **model_inputs,
                max_new_tokens=1000,
                do_sample=True,
                temperature=0.2,
                pad_token_id=self._tokenizer.eos_token_id,
                repetition_penalty=1.1
            )

        resp_ids = outputs[0]
        raw = self._tokenizer.decode(resp_ids, skip_special_tokens=True).replace("<think>", "")

        # ✂️ Cắt ngay khi gặp <EOS> đầu tiên
        if "<EOS>" in raw:
            raw = raw.split("<EOS>")[0]

        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
        logger.info(f"Generated: {"\n".join(lines)}")

        return lines

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        pass

    @property
    def model_name(self) -> str:
        return f"hf:{self.model_repo}"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def generate_questions(
            self,
            prompt: str,  # seed_question
            contexts: List[Dict],
            n: int = 5,
            lang: str = "vi",
            history_block: str = "",
            summary_block: str = "",
            **kwargs
    ) -> List[str]:
        """
        Generate follow-up questions

        Returns: List[str] - List of questions
        """
        await self._ensure_loaded()
        loop = asyncio.get_running_loop()

        def _gen():
            # ===== Build prompt for QG =====
            contexts_str = "\n".join(
                f"[{i + 1}] {ctx['text'][:300]}..."
                for i, ctx in enumerate(contexts[:3])  # Top 3 contexts
            )

            # ===== Generate =====
            inputs = self._tokenizer(
                [prompt],
                return_tensors="pt",
                truncation=True,
                max_length=1024
            ).to(self._model.device)

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=500,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self._tokenizer.eos_token_id,
                    repetition_penalty=1.2
                )

            # ===== Parse output =====
            generated_text = self._tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )

            # Extract questions (split by newlines)
            lines = generated_text.split("\n")
            questions = []

            for line in lines:
                line = line.strip()
                # Skip empty, too short, or prompt lines
                if (
                        line and
                        len(line) > 10 and
                        "?" in line and
                        not line.startswith("Question:") and
                        not line.startswith("Context:")
                ):
                    # Clean up numbering (1., 2., etc.)
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)
                    questions.append(line)

                    if len(questions) >= n:
                        break

            return questions[:n]  # Return exactly n questions

        return await loop.run_in_executor(None, _gen)
