from app.retrieval.evidence import EvidenceChunk
from app.retrieval.retriever import Retriever


class DemoRetriever(Retriever):
    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        demo_chunks = [
            EvidenceChunk(
                chunk_id="demo-001",
                paper_id="https://openalex.org/W123456789",
                title="Fake News Detection on Social Media",
                text=(
                    "Social media enables rapid dissemination of news "
                    "and misinformation."
                ),
                source_url="https://doi.org/10.1145/3137597.3137600",
                page_number=1,
                section="Introduction",
            ),
            EvidenceChunk(
                chunk_id="demo-002",
                paper_id="https://openalex.org/W987654321",
                title="MVAE: Multimodal Variational Autoencoder for Fake News Detection",
                text=(
                    "Fake news spreads rapidly through microblogging networks "
                    "and can have a significant social impact."
                ),
                source_url="https://doi.org/10.1145/3308558.3313552",
                page_number=1,
                section="Introduction",
            ),
        ]

        return demo_chunks[:top_k]
