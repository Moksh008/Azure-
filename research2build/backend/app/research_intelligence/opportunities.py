"""M4 — Research-opportunity generation component.

Transforms recurring limitations identified across multiple research papers
into structured Potential Research Opportunities.

Operates deterministically and locally without LLM or external dependencies.
Flexible across RecurringLimitation objects, plain objects, and dictionaries.

Responsible AI constraints:
- Generated items represent POTENTIAL research directions only.
- Does NOT claim that a research gap or novelty has been discovered.
- Uses exact novelty_confidence = "Requires human validation".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from backend.app.research_intelligence.models import (
    RecurringLimitation,
    ResearchOpportunity,
)

# Standard English stop words for keyword extraction from custom limitations
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
    # Boilerplate academic fillers
    "model", "models", "approach", "method", "paper", "study", "system", "systems",
    "results", "observed", "reported", "due", "primarily", "current",
})


@dataclass(frozen=True)
class OpportunityTemplate:
    """Template mapping limitation patterns to structured research opportunities."""

    category_id: str
    trigger_keywords: frozenset[str]
    title: str
    description: str
    keywords: tuple[str, ...]


OPPORTUNITY_TEMPLATES: tuple[OpportunityTemplate, ...] = (
    OpportunityTemplate(
        category_id="data_efficiency",
        trigger_keywords=frozenset({
            "data", "dataset", "datasets", "sample", "samples", "scarcity",
            "few-shot", "examples", "corpus", "corpora", "labeled",
        }),
        title="Data-Efficient Learning and Synthetic Augmentation",
        description=(
            "Investigate data-efficient, semi-supervised, or synthetic data augmentation "
            "techniques to alleviate dependence on large labeled training datasets."
        ),
        keywords=(
            "data efficiency", "semi-supervised learning", "synthetic data",
            "data augmentation", "few-shot learning",
        ),
    ),
    OpportunityTemplate(
        category_id="compute_optimization",
        trigger_keywords=frozenset({
            "compute", "computational", "gpu", "gpus", "hardware", "memory",
            "flops", "footprint", "vram", "ram",
        }),
        title="Model Compression and Compute-Efficient Optimization",
        description=(
            "Explore model pruning, quantization, parameter-efficient fine-tuning (PEFT), "
            "and knowledge distillation to reduce compute overhead and hardware requirements."
        ),
        keywords=(
            "model compression", "quantization", "PEFT", "knowledge distillation",
            "efficient inference",
        ),
    ),
    OpportunityTemplate(
        category_id="latency_acceleration",
        trigger_keywords=frozenset({
            "latency", "inference", "runtime", "speed", "throughput", "delay",
            "response time", "lag",
        }),
        title="Low-Latency Inference Acceleration and Caching",
        description=(
            "Investigate speculative decoding, KV-cache compression, and architectural "
            "streamlining to minimize inference latency in interactive environments."
        ),
        keywords=(
            "latency reduction", "inference acceleration", "speculative decoding",
            "caching", "throughput optimization",
        ),
    ),
    OpportunityTemplate(
        category_id="scalability",
        trigger_keywords=frozenset({
            "scalability", "scale", "scaling", "large-scale", "unscalable",
        }),
        title="Distributed Scaling and Sub-Quadratic Architectures",
        description=(
            "Explore distributed scaling strategies, hierarchical routing, or "
            "sub-quadratic sequence architectures to overcome scaling bottlenecks on large workloads."
        ),
        keywords=(
            "scalability", "distributed systems", "hierarchical architectures",
            "throughput", "large-scale computing",
        ),
    ),
    OpportunityTemplate(
        category_id="domain_generalization",
        trigger_keywords=frozenset({
            "generalization", "generalize", "domain", "transfer", "transferability",
            "out-of-distribution", "ood", "unseen", "cross-domain",
        }),
        title="Domain-Robust Representations and Adaptive Transfer",
        description=(
            "Investigate domain-adversarial training, invariant representation learning, "
            "and test-time adaptation to enhance out-of-distribution robustness and cross-domain transfer."
        ),
        keywords=(
            "domain adaptation", "out-of-distribution robustness", "invariant representations",
            "generalization", "transfer learning",
        ),
    ),
    OpportunityTemplate(
        category_id="hallucination_mitigation",
        trigger_keywords=frozenset({
            "hallucination", "hallucinations", "factuality", "factual",
            "faithfulness", "grounding", "confabulation",
        }),
        title="Grounded Factuality and Verification Mechanisms",
        description=(
            "Explore external knowledge retrieval verification, citation-enforced decoding, "
            "and self-consistency checking to mitigate factual hallucinations."
        ),
        keywords=(
            "factuality verification", "hallucination mitigation", "evidence grounding",
            "citation verification", "consistency",
        ),
    ),
    OpportunityTemplate(
        category_id="bias_fairness",
        trigger_keywords=frozenset({
            "bias", "biases", "demographic", "diversity", "representation",
            "fairness", "skew", "skewed",
        }),
        title="Balanced Benchmarking and Algorithmic Debiasing",
        description=(
            "Explore fairness-aware reweighting, counterfactual evaluation, and "
            "inclusive curation pipelines to address dataset bias and improve demographic diversity."
        ),
        keywords=(
            "fairness", "algorithmic debiasing", "counterfactual evaluation",
            "inclusive curation", "representation",
        ),
    ),
    OpportunityTemplate(
        category_id="interpretability",
        trigger_keywords=frozenset({
            "interpretability", "explainability", "black-box", "transparency",
            "interpretable", "explainable",
        }),
        title="Interpretable Architectures and Mechanistic Explainability",
        description=(
            "Investigate concept attribution, mechanistic interpretability, and "
            "post-hoc rationalization to provide transparent and verifiable reasoning paths."
        ),
        keywords=(
            "interpretability", "explainable AI", "feature attribution",
            "transparency", "rationalization",
        ),
    ),
    OpportunityTemplate(
        category_id="annotation_efficiency",
        trigger_keywords=frozenset({
            "annotation", "labeling", "annotators", "feedback", "rlhf", "curation",
        }),
        title="Active Learning and Weak Supervision Pipelines",
        description=(
            "Explore active learning, programmatic weak supervision, and self-training "
            "heuristics to significantly reduce manual labeling and curation overhead."
        ),
        keywords=(
            "active learning", "weak supervision", "pseudo-labeling",
            "annotation efficiency", "human-in-the-loop",
        ),
    ),
    OpportunityTemplate(
        category_id="evaluation_frameworks",
        trigger_keywords=frozenset({
            "benchmark", "benchmarks", "metric", "metrics", "testbed",
            "ground truth", "evaluation",
        }),
        title="Ecological Validity and Real-World Evaluation Frameworks",
        description=(
            "Develop holistic stress-testing testbeds, dynamic benchmark protocols, and "
            "ecological validity suites to move beyond narrow synthetic evaluation."
        ),
        keywords=(
            "benchmark design", "stress testing", "real-world evaluation",
            "robustness metrics", "ecological validity",
        ),
    ),
    OpportunityTemplate(
        category_id="sensitivity_robustness",
        trigger_keywords=frozenset({
            "hyperparameter", "hyperparameters", "prompt", "prompting", "noise",
            "perturbation", "perturbations", "stability", "brittle", "sensitivity",
        }),
        title="Robust Optimization and Sensitivity Minimization",
        description=(
            "Explore sharpness-aware minimization, prompt ensemble distillation, and "
            "noise-resilient training objectives to stabilize model performance against parameter perturbations."
        ),
        keywords=(
            "robust optimization", "noise resilience", "prompt robustness",
            "stability", "sensitivity analysis",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tokens(text: str) -> set[str]:
    """Extract lowercase alphanumeric tokens."""
    return set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", text.lower()))


def _extract_content_keywords(text: str) -> list[str]:
    """Extract significant non-stopword tokens from custom limitations."""
    tokens = _extract_tokens(text)
    keywords = [t for t in tokens if len(t) >= 3 and t not in STOP_WORDS and not t.isdigit()]
    return sorted(keywords)


def _clean_title(text: str) -> str:
    """Format raw text into a clean Title Case string."""
    cleaned = re.sub(r"[^\w\s-]", " ", text)
    words = cleaned.split()
    return " ".join(w.capitalize() for w in words)


def _match_template(description: str) -> OpportunityTemplate | None:
    """Find the best matching opportunity template for a limitation description."""
    tokens = _extract_tokens(description)
    desc_lower = description.lower()

    # Exact phrase or strong keyword match
    for template in OPPORTUNITY_TEMPLATES:
        # Check intersection with trigger keywords
        overlap = tokens.intersection(template.trigger_keywords)
        if len(overlap) >= 2 or any(kw in desc_lower for kw in template.trigger_keywords if " " in kw):
            return template

    # Fallback to single strong keyword if unique match
    for template in OPPORTUNITY_TEMPLATES:
        if bool(tokens.intersection(template.trigger_keywords)):
            return template

    return None


@dataclass
class _OpportunityDraft:
    category_key: str
    title: str
    description: str
    keywords: set[str]
    source_limitation_ids: set[str]
    paper_ids: set[str]
    evidence: set[str]


# ---------------------------------------------------------------------------
# Public Opportunity Generation Entry Point
# ---------------------------------------------------------------------------

def generate_opportunities(
    recurring_limitations: list[RecurringLimitation],
) -> list[ResearchOpportunity]:
    """Generate potential research opportunities from recurring limitations.

    Parameters
    ----------
    recurring_limitations:
        Limitations that appeared across multiple paper analyses.

    Returns
    -------
    list[ResearchOpportunity]
        Potential research directions. Each opportunity carries the
        ``novelty_confidence = "Requires human validation"`` disclaimer.
    """
    if not recurring_limitations:
        return []

    # Map category_key -> _OpportunityDraft for deterministic deduplication
    drafts: dict[str, _OpportunityDraft] = {}

    for idx, lim in enumerate(recurring_limitations):
        if lim is None:
            continue

        # Extract fields robustly whether Pydantic, dict, or object
        lim_id = getattr(lim, "limitation_id", None) or getattr(lim, "id", None)
        if isinstance(lim, dict):
            lim_id = lim.get("limitation_id") or lim.get("id")
            description = str(lim.get("description") or "").strip()
            paper_ids = list(lim.get("paper_ids") or [])
            evidence = list(lim.get("evidence") or [])
        else:
            description = str(getattr(lim, "description", "") or "").strip()
            paper_ids = list(getattr(lim, "paper_ids", []) or [])
            evidence = list(getattr(lim, "evidence", []) or [])

        if not lim_id:
            lim_id = f"lim_{idx + 1}"
        else:
            lim_id = str(lim_id)

        if not description:
            continue

        # Match template or generate domain-grounded fallback
        template = _match_template(description)

        if template is not None:
            cat_key = template.category_id
            title = template.title
            opp_description = template.description
            kw_set = set(template.keywords)
        else:
            # Domain-grounded fallback for unmapped recurring limitation
            cat_key = f"custom_{re.sub(r'[^a-zA-Z0-9_]', '_', description.lower()[:30])}"
            title = f"Targeted Exploration for {_clean_title(description)}"
            opp_description = (
                f"Investigate algorithmic enhancements and specialized adaptation strategies "
                f"to address the recurring limitation: '{description}'."
            )
            kw_set = set(_extract_content_keywords(description))
            if not kw_set:
                kw_set = {"targeted exploration", "adaptation"}

        # Deduplicate into drafts
        if cat_key not in drafts:
            drafts[cat_key] = _OpportunityDraft(
                category_key=cat_key,
                title=title,
                description=opp_description,
                keywords=set(kw_set),
                source_limitation_ids={lim_id},
                paper_ids=set(paper_ids),
                evidence=set(evidence),
            )
        else:
            existing = drafts[cat_key]
            existing.source_limitation_ids.add(lim_id)
            existing.paper_ids.update(paper_ids)
            existing.evidence.update(evidence)
            existing.keywords.update(kw_set)

    # Convert drafts into ResearchOpportunity objects
    opportunities: list[ResearchOpportunity] = []
    for draft in drafts.values():
        sorted_lim_ids = sorted(draft.source_limitation_ids)
        sorted_paper_ids = sorted(draft.paper_ids)
        sorted_evidence = sorted(draft.evidence)
        sorted_keywords = sorted(draft.keywords)

        # Deterministic UUID based on title and source limitation IDs
        opp_id = uuid5(NAMESPACE_DNS, f"opportunity:{draft.title}:{','.join(sorted_lim_ids)}").hex

        opportunities.append(
            ResearchOpportunity(
                opportunity_id=opp_id,
                title=draft.title,
                description=draft.description,
                source_limitation_ids=sorted_lim_ids,
                novelty_confidence="Requires human validation",
                keywords=sorted_keywords,
                paper_ids=sorted_paper_ids,
                evidence=sorted_evidence,
            )
        )

    # Deterministic sorting: most supporting papers first, then alphabetically by title
    opportunities.sort(key=lambda opp: (-len(opp.paper_ids), -len(opp.source_limitation_ids), opp.title))

    return opportunities
