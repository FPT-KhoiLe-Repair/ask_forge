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


class QuestionGeneratorAdapter(LLMProvider):
    """
    ✅ Unified adapter for Question Generation with HuggingFace models

    Implements both:
    - generate() for compatibility with LLMProvider interface
    - generate_questions() for specific QG use case
    """

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
                logger.info(f"🧠 Loading QG model: {self.model_repo}")
                tok = AutoTokenizer.from_pretrained(self.model_repo)
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_repo,
                    torch_dtype=torch.bfloat16,
                    device_map=settings.HF_DEVICE_MAP,
                ).eval()
                logger.info(f"✅ QG model loaded on {settings.HF_DEVICE_MAP}")
                return tok, model

            self._tokenizer, self._model = await loop.run_in_executor(None, _load)

    async def generate(
            self,
            prompt: str,
            contexts: List[Dict] =None,
            n: int = 5,
            lang: str = "vi",
            history_block: str = "",
            summary_block: str = "",
            **kwargs
    ) -> List[str]:
        """
        ✅ Main generate method - returns list of questions

        This method unifies the interface for both:
        - Direct calls from chat service
        - Worker calls via router
        """
        # contexts = kwargs.get("contexts")
        # n = kwargs.get("n")
        # lang = kwargs.get("lang")
        # history_block = kwargs.get("history_block")
        # summary_block = kwargs.get("summary_block")

        await self._ensure_loaded()
        loop = asyncio.get_running_loop()

        def _gen():
            user_prompt = prompt
            # user_prompt = build_queries_prompt_from_template(
            #     seed_question=prompt,
            #     contexts=self._format_contexts(contexts),
            #     n=n,
            #     lang=lang,
            #     history_block=history_block,
            #     summary_block=summary_block,
            # )

            # Tokenize
            model_inputs = self._tokenizer([user_prompt],return_tensors="pt",).to(self._model.device)

            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **model_inputs,
                    max_new_tokens=1000,
                    do_sample=True,
                    temperature=0.2,
                    pad_token_id=self._tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            # Decode & Parse
            resp_ids = outputs[0]
            raw = self._tokenizer.decode(resp_ids, skip_special_tokens=True).replace("<think>", "")

            # ✂️ Cắt ngay khi gặp <EOS> đầu tiên
            if "<EOS>" in raw:
                raw = raw.split("<EOS>")[0]

            questions = [ln.strip() for ln in raw.split("\n") if ln.strip()]
            questions = self._filter_questions(questions)

            logger.info(f"✅ Generated {len(questions)}/{n} questions")
            return questions

        return await loop.run_in_executor(None, _gen)

    def _format_contexts(self, contexts: Optional[List[Dict]]) -> str:
        """Format contexts list into string"""
        if not contexts:
            return ""

        formatted = []
        for i, ctx in enumerate(contexts[:3], 1):  # Top 3 contexts
            text = ctx.get("text", "")[:300]  # Limit to 300 chars
            formatted.append(f"[{i}] {text}...")

        return "\n".join(formatted)
    def _filter_questions(self, questions: List[str]) -> List[str]:
        # TODO: Nếu như m muốn chỉnh sửa thêm bộ lọc để lọc ra những question chất lượng thì làm ở đây
        return questions

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Not implemented for QG - questions are generated in batch"""
        raise NotImplementedError("QG does not support streaming")

    @property
    def model_name(self) -> str:
        return f"hf:{self.model_repo}"

    @property
    def supports_streaming(self) -> bool:
        return True