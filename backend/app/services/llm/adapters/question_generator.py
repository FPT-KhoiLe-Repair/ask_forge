# backend/app/services/llm/adapters/question_generator.py
import asyncio
import torch
from typing import AsyncIterator, Optional, Dict, List
from transformers import AutoTokenizer, AutoModelForCausalLM

from ask_forge.backend.app.services.llm.base import LLMProvider
from ask_forge.backend.app.core.config import settings


class QuestionGeneratorAdapter: # Không dùng LLMProvider nữa vì nhu cầu sử dụng tham số khác
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
            prompt: str, # seed_question
            contexts: List[Dict],
            n: int=5,
            lang: str = "vi",
            history_block: str ="",
            summary_block: str ="",
            **kwargs # temperature
    ) -> str:
        await self._ensure_loaded()
        loop = asyncio.get_running_loop()

        def _gen():
            contexts_str = "".join(ctx["text"] for ctx in contexts)
            # TODO: Build queries prompt here

            inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=1000,
                    do_sample=True,
                    temperature=kwargs.get("temperature", 0.2),
                    pad_token_id=self._tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            return self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        return await loop.run_in_executor(None, _gen)

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        # HF TextIteratorStreamer cho streaming
        from transformers import TextIteratorStreamer
        from threading import Thread

        await self._ensure_loaded()

        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)

        def _generate():
            self._model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_tokens", 512),
                streamer=streamer,
                do_sample=True,
                temperature=kwargs.get("temperature", 0.7)
            )

        thread = Thread(target=_generate)
        thread.start()

        for text in streamer:
            yield text

        thread.join()

    @property
    def model_name(self) -> str:
        return f"hf:{self.model_repo}"

    @property
    def supports_streaming(self) -> bool:
        return True