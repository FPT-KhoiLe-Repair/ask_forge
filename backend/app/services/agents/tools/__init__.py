from abc import ABC, abstractmethod

from ask_forge.backend.app.repositories.vectorstore import ChromaRepo


class AgentTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        pass

class VectorSearchTool(AgentTool):
    def __init__(self, repo: ChromaRepo):
        self.repo = repo

    @property
    def name(self) -> str:
        return "vector_search"

    @property
    def description(self) -> str:
        return "Search knowledge base for relevant context"

    async def run(self, query: str, index: str, k: int =5) -> dict:
        results = self.repo.get_context_for_chat(index, query, k)
        return {"contexts": results}
