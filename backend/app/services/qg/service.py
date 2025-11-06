from typing import Dict, List

from ask_forge.backend.app.services.qg.pipeline import HFQueryGenerator
from ask_forge.backend.app.core.config import settings
class QGService:
    def __init__(self):
        self.generator = HFQueryGenerator(model_repo=settings.HF_QUESTION_GENERATOR_CKPT)

    async def generate_questions(self,
                                 seed_question: str,
                                 contexts: List[Dict],
                                 n: int = 5,
                                 lang: str = "vi",
                                 history_block: str = "",
                                 summary_block: str = "",):
        contexts_str = "".join(ctx["text"] for ctx in contexts)
        return await self.generator.generate(seed_question, contexts_str, n, lang, history_block=history_block, summary_block=summary_block)
