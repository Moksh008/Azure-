"""M4 — Recurring limitations extraction component.

Scans a collection of paper analyses to identify limitations that recur
across multiple research papers.

Operates deterministically and locally without LLM or external dependencies.
Flexible across Pydantic models, plain objects, dictionaries, and raw strings.

Responsible AI constraint:
This component only groups and reports recurring limitations. It does NOT
claim that a research gap or novelty has been discovered.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from backend.app.research_intelligence.models import RecurringLimitation

# Stop words and filler words excluded from limitation clustering tokens
STOP_WORDS: frozenset[str] = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "should", "shouldn't", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "were", "weren't", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "won't", "would", "wouldn't", "you", "your",
    "yours", "yourself", "yourselves",
    # Academic/limitation boilerplate terms
    "paper", "study", "approach", "method", "model", "models", "system", "systems",
    "work", "author", "authors", "result", "results", "current", "currently",
    "specifically", "particularly", "observed", "reported", "due", "primarily",
})


@dataclass(frozen=True)
class SemanticLimitationCategory:
    """Represents a canonical recurring limitation concept."""

    category_id: str
    canonical_description: str
    core_concepts: frozenset[str]
    qualifiers: frozenset[str]
    trigger_phrases: tuple[str, ...]


# Canonical categories for research limitations
SEMANTIC_CATEGORIES: tuple[SemanticLimitationCategory, ...] = (
    SemanticLimitationCategory(
        category_id="data_scarcity",
        canonical_description="Limited training data and small dataset size",
        core_concepts=frozenset({
            "data", "dataset", "datasets", "sample", "samples", "examples",
            "corpus", "corpora", "examples",
        }),
        qualifiers=frozenset({
            "limited", "small", "insufficient", "scarcity", "scarce", "lack",
            "lacking", "few", "tiny", "modest", "restricted", "low", "shortage",
            "constrained", "scant",
        }),
        trigger_phrases=(
            "limited data", "small dataset", "data scarcity", "sample size",
            "small sample", "insufficient data", "limited training data",
            "dataset size", "few examples", "insufficient training data",
        ),
    ),
    SemanticLimitationCategory(
        category_id="compute_cost",
        canonical_description="High computational cost and hardware resource demands",
        core_concepts=frozenset({
            "compute", "computational", "hardware", "gpu", "gpus", "tpu", "tpus",
            "memory", "ram", "vram", "flops", "footprint", "resources",
        }),
        qualifiers=frozenset({
            "high", "expensive", "cost", "overhead", "heavy", "intensive",
            "prohibitive", "exorbitant", "demanding", "huge", "large", "excessive",
            "consumption", "constraints", "constrained", "requirements", "limited",
        }),
        trigger_phrases=(
            "computational cost", "compute overhead", "hardware requirements",
            "high compute", "gpu memory", "resource intensive", "memory overhead",
            "memory footprint", "compute resources",
        ),
    ),
    SemanticLimitationCategory(
        category_id="latency_overhead",
        canonical_description="High inference latency and runtime overhead",
        core_concepts=frozenset({
            "latency", "inference", "runtime", "speed", "throughput", "execution",
            "response", "delay",
        }),
        qualifiers=frozenset({
            "high", "slow", "overhead", "bottleneck", "long", "excessive",
            "increased", "degraded", "poor", "lag", "delays",
        }),
        trigger_phrases=(
            "high latency", "inference latency", "slow inference", "runtime overhead",
            "inference speed", "response time", "execution delay",
        ),
    ),
    SemanticLimitationCategory(
        category_id="generalization",
        canonical_description="Limited out-of-distribution generalization and domain transfer",
        core_concepts=frozenset({
            "generalization", "generalize", "transfer", "transferability", "domain",
            "unseen", "out-of-distribution", "ood", "cross-domain",
        }),
        qualifiers=frozenset({
            "limited", "poor", "lack", "fails", "struggles", "degradation",
            "degrades", "difficulty", "weak", "inability", "restricted",
        }),
        trigger_phrases=(
            "domain shift", "out-of-distribution", "limited generalization",
            "cross-domain", "unseen domains", "poor generalization", "generalization gap",
        ),
    ),
    SemanticLimitationCategory(
        category_id="scalability",
        canonical_description="Scalability bottlenecks on large-scale workloads",
        core_concepts=frozenset({
            "scalability", "scale", "scaling",
        }),
        qualifiers=frozenset({
            "poor", "limited", "bottleneck", "difficulty", "fails", "hard",
            "constrained", "issues", "unscalable", "challenges",
        }),
        trigger_phrases=(
            "scalability bottleneck", "scaling challenges", "poor scalability",
            "limits scalability", "does not scale", "scale poorly",
        ),
    ),
    SemanticLimitationCategory(
        category_id="hallucination",
        canonical_description="Susceptibility to hallucinations and factual inconsistencies",
        core_concepts=frozenset({
            "hallucination", "hallucinations", "factuality", "factual",
            "faithfulness", "grounding", "confabulation",
        }),
        qualifiers=frozenset({
            "high", "frequent", "susceptible", "errors", "issues", "unreliable",
            "prone", "unfaithful", "untruthful",
        }),
        trigger_phrases=(
            "prone to hallucination", "factual inconsistency", "hallucination rate",
            "unfaithful generation", "factual errors", "hallucinations",
        ),
    ),
    SemanticLimitationCategory(
        category_id="bias_diversity",
        canonical_description="Dataset bias and lack of demographic diversity",
        core_concepts=frozenset({
            "bias", "biases", "demographic", "diversity", "representation",
            "fairness", "skew", "skewed",
        }),
        qualifiers=frozenset({
            "high", "lack", "limited", "present", "inherent", "unbalanced",
            "imbalanced", "poor", "skewed",
        }),
        trigger_phrases=(
            "demographic diversity", "dataset bias", "representation bias",
            "lack of diversity", "demographic representation",
        ),
    ),
    SemanticLimitationCategory(
        category_id="interpretability",
        canonical_description="Limited model interpretability and explainability",
        core_concepts=frozenset({
            "interpretability", "explainability", "black-box", "transparency",
            "interpretable", "explainable",
        }),
        qualifiers=frozenset({
            "lack", "limited", "poor", "difficult", "challenging", "opaque",
            "black-box",
        }),
        trigger_phrases=(
            "black box", "limited interpretability", "lack of explainability",
            "opaque decision", "model interpretability",
        ),
    ),
    SemanticLimitationCategory(
        category_id="annotation_cost",
        canonical_description="High manual annotation and labeling overhead",
        core_concepts=frozenset({
            "annotation", "labeling", "annotators", "feedback", "rlhf", "curation", "label",
        }),
        qualifiers=frozenset({
            "expensive", "cost", "labor-intensive", "manual", "high",
            "time-consuming", "overhead", "demanding",
        }),
        trigger_phrases=(
            "annotation cost", "manual annotation", "labor intensive",
            "human labeling", "expensive curation", "labeling overhead",
        ),
    ),
    SemanticLimitationCategory(
        category_id="evaluation_benchmark",
        canonical_description="Narrow evaluation scope and simplified benchmark settings",
        core_concepts=frozenset({
            "evaluation", "benchmark", "benchmarks", "metric", "metrics",
            "testbed", "ground truth",
        }),
        qualifiers=frozenset({
            "limited", "synthetic", "narrow", "flawed", "insufficient",
            "unrealistic", "simplified", "restricted",
        }),
        trigger_phrases=(
            "synthetic benchmarks", "narrow evaluation", "simplified setting",
            "limited benchmark", "unrealistic evaluation",
        ),
    ),
    SemanticLimitationCategory(
        category_id="sensitivity_instability",
        canonical_description="High sensitivity to hyperparameters, prompts, or input noise",
        core_concepts=frozenset({
            "hyperparameter", "hyperparameters", "prompt", "prompting", "noise",
            "perturbation", "perturbations", "stability",
        }),
        qualifiers=frozenset({
            "sensitive", "sensitivity", "brittle", "unstable", "fragile",
            "variance", "instability", "high",
        }),
        trigger_phrases=(
            "hyperparameter sensitivity", "prompt brittleness", "sensitive to noise",
            "unstable training", "brittle prompts",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Extraction & text normalization helpers
# ---------------------------------------------------------------------------

def _get_field(paper: Any, *keys: str, default: Any = None) -> Any:
    """Retrieve field value from dict or object by testing candidate keys."""
    if isinstance(paper, dict):
        for k in keys:
            if k in paper and paper[k] is not None:
                return paper[k]
    else:
        for k in keys:
            if hasattr(paper, k):
                val = getattr(paper, k)
                if val is not None:
                    return val
    return default


def _extract_claim_text(item: Any) -> str:
    """Extract string text from a GroundedClaim, dict, string, or generic object."""
    if item is None:
        return ""
    if isinstance(item, str):
        return item.strip()
    claim = getattr(item, "claim", None)
    if claim is not None and not callable(claim):
        return str(claim).strip()
    text = getattr(item, "text", None)
    if text is not None and not callable(text):
        return str(text).strip()
    if isinstance(item, dict):
        desc = (
            item.get("claim")
            or item.get("text")
            or item.get("description")
            or item.get("name")
            or item.get("title")
        )
        if desc is not None:
            return str(desc).strip()
    return str(item).strip()


def _to_string_list(val: Any) -> list[str]:
    """Convert any value to a clean, non-empty list of strings."""
    if val is None:
        return []
    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return []
        if "\n" in cleaned:
            lines = [line.strip().lstrip("-*•0123456789. ") for line in cleaned.split("\n")]
            return [line for line in lines if line]
        if ";" in cleaned:
            parts = [part.strip() for part in cleaned.split(";")]
            return [part for part in parts if part]
        return [cleaned]
    if isinstance(val, (list, tuple, set)):
        result: list[str] = []
        for item in val:
            if item is None:
                continue
            s = _extract_claim_text(item)
            if s:
                result.append(s)
        return result
    s = _extract_claim_text(val)
    return [s] if s else []


def _extract_paper_limitations(paper: Any, idx: int) -> tuple[str, list[str]]:
    """Extract paper_id and list of raw limitations from an input paper."""
    if isinstance(paper, str):
        pid = paper.strip() or f"paper_{idx + 1}"
        return pid, []

    raw_id = _get_field(paper, "paper_id", "id", "paperId")
    title = str(_get_field(paper, "title", "paper_title", "name", default="") or "").strip()

    if raw_id is not None and str(raw_id).strip():
        paper_id = str(raw_id).strip()
    elif title:
        paper_id = title
    else:
        paper_id = f"paper_{idx + 1}"

    limitations = _to_string_list(
        _get_field(paper, "limitations", "limitation", "weaknesses", "weakness", "challenges", "challenge", "caveats")
    )

    return paper_id, limitations


def _normalize_text(text: str) -> str:
    """Lowercase and strip non-alphanumeric punctuation."""
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    return " ".join(cleaned.split())


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", text.lower())


def _content_tokens(text: str) -> set[str]:
    """Extract significant content tokens (non-stopwords, length >= 3)."""
    return {
        t for t in _tokenize(text)
        if len(t) >= 3 and t not in STOP_WORDS and not t.isdigit()
    }


# ---------------------------------------------------------------------------
# Clustering & Recurring limitation detection logic
# ---------------------------------------------------------------------------

@dataclass
class _LimitationCluster:
    cluster_id: str
    description: str
    paper_ids: set[str]
    evidence: list[str]


def _match_semantic_category(norm_text: str, tokens: set[str]) -> SemanticLimitationCategory | None:
    """Test whether a limitation matches a predefined semantic category."""
    for category in SEMANTIC_CATEGORIES:
        # 1. Exact trigger phrase match
        for phrase in category.trigger_phrases:
            if phrase in norm_text:
                return category

        # 2. Concept + Qualifier token co-occurrence
        has_core = bool(tokens.intersection(category.core_concepts))
        has_qualifier = bool(tokens.intersection(category.qualifiers))
        if has_core and has_qualifier:
            return category

    return None


def _is_dynamic_match(tokens1: set[str], tokens2: set[str], text1: str, text2: str) -> bool:
    """Check if two custom limitation statements represent the same concept.

    Strict rule: must share at least 2 content tokens with high overlap ratio.
    Never merges merely because they share a single word.
    """
    if text1 == text2:
        return True

    shared = tokens1.intersection(tokens2)
    if len(shared) < 2:
        return False

    min_len = min(len(tokens1), len(tokens2))
    if min_len == 0:
        return False

    overlap_ratio = len(shared) / min_len
    jaccard = len(shared) / len(tokens1.union(tokens2))

    return overlap_ratio >= 0.6 or jaccard >= 0.5


def _estimate_severity(frequency: int, evidence: list[str]) -> str:
    """Estimate limitation severity based on cross-paper frequency and impact keywords."""
    joined = " ".join(evidence).lower()
    critical_terms = ("critical", "severe", "prohibitive", "fails", "unusable", "bottleneck", "degraded")

    if frequency >= 3 or any(term in joined for term in critical_terms):
        return "high"
    if frequency >= 2:
        return "medium"
    return "low"


def _clean_title(text: str) -> str:
    """Convert raw limitation text into a clean description title."""
    s = text.strip()
    if s:
        return s[0].upper() + s[1:]
    return s


# ---------------------------------------------------------------------------
# Public limitations extraction entry point
# ---------------------------------------------------------------------------

def find_recurring_limitations(papers: list[Any]) -> list[RecurringLimitation]:
    """Identify limitations that appear across multiple papers.

    Parameters
    ----------
    papers:
        A list of paper-analysis objects (Pydantic models, dicts, or generic objects).

    Returns
    -------
    list[RecurringLimitation]
        Limitations observed in at least two papers, ranked by frequency.
    """
    if not papers:
        return []

    # Map cluster_id -> _LimitationCluster
    semantic_clusters: dict[str, _LimitationCluster] = {}
    dynamic_clusters: list[_LimitationCluster] = []

    for idx, paper in enumerate(papers):
        paper_id, raw_limitations = _extract_paper_limitations(paper, idx)

        for raw_lim in raw_limitations:
            norm_text = _normalize_text(raw_lim)
            if not norm_text:
                continue

            tokens = _content_tokens(norm_text)
            evidence_entry = f"[{paper_id}] {raw_lim}"

            # Step 1: Match against canonical semantic categories
            matched_category = _match_semantic_category(norm_text, tokens)
            if matched_category is not None:
                cid = matched_category.category_id
                if cid not in semantic_clusters:
                    semantic_clusters[cid] = _LimitationCluster(
                        cluster_id=cid,
                        description=matched_category.canonical_description,
                        paper_ids=set(),
                        evidence=[],
                    )
                semantic_clusters[cid].paper_ids.add(paper_id)
                if evidence_entry not in semantic_clusters[cid].evidence:
                    semantic_clusters[cid].evidence.append(evidence_entry)
                continue

            # Step 2: Open-domain / Dynamic clustering for non-categorized limitations
            matched_dynamic: _LimitationCluster | None = None
            for d_cluster in dynamic_clusters:
                d_tokens = _content_tokens(_normalize_text(d_cluster.description))
                d_norm = _normalize_text(d_cluster.description)
                if _is_dynamic_match(tokens, d_tokens, norm_text, d_norm):
                    matched_dynamic = d_cluster
                    break

            if matched_dynamic is not None:
                matched_dynamic.paper_ids.add(paper_id)
                if evidence_entry not in matched_dynamic.evidence:
                    matched_dynamic.evidence.append(evidence_entry)
            else:
                new_dyn = _LimitationCluster(
                    cluster_id=f"dyn_{len(dynamic_clusters)}",
                    description=_clean_title(raw_lim),
                    paper_ids={paper_id},
                    evidence=[evidence_entry],
                )
                dynamic_clusters.append(new_dyn)

    # Combine all candidate clusters
    all_clusters = list(semantic_clusters.values()) + dynamic_clusters

    # Filter for recurring limitations: MUST appear in at least 2 distinct papers
    recurring: list[RecurringLimitation] = []
    for cluster in all_clusters:
        if len(cluster.paper_ids) >= 2:
            sorted_paper_ids = sorted(cluster.paper_ids)
            sorted_evidence = sorted(cluster.evidence)
            freq = len(sorted_paper_ids)
            sev = _estimate_severity(freq, sorted_evidence)

            # Deterministic limitation ID
            lim_id = uuid5(NAMESPACE_DNS, f"limitation:{cluster.description}:{','.join(sorted_paper_ids)}").hex

            recurring.append(
                RecurringLimitation(
                    limitation_id=lim_id,
                    description=cluster.description,
                    paper_ids=sorted_paper_ids,
                    frequency=freq,
                    severity=sev,
                    evidence=sorted_evidence,
                )
            )

    # Deterministic ranking: frequency descending, then description ascending
    recurring.sort(key=lambda r: (-r.frequency, r.description))

    return recurring
