import json

from backend.app.services.llm_service import LLMService
from shared.schemas import EvidenceChunk, GroundedClaim, PaperAnalysis


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

Return ONLY valid JSON with this structure:

{{
  "problem": "string",
  "objective": "string",
  "methodology": "string",
  "dataset": "string",
  "models": "string",
  "results": ["string"],
  "limitations": ["string"],
  "future_work": ["string"]
}}

Do not invent information that is not present in the evidence.
"""

        response = self.llm_service.generate(
            prompt=prompt,
            system_prompt=(
                "You are a research paper analysis assistant. "
                "Use only the supplied evidence."
            ),
            temperature=0.0,
        )

        data = self._parse_response(response)

        return PaperAnalysis(
            paper_id=paper_id,
            paper_title=paper_title,
            problem=self._claim(data.get("problem")),
            objective=self._claim(data.get("objective")),
            methodology=self._claim(data.get("methodology")),
            dataset=self._claim(data.get("dataset")),
            models=self._claim(data.get("models")),
            results=self._claims(data.get("results")),
            limitations=self._claims(data.get("limitations")),
            future_work=self._claims(data.get("future_work")),
        )

    @staticmethod
    def _format_evidence(evidence: list[EvidenceChunk]) -> str:
        parts = []

        for chunk in evidence:
            parts.append(
                f"[{chunk.chunk_id}] "
                f"Section: {chunk.section or 'Unknown'} | "
                f"Page: {chunk.page or 'Unknown'}\n"
                f"{chunk.text}"
            )

        return "\n\n".join(parts)

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
    def _claim(value: str | None) -> GroundedClaim | None:
        if not value:
            return None

        return GroundedClaim(text=value)

    @staticmethod
    def _claims(values: list[str] | None) -> list[GroundedClaim]:
        if not values:
            return []

        return [
            GroundedClaim(text=value)
            for value in values
            if value
        ]