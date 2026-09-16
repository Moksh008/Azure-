"""M4 — Paper comparison component.

Accepts a collection of paper-analysis objects and produces a PaperComparison
summarising shared themes, methodological overlaps and differences, dataset
comparisons, key findings, common limitations, points of agreement, and
areas of difference or contradiction.

Operates deterministically and locally without LLM or external API calls.
Flexible across Pydantic models, plain objects, and dictionaries.

Responsible AI constraint:
This component is responsible solely for structured comparison. It does NOT
claim that a research gap or novelty has been discovered.
"""

from __future__ import annotations

import re
from typing import Any

from backend.app.research_intelligence.models import PaperComparison

# Common English stop words and academic filler words
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
    # Academic and publication boilerplate terms
    "paper", "study", "research", "work", "approach", "method", "results",
    "proposed", "using", "presents", "show", "shows", "shown", "based",
    "use", "used", "evaluates", "investigates", "via", "towards", "within",
    "also", "well", "one", "two", "three", "first", "second", "new",
    "demonstrate", "demonstrates", "demonstrated", "present", "presented",
    "provides", "provide", "provided", "article", "author", "authors",
    "evaluation", "analysis", "experiments", "experiment", "experimental",
    "however", "furthermore", "moreover", "respectively", "aims", "aim",
})

# Common recurring limitation concepts for structured recognition
KNOWN_LIMITATION_CONCEPTS: tuple[str, ...] = (
    "sample size",
    "dataset size",
    "computational cost",
    "compute overhead",
    "memory overhead",
    "latency",
    "scalability",
    "generalization",
    "data scarcity",
    "annotation cost",
    "hardware requirements",
    "bias",
    "hallucination",
    "domain shift",
    "interpretability",
    "robustness",
)

# Directional/polarity word pairs for contradiction detection
CONTRADICTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("improved", "degraded"),
    ("increase", "decrease"),
    ("increased", "decreased"),
    ("higher", "lower"),
    ("faster", "slower"),
    ("effective", "ineffective"),
    ("positive", "negative"),
    ("outperformed", "underperformed"),
    ("robust", "fragile"),
    ("scalable", "unscalable"),
    ("reduces", "increases"),
    ("reduced", "increased"),
)


# ---------------------------------------------------------------------------
# Data extraction & normalization helpers
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
            if isinstance(item, str):
                s = item.strip()
                if s:
                    result.append(s)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("title") or str(item)
                s = str(name).strip()
                if s:
                    result.append(s)
            elif item is not None:
                s = str(item).strip()
                if s:
                    result.append(s)
        return result
    s = str(val).strip()
    return [s] if s else []


def _normalize_dataset_list(val: Any) -> list[str]:
    """Extract dataset names, splitting comma-separated lists when appropriate."""
    items = _to_string_list(val)
    normalized: list[str] = []
    for item in items:
        # Split on commas if it looks like a list rather than a full sentence
        if "," in item and not any(punct in item for punct in (". ", "?", "!")):
            subparts = [p.strip() for p in item.split(",") if p.strip()]
            normalized.extend(subparts)
        else:
            normalized.append(item)
    return normalized


def _extract_paper_record(paper: Any, idx: int) -> dict[str, Any]:
    """Extract normalized attributes from a paper object, dict, or primitive."""
    if isinstance(paper, str):
        paper_id = paper.strip() or f"paper_{idx + 1}"
        return {
            "paper_id": paper_id,
            "title": paper_id,
            "authors": [],
            "abstract": "",
            "research_question": "",
            "methodology": [],
            "datasets": [],
            "key_findings": [],
            "limitations": [],
        }

    # Extract paper_id
    raw_id = _get_field(paper, "paper_id", "id", "paperId")
    title = str(_get_field(paper, "title", "paper_title", "name", default="") or "").strip()

    if raw_id is not None and str(raw_id).strip():
        paper_id = str(raw_id).strip()
    elif title:
        paper_id = title
    else:
        paper_id = f"paper_{idx + 1}"

    authors = _to_string_list(_get_field(paper, "authors", "author_list", "author"))
    abstract = str(_get_field(paper, "abstract", "summary", "description", default="") or "").strip()
    research_question = str(
        _get_field(paper, "research_question", "research_questions", "problem_statement", "problem", default="") or ""
    ).strip()
    methodology = _to_string_list(_get_field(paper, "methodology", "method", "methods", "approach", "techniques"))
    datasets = _normalize_dataset_list(_get_field(paper, "datasets", "dataset", "data", "benchmarks"))
    key_findings = _to_string_list(_get_field(paper, "key_findings", "findings", "results", "conclusions"))
    limitations = _to_string_list(_get_field(paper, "limitations", "limitation", "weaknesses", "challenges"))

    return {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "research_question": research_question,
        "methodology": methodology,
        "datasets": datasets,
        "key_findings": key_findings,
        "limitations": limitations,
    }


# ---------------------------------------------------------------------------
# Text processing & theme detection helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return [token for token in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", text.lower())]


def _extract_acronyms(text: str) -> list[str]:
    """Extract uppercase acronyms or technical names (e.g. NLP, RAG, LoRA, SQuAD)."""
    # Pattern matches standard acronyms like NLP, LLM, or mixed cases like LoRA, SQuAD
    matches = re.findall(r"\b(?:[A-Z]{2,}(?:-[A-Z0-9]+)?|[A-Z]+[a-z]+[A-Z]+)\b", text)
    return [m for m in matches if m.lower() not in STOP_WORDS]


def _extract_candidate_terms(text: str) -> dict[str, str]:
    """Extract normalized terms mapped to preferred display format."""
    terms: dict[str, str] = {}

    # Acronyms (preserved in their original casing)
    for acr in _extract_acronyms(text):
        terms[acr.lower()] = acr

    tokens = _tokenize(text)

    # Single meaningful words
    for token in tokens:
        if len(token) >= 3 and token not in STOP_WORDS and not token.isdigit():
            if token not in terms:
                terms[token] = token.capitalize()

    # Meaningful bigrams
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i + 1]
        if (
            len(w1) >= 3
            and len(w2) >= 3
            and w1 not in STOP_WORDS
            and w2 not in STOP_WORDS
            and not w1.isdigit()
            and not w2.isdigit()
        ):
            bigram_key = f"{w1} {w2}"
            if bigram_key not in terms:
                terms[bigram_key] = f"{w1.capitalize()} {w2.capitalize()}"

    return terms


def _find_shared_themes(records: list[dict[str, Any]]) -> list[str]:
    """Identify meaningful themes appearing across multiple papers."""
    paper_terms: list[dict[str, str]] = []

    for r in records:
        combined_text = " ".join([
            r["title"],
            r["abstract"],
            r["research_question"],
            " ".join(r["key_findings"]),
        ])
        paper_terms.append(_extract_candidate_terms(combined_text))

    # Track presence in each paper
    term_counts: dict[str, set[str]] = {}
    term_displays: dict[str, str] = {}

    for idx, terms_dict in enumerate(paper_terms):
        paper_id = records[idx]["paper_id"]
        for norm_key, display in terms_dict.items():
            term_counts.setdefault(norm_key, set()).add(paper_id)
            # Prefer acronym display over lower/capitalized
            if norm_key not in term_displays or display.isupper():
                term_displays[norm_key] = display

    # Filter terms appearing in >= 2 papers
    shared = [
        norm_key
        for norm_key, paper_set in term_counts.items()
        if len(paper_set) >= 2
    ]

    # Sort deterministically: frequency descending, length descending, key ascending
    shared.sort(key=lambda k: (-len(term_counts[k]), -len(k), k))

    # De-duplicate single words that are already subsumed by an accepted multi-word theme
    final_themes: list[str] = []
    accepted_keys: list[str] = []

    for k in shared:
        # Check if single word is already contained in an accepted bigram with >= count
        is_redundant = any(
            " " in acc and k in acc.split() and len(term_counts[k]) <= len(term_counts[acc])
            for acc in accepted_keys
        )
        if not is_redundant:
            accepted_keys.append(k)
            final_themes.append(term_displays[k])

    return final_themes[:10]


# ---------------------------------------------------------------------------
# Methodology comparison helpers
# ---------------------------------------------------------------------------

def _compare_methodology(records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Identify methodological overlaps and differences across papers."""
    overlaps: list[str] = []
    differences: list[str] = []

    # Map normalized method item / term -> set of paper_ids and display form
    method_item_map: dict[str, set[str]] = {}
    method_item_display: dict[str, str] = {}

    term_map: dict[str, set[str]] = {}
    term_display: dict[str, str] = {}

    for r in records:
        pid = r["paper_id"]
        for method_item in r["methodology"]:
            norm_item = method_item.strip().lower()
            if norm_item:
                method_item_map.setdefault(norm_item, set()).add(pid)
                method_item_display.setdefault(norm_item, method_item.strip())

            # Also extract keywords/acronyms from methodology descriptions
            terms = _extract_candidate_terms(method_item)
            for k, disp in terms.items():
                term_map.setdefault(k, set()).add(pid)
                if k not in term_display or disp.isupper():
                    term_display[k] = disp

    # Find full items that appear across >= 2 papers
    shared_items: set[str] = set()
    for norm_item, pids in sorted(method_item_map.items()):
        if len(pids) >= 2:
            display = method_item_display[norm_item]
            overlaps.append(display)
            shared_items.add(norm_item)

    # Find method concepts/keywords that appear across >= 2 papers
    for k, pids in sorted(term_map.items(), key=lambda x: (-len(x[1]), x[0])):
        if len(pids) >= 2:
            display = term_display[k]
            # Avoid duplicating full items already captured
            if not any(display.lower() == item.lower() for item in overlaps):
                # Only include significant methodology terms
                if len(k) >= 4 or display.isupper():
                    overlaps.append(display)

    # Methodological differences: unique methods per paper
    for r in records:
        pid = r["paper_id"]
        for method_item in r["methodology"]:
            norm_item = method_item.strip().lower()
            if norm_item not in shared_items:
                differences.append(f"[{pid}] {method_item.strip()}")

    # Ensure unique and deterministically sorted
    seen_overlaps: set[str] = set()
    unique_overlaps: list[str] = []
    for item in overlaps:
        if item.lower() not in seen_overlaps:
            seen_overlaps.add(item.lower())
            unique_overlaps.append(item)

    return sorted(unique_overlaps), sorted(differences)


# ---------------------------------------------------------------------------
# Dataset comparison helpers
# ---------------------------------------------------------------------------

def _compare_datasets(records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Compare dataset usage across papers, returning shared and unique datasets."""
    dataset_map: dict[str, set[str]] = {}
    dataset_display: dict[str, str] = {}

    for r in records:
        pid = r["paper_id"]
        for ds in r["datasets"]:
            norm_ds = ds.strip().lower()
            if norm_ds:
                dataset_map.setdefault(norm_ds, set()).add(pid)
                if norm_ds not in dataset_display:
                    dataset_display[norm_ds] = ds.strip()

    shared: list[str] = []
    differences: list[str] = []

    for norm_ds, pids in dataset_map.items():
        display = dataset_display[norm_ds]
        if len(pids) >= 2:
            shared.append(display)
        else:
            only_pid = next(iter(pids))
            differences.append(f"[{only_pid}] {display}")

    return sorted(shared), sorted(differences)


# ---------------------------------------------------------------------------
# Key findings & contradictions helpers
# ---------------------------------------------------------------------------

def _compare_findings(records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Preserve findings from each paper and detect obvious opposing claims."""
    key_findings: list[str] = []
    contradictions: list[str] = []

    for r in records:
        pid = r["paper_id"]
        for finding in r["key_findings"]:
            key_findings.append(f"[{pid}] {finding}")

    # Check for direct contradictions on shared topics with opposing keywords
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            r1, r2 = records[i], records[j]
            for f1 in r1["key_findings"]:
                f1_lower = f1.lower()
                for f2 in r2["key_findings"]:
                    f2_lower = f2.lower()
                    # Check for opposing indicators on shared nouns/topics
                    for w_pos, w_neg in CONTRADICTION_PAIRS:
                        has_pos_1 = w_pos in f1_lower
                        has_neg_2 = w_neg in f2_lower
                        has_neg_1 = w_neg in f1_lower
                        has_pos_2 = w_pos in f2_lower

                        if (has_pos_1 and has_neg_2) or (has_neg_1 and has_pos_2):
                            # Verify if there is a shared topical keyword
                            t1 = set(_tokenize(f1)) - STOP_WORDS
                            t2 = set(_tokenize(f2)) - STOP_WORDS
                            shared_topic = t1.intersection(t2) - {w_pos, w_neg}
                            if shared_topic:
                                topic = sorted(shared_topic)[0]
                                contradiction_msg = (
                                    f"Contradiction on '{topic}' between [{r1['paper_id']}] and [{r2['paper_id']}]: "
                                    f"'{f1}' vs '{f2}'"
                                )
                                if contradiction_msg not in contradictions:
                                    contradictions.append(contradiction_msg)

    return sorted(key_findings), sorted(contradictions)


# ---------------------------------------------------------------------------
# Limitations comparison helpers
# ---------------------------------------------------------------------------

def _compare_limitations(records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Preserve limitations from all papers and identify common limitation concepts."""
    all_limitations: list[str] = []
    common_limitations: list[str] = []

    limitation_map: dict[str, set[str]] = {}
    limitation_display: dict[str, str] = {}

    concept_map: dict[str, set[str]] = {}

    for r in records:
        pid = r["paper_id"]
        for lim in r["limitations"]:
            all_limitations.append(f"[{pid}] {lim}")
            norm_lim = lim.strip().lower()
            if norm_lim:
                limitation_map.setdefault(norm_lim, set()).add(pid)
                limitation_display.setdefault(norm_lim, lim.strip())

            # Check known limitation concepts
            for concept in KNOWN_LIMITATION_CONCEPTS:
                if concept in norm_lim:
                    concept_map.setdefault(concept, set()).add(pid)

    # Limitations with exact / near-exact text match across >= 2 papers
    for norm_lim, pids in limitation_map.items():
        if len(pids) >= 2:
            common_limitations.append(limitation_display[norm_lim])

    # Limitations sharing known recurring concepts across >= 2 papers
    for concept, pids in concept_map.items():
        if len(pids) >= 2:
            desc = f"Shared limitation: {concept}"
            if desc not in common_limitations:
                common_limitations.append(desc)

    return sorted(common_limitations), sorted(all_limitations)


# ---------------------------------------------------------------------------
# Agreements & differences synthesis
# ---------------------------------------------------------------------------

def _derive_agreements_and_differences(
    shared_themes: list[str],
    methodological_overlaps: list[str],
    methodological_differences: list[str],
    shared_datasets: list[str],
    dataset_differences: list[str],
    common_limitations: list[str],
    contradictions: list[str],
) -> tuple[list[str], list[str]]:
    """Synthesize high-level consensus areas and differences across papers."""
    agreements: list[str] = []
    differences: list[str] = []

    # Agreements
    if shared_themes:
        agreements.append(f"Common focus: {', '.join(shared_themes[:3])}")
    for method in methodological_overlaps[:3]:
        agreements.append(f"Shared methodology: {method}")
    for ds in shared_datasets[:3]:
        agreements.append(f"Shared dataset benchmark: {ds}")
    for lim in common_limitations[:3]:
        agreements.append(f"Agreed limitation: {lim}")

    # Differences
    for diff_m in methodological_differences[:4]:
        differences.append(f"Methodology divergence: {diff_m}")
    for diff_ds in dataset_differences[:4]:
        differences.append(f"Dataset divergence: {diff_ds}")
    for c in contradictions:
        differences.append(c)

    return sorted(agreements), sorted(differences)


# ---------------------------------------------------------------------------
# Public comparison entry point
# ---------------------------------------------------------------------------

def compare_papers(papers: list[Any]) -> PaperComparison:
    """Compare a collection of paper analyses and return a structured PaperComparison.

    Parameters
    ----------
    papers:
        A list of paper-analysis objects (Pydantic models, dicts, or generic objects).
        At least two papers are required.

    Returns
    -------
    PaperComparison
        Structured comparison containing shared themes, methodology overlaps and
        differences, dataset comparisons, preserved findings, limitations,
        agreements, differences, and contradictions.

    Raises
    ------
    ValueError
        If fewer than two papers are provided.
    """
    if papers is None or len(papers) < 2:
        raise ValueError("At least two paper analyses are required for comparison.")

    records = [_extract_paper_record(p, idx) for idx, p in enumerate(papers)]
    paper_ids = [r["paper_id"] for r in records]

    shared_themes = _find_shared_themes(records)
    method_overlaps, method_diffs = _compare_methodology(records)
    shared_datasets, dataset_diffs = _compare_datasets(records)
    key_findings, contradictions = _compare_findings(records)
    common_limitations, all_limitations = _compare_limitations(records)

    agreements, differences = _derive_agreements_and_differences(
        shared_themes=shared_themes,
        methodological_overlaps=method_overlaps,
        methodological_differences=method_diffs,
        shared_datasets=shared_datasets,
        dataset_differences=dataset_diffs,
        common_limitations=common_limitations,
        contradictions=contradictions,
    )

    return PaperComparison(
        paper_ids=paper_ids,
        shared_themes=shared_themes,
        methodological_overlaps=method_overlaps,
        methodological_differences=method_diffs,
        shared_datasets=shared_datasets,
        dataset_differences=dataset_diffs,
        key_findings=key_findings,
        common_limitations=common_limitations,
        all_limitations=all_limitations,
        agreements=agreements,
        differences=differences,
        contradictions=contradictions,
    )
