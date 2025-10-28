from ask_forge.backend.app.features.qg.pipeline import HFQueryGenerator

class QGService:
    def __init__(self):
        self.generator = HFQueryGenerator()

    async def generate_questions(self, seed_question: str, contexts: str, n: int = 5, lang: str = "vi"):
        return await self.generator.generate(seed_question, contexts, n, lang)
