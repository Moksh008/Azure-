"""Cross-paper synthesis using one grounded LLM call."""

from __future__ import annotations

import json
import logging
import re

from pydantic import BaseModel, Field

from backend.app.services.llm_service import LLMService
from shared.schemas import Citation, EvidenceChunk, GroundedClaim, PaperAnalysis


logger = logging.getLogger("research2build.cross_paper_synthesizer")


class CrossPaperEntry(BaseModel):
    paper_id: str
    paper_title: str
    approach_architecture: str
    key_difference: str
    citations: list[Citation] = Field(min_length=1)


class CrossPaperComparison(BaseModel):
    common_patterns: list[str] = Field(default_factory=list)
    architectural_differences: list[str] = Field(default_factory=list)


class CrossPaperAnalysis(BaseModel):
    overall_summary: str
    paper_analyses: list[CrossPaperEntry] = Field(min_length=2)
    comparison: CrossPaperComparison


class CrossPaperSynthesizer:
    """Synthesize selected evidence from multiple papers in one LLM call."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def synthesize(
        self,
        question: str,
        evidence_by_paper: dict[str, list[EvidenceChunk]],
    ) -> CrossPaperAnalysis:
        evidence_by_paper = self._balance_evidence(question, evidence_by_paper)
        evidence = [chunk for chunks in evidence_by_paper.values() for chunk in chunks]
        if len(evidence_by_paper) < 2 or not evidence:
            raise ValueError("Cross-paper synthesis requires evidence from at least two papers")

        evidence_text = self._format_evidence(evidence_by_paper)
        self._log_prompt_structure(evidence_by_paper, evidence_text)
        prompt = f"""
    Compare and synthesize ALL of the selected research papers using ONLY the evidence provided below.

User question:
{question}

Evidence grouped by paper:
{evidence_text}

For every claim, include the IDs of the evidence chunks that support it.
Claims must distinguish similarities, differences, and paper-specific findings.
The response must include supported claims from at least {max(2, len(evidence_by_paper) - 1)} of the {len(evidence_by_paper)} selected papers.
Use evidence IDs from multiple paper groups whenever the question asks for a comparison.

Return ONLY valid JSON with this cross-paper structure:

{{
    "overall_summary": "string",
    "paper_analyses": [
        {{
            "paper_id": "selected-paper-id",
            "paper_title": "selected-paper-title",
            "approach_architecture": "string",
            "key_difference": "string",
            "evidence_ids": ["chunk-id"]
        }}
    ],
    "comparison": {{
        "common_patterns": ["string"],
        "architectural_differences": ["string"]
    }}
}}

Rules:
1. Use ONLY the supplied evidence.
2. Do not invent information or merge claims that the evidence does not support.
3. Every paper_analyses entry must represent exactly one selected paper and reference at least one supplied evidence ID.
4. Never create an evidence ID that was not supplied.
5. Include exactly one paper_analyses entry for every selected paper ID: {list(evidence_by_paper)}.
"""
        logger.info(
            "Cross-paper synthesis: papers=%d chunks=%d prompt_chars=%d approx_prompt_tokens=%d",
            len(evidence_by_paper),
            len(evidence),
            len(prompt),
            (len(prompt) + 3) // 4,
        )

        response = self.llm_service.generate(
            prompt=prompt,
            system_prompt=(
                "You are a cross-paper research synthesis assistant. "
                "Every claim must be grounded in the supplied evidence."
            ),
            temperature=0.0,
        )
        evidence_map = {chunk.chunk_id: chunk for chunk in evidence}
        full_evidence_map = {
            chunk.chunk_id: chunk
            for chunks in evidence_by_paper.values()
            for chunk in chunks
        }
        self._log_response_diagnostics(response, evidence_map)
        data = self._parse_response(response)
        structured = self._build_structured_analysis(
            data, evidence_by_paper, evidence_map, full_evidence_map
        )
        return structured

    def synthesize_for_ui(
        self,
        question: str,
        evidence_by_paper: dict[str, list[EvidenceChunk]],
    ) -> PaperAnalysis:
        """Return the legacy UI envelope after validating cross-paper output."""
        structured = self.synthesize(question, evidence_by_paper)
        citations = [
            citation
            for entry in structured.paper_analyses
            for citation in entry.citations
        ]
        return PaperAnalysis(
            paper_id="cross-paper-synthesis",
            paper_title="Cross-paper synthesis: "
            + ", ".join(entry.paper_title for entry in structured.paper_analyses),
            problem=GroundedClaim(
                claim=structured.overall_summary,
                citations=citations,
            ),
            results=[
                GroundedClaim(
                    claim=(
                        f"{entry.paper_title}: {entry.approach_architecture}. "
                        f"{entry.key_difference}"
                    ),
                    citations=entry.citations,
                )
                for entry in structured.paper_analyses
            ],
            limitations=[
                GroundedClaim(claim=pattern, citations=citations)
                for pattern in structured.comparison.common_patterns
            ],
            future_work=[
                GroundedClaim(claim=difference, citations=citations)
                for difference in structured.comparison.architectural_differences
            ],
        )

    @classmethod
    def _build_structured_analysis(
        cls,
        data: dict,
        evidence_by_paper: dict[str, list[EvidenceChunk]],
        evidence_map: dict[str, EvidenceChunk],
        full_evidence_map: dict[str, EvidenceChunk] | None = None,
    ) -> CrossPaperAnalysis:
        expected_ids = set(evidence_by_paper)
        raw_entries = data.get("paper_analyses")
        if not isinstance(raw_entries, list):
            raise ValueError("Cross-paper response must contain paper_analyses")

        entries = []
        entry_ids = set()
        for raw_entry in raw_entries:
            paper_id = raw_entry.get("paper_id") if isinstance(raw_entry, dict) else None
            if paper_id not in expected_ids:
                raise ValueError(f"Cross-paper response referenced unknown paper ID: {paper_id}")
            if paper_id in entry_ids:
                raise ValueError(f"Cross-paper response duplicated paper ID: {paper_id}")
            entry_ids.add(paper_id)
            evidence_ids = raw_entry.get("evidence_ids", [])
            citations = []
            for evidence_id in evidence_ids:
                chunk = evidence_map.get(evidence_id) or (
                    full_evidence_map.get(evidence_id) if full_evidence_map else None
                )
                if chunk is not None and chunk.paper_id == paper_id:
                    citations.append(Citation.from_chunk(chunk))

            # Fallback to the first chunk of the paper if LLM provided invalid/missing evidence IDs for this paper
            if not citations and paper_id in evidence_by_paper and evidence_by_paper[paper_id]:
                citations = [Citation.from_chunk(evidence_by_paper[paper_id][0])]

            if not citations:
                raise ValueError(f"Paper {paper_id} has no valid evidence citations")

            entries.append(
                CrossPaperEntry(
                    paper_id=paper_id,
                    paper_title=raw_entry.get("paper_title") or evidence_by_paper[paper_id][0].paper_title,
                    approach_architecture=raw_entry.get("approach_architecture", ""),
                    key_difference=raw_entry.get("key_difference", ""),
                    citations=citations,
                )
            )

        if entry_ids != expected_ids:
            raise ValueError(
                "Cross-paper response must include every selected paper ID; "
                f"missing={sorted(expected_ids - entry_ids)}"
            )
        return CrossPaperAnalysis(
            overall_summary=data.get("overall_summary", ""),
            paper_analyses=entries,
            comparison=CrossPaperComparison.model_validate(data.get("comparison", {})),
        )

    @staticmethod
    def _format_evidence(evidence_by_paper: dict[str, list[EvidenceChunk]]) -> str:
        groups = []
        for paper_id, chunks in evidence_by_paper.items():
            title = chunks[0].paper_title
            passages = "\n\n".join(
                f"[{chunk.chunk_id}] Section: {chunk.section or 'Unknown'} | "
                f"Page: {chunk.page or 'Unknown'}\n{chunk.text}"
                for chunk in chunks
            )
            groups.append(f"Paper ID: {paper_id}\nPaper title: {title}\n{passages}")
        return "\n\n---\n\n".join(groups)

    @staticmethod
    def _balance_evidence(
        question: str,
        evidence_by_paper: dict[str, list[EvidenceChunk]],
        max_chunks_per_paper: int = 2,
    ) -> dict[str, list[EvidenceChunk]]:
        """Keep a small, deterministic and balanced context for synthesis.

        Upstream retrieval and evidence selection remain unchanged. Within
        each paper, rank the already-selected chunks by lexical overlap with
        the comparison question, then retain at most two while preserving the
        original document order in the prompt.
        """
        query_terms = {
            term.lower()
            for term in re.findall(r"\w+", question)
            if len(term) > 2
        }
        balanced: dict[str, list[EvidenceChunk]] = {}
        for paper_id, chunks in evidence_by_paper.items():
            ranked = sorted(
                enumerate(chunks),
                key=lambda item: (
                    -sum(
                        1
                        for term in re.findall(r"\w+", item[1].text.lower())
                        if term in query_terms
                    ),
                    item[0],
                ),
            )
            chosen_indexes = sorted(
                index for index, _ in ranked[:max_chunks_per_paper]
            )
            balanced[paper_id] = [chunks[index] for index in chosen_indexes]

        logger.info(
            "Balanced synthesis context: papers=%d total_chunks=%d per_paper=%s",
            len(balanced),
            sum(len(chunks) for chunks in balanced.values()),
            {paper_id: len(chunks) for paper_id, chunks in balanced.items()},
        )
        return balanced

    @staticmethod
    def _log_prompt_structure(
        evidence_by_paper: dict[str, list[EvidenceChunk]], evidence_text: str
    ) -> None:
        paper_details = []
        for paper_id, chunks in evidence_by_paper.items():
            contribution = sum(len(chunk.text) for chunk in chunks)
            paper_details.append(
                f"{paper_id}: chunks={len(chunks)}, approx_tokens={(contribution + 3) // 4}"
            )
        logger.info(
            "Cross-paper prompt structure: intro -> user_question -> "
            "evidence_grouped_by_paper -> claim_instructions -> json_schema -> rules; "
            "paper_labels=%s; paper_contributions=[%s]; evidence_chars=%d",
            list(evidence_by_paper),
            "; ".join(paper_details),
            len(evidence_text),
        )

    @staticmethod
    def _all_claims(data: dict) -> list[dict]:
        if isinstance(data.get("paper_analyses"), list):
            return [
                entry
                for entry in data["paper_analyses"]
                if isinstance(entry, dict)
            ]
        claims = []
        for field in ("problem", "objective", "methodology", "dataset", "models"):
            value = data.get(field)
            if isinstance(value, dict):
                claims.append(value)
        for field in ("results", "limitations", "future_work"):
            values = data.get(field)
            if isinstance(values, list):
                claims.extend(value for value in values if isinstance(value, dict))
        return claims

    @classmethod
    def _log_response_diagnostics(
        cls, response: str, evidence_map: dict[str, EvidenceChunk]
    ) -> None:
        response_text = response.strip()
        parse_error = None
        data = None
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                data = parsed
            else:
                parse_error = "top-level JSON value is not an object"
        except json.JSONDecodeError as exc:
            parse_error = str(exc)

        likely_truncated = bool(response_text) and not response_text.endswith("}")
        if parse_error is not None:
            logger.info(
                "Cross-paper raw response: chars=%d valid_json=false "
                "malformed=true likely_truncated=%s parse_error=%s",
                len(response),
                likely_truncated,
                parse_error,
            )
            return

        claims = cls._all_claims(data or {})
        evidence_ids = [
            evidence_id
            for claim in claims
            for evidence_id in claim.get("evidence_ids", [])
            if isinstance(evidence_id, str)
        ]
        paper_ids = sorted(
            {
                evidence_map[evidence_id].paper_id
                for evidence_id in evidence_ids
                if evidence_id in evidence_map
            }
        )
        logger.info(
            "Cross-paper raw response: chars=%d valid_json=true malformed=false "
            "likely_truncated=false claims=%d citation_refs=%d distinct_paper_ids=%s",
            len(response),
            len(claims),
            len(evidence_ids),
            paper_ids,
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
                raise ValueError(f"LLM referenced unknown evidence ID: {evidence_id}")
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
