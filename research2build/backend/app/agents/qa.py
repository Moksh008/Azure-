import json
import logging

from backend.app.services.llm_service import LLMService
from shared.schemas import (
    Citation,
    EvidenceChunk,
    GroundedAnswer,
)

logger = logging.getLogger("research2build.qa")


class GroundedQA:
    """Answer questions using only supplied evidence."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def answer(
        self,
        question: str,
        evidence: list[EvidenceChunk],
    ) -> GroundedAnswer:
        if not question.strip():
            raise ValueError("Question cannot be empty")

        if not evidence:
            return GroundedAnswer(
                answer="I could not find enough evidence in the provided papers to answer this question.",
                citations=[],
                evidence_sufficient=False,
            )

        evidence_text = self._format_evidence(evidence)

        prompt = f"""
Answer the user's question using ONLY the evidence provided below.

Question:
{question}

Evidence:
{evidence_text}

Return ONLY valid JSON with this structure:

{{
  "answer": "string",
  "evidence_ids": ["chunk-id"],
  "evidence_sufficient": true
}}

Rules:
1. Use ONLY the supplied evidence.
2. Do not invent information.
3. Every factual answer must reference at least one supplied evidence ID.
4. Never create an evidence ID that was not supplied.
5. If the evidence is insufficient to answer the question, set
   "evidence_sufficient" to false and explain that the available evidence
   is insufficient.
"""

        evidence_map = {
            chunk.chunk_id: chunk
            for chunk in evidence
        }
        system_prompt = (
            "You are an evidence-based research assistant. "
            "Answer only from the supplied evidence."
        )

        try:
            response = self.llm_service.generate(
                prompt, system_prompt=system_prompt, temperature=0.0
            )
            data = self._parse_response(response)
            return self._build_answer(data, evidence_map)
        except ValueError as exc:
            logger.warning(
                "Grounded Q&A validation failed, retrying once: %s", exc
            )
            retry_prompt = (
                f"{prompt}\n\n"
                "IMPORTANT CORRECTION: your previous answer was rejected because it "
                f"failed this check: {exc}\n"
                "Only use evidence IDs exactly as they appear in brackets above — "
                "never invent, abbreviate, or renumber an evidence ID."
            )
            response = self.llm_service.generate(
                prompt=retry_prompt, system_prompt=system_prompt, temperature=0.0
            )
            data = self._parse_response(response)
            return self._build_answer(data, evidence_map)

    @classmethod
    def _build_answer(
        cls,
        data: dict,
        evidence_map: dict[str, EvidenceChunk],
    ) -> GroundedAnswer:
        citations = []
        evidence_ids = data.get("evidence_ids", [])

        for evidence_id in evidence_ids:
            chunk = evidence_map.get(evidence_id)

            if chunk is None:
                raise ValueError(
                    f"LLM referenced unknown evidence ID: {evidence_id}"
                )

            citations.append(cls._citation(chunk))

        answer = data.get("answer")

        if not answer:
            raise ValueError("LLM returned an empty answer")

        evidence_sufficient = data.get(
            "evidence_sufficient",
            bool(citations),
        )

        if evidence_sufficient and not citations:
            raise ValueError(
                "Sufficient answer must contain evidence citations"
            )

        return GroundedAnswer(
            answer=answer,
            citations=citations,
            evidence_sufficient=evidence_sufficient,
        )

    @staticmethod
    def _format_evidence(
        evidence: list[EvidenceChunk],
    ) -> str:
        parts = []

        for chunk in evidence:
            parts.append(
                f"[{chunk.chunk_id}] "
                f"Paper: {chunk.paper_title} | "
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
    def _citation(chunk: EvidenceChunk) -> Citation:
        return Citation.from_chunk(chunk)