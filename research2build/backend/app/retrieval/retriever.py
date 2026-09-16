from abc import ABC, abstractmethod

from app.retrieval.evidence import EvidenceChunk


class Retriever(ABC):
    @abstractmethod
    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        """Return the most relevant evidence chunks."""
        raise NotImplementedError
