import json

from backend.app.services.llm_service import LLMService
from shared.schemas import (
    Citation,
    EvidenceChunk,
    GroundedAnswer,
)
import json

from backend.app.services.llm_service import LLMService
from shared.schemas import (
    Citation,
    EvidenceChunk,
    GroundedClaim,
    PaperAnalysis,
)


class PaperAnalyzer:
    """Analyze a research paper using retrieved evidence."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def analyze(
        self,
        paper_id: str,
        paper_title: str,
        evidence: list[EvidenceChunk],
    ) -> PaperAnalysis:
        if not evidence:
            raise ValueError("At least one evidence chunk is required")

        evidence_text = self._format_evidence(evidence)
        prompt = f"""
Analyze the research paper using ONLY the evidence provided below.

Paper ID: {paper_id}
Paper title: {paper_title}

Evidence:
{evidence_text}

For every claim, include the IDs of the evidence chunks that support it.

Return ONLY valid JSON with this structure:

{{
  "problem": {{"text": "string", "evidence_ids": ["chunk-id"]}},
  "objective": {{"text": "string", "evidence_ids": ["chunk-id"]}},
  "methodology": {{"text": "string", "evidence_ids": ["chunk-id"]}},
  "dataset": {{"text": "string", "evidence_ids": ["chunk-id"]}},
  "models": {{"text": "string", "evidence_ids": ["chunk-id"]}},
  "results": [{{"text": "string", "evidence_ids": ["chunk-id"]}}],
  "limitations": [{{"text": "string", "evidence_ids": ["chunk-id"]}}],
  "future_work": [{{"text": "string", "evidence_ids": ["chunk-id"]}}]
}}

Rules:
1. Use ONLY the supplied evidence.
2. Do not invent information.
3. Every claim must reference at least one supplied evidence ID.
4. Never create an evidence ID that was not supplied.
"""

        response = self.llm_service.generate(
            prompt=prompt,
            system_prompt=(
                "You are a research paper analysis assistant. "
                "Every claim must be grounded in the supplied evidence."
            ),
            temperature=0.0,
        )
        data = self._parse_response(response)
        evidence_map = {chunk.chunk_id: chunk for chunk in evidence}

        return PaperAnalysis(
            paper_id=paper_id,
            paper_title=paper_title,
            problem=self._claim(data.get("problem"), evidence_map),
            objective=self._claim(data.get("objective"), evidence_map),
            methodology=self._claim(data.get("methodology"), evidence_map),
            dataset=self._claim(data.get("dataset"), evidence_map),
            models=self._claim(data.get("models"), evidence_map),
            results=self._claims(data.get("results"), evidence_map),
            limitations=self._claims(data.get("limitations"), evidence_map),
            future_work=self._claims(data.get("future_work"), evidence_map),
        )

    @staticmethod
    def _format_evidence(evidence: list[EvidenceChunk]) -> str:
        return "\n\n".join(
            f"[{chunk.chunk_id}] Section: {chunk.section or 'Unknown'} | "
            f"Page: {chunk.page or 'Unknown'}\n{chunk.text}"
            for chunk in evidence
        )

    @staticmethod
    def _parse_response(response: str) -> dict:
        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise ValueError("LLM response must be a JSON object")
        return data

    @staticmethod
    def _citation(chunk: EvidenceChunk) -> Citation:
        return Citation.from_chunk(chunk)

    @classmethod
    def _claim(
        cls,
        value: dict | None,
        evidence_map: dict[str, EvidenceChunk],
    ) -> GroundedClaim | None:
        if not value:
            return None

        text = value.get("text")
        if not text:
            return None

        citations = []
        for evidence_id in value.get("evidence_ids", []):
            chunk = evidence_map.get(evidence_id)
            if chunk is None:
                raise ValueError(
                    f"LLM referenced unknown evidence ID: {evidence_id}"
                )
            citations.append(cls._citation(chunk))

        if not citations:
            raise ValueError(f"Claim has no valid evidence citations: {text}")

        return GroundedClaim(claim=text, citations=citations)

    @classmethod
    def _claims(
        cls,
        values: list[dict] | None,
        evidence_map: dict[str, EvidenceChunk],
    ) -> list[GroundedClaim]:
        if not values:
            return []

        return [
            claim
            for value in values
            if (claim := cls._claim(value, evidence_map)) is not None
        ]