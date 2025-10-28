from typing import Dict, List

from ask_forge.backend.app.features.qg.pipeline import HFQueryGenerator

class QGService:
    def __init__(self):
        self.generator = HFQueryGenerator()

    async def generate_questions(self, seed_question: str, contexts: List[Dict], n: int = 5, lang: str = "vi"):
        contexts_str = "".join(ctx["text"] for ctx in contexts)
        return await self.generator.generate(seed_question, contexts_str, n, lang)
