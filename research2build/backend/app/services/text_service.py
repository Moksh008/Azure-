"""Text normalization and section/heading detection for extracted PDF text."""

from __future__ import annotations

import re

# Canonical section names this heuristic recognizes. Extend as new paper
# layouts show up in testing rather than trying to cover every case upfront.
KNOWN_SECTIONS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "motivation",
    "problem statement",
    "method",
    "methods",
    "methodology",
    "approach",
    "system design",
    "implementation",
    "experiments",
    "experimental setup",
    "evaluation",
    "results",
    "discussion",
    "limitations",
    "future work",
    "conclusion",
    "conclusions",
    "acknowledgments",
    "acknowledgements",
    "references",
    "appendix",
}

_LEADING_NUMBERING_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)*[\.\)]?|[IVXLC]+[\.\)])\s+")
_HYPHEN_LINEBREAK_RE = re.compile(r"(\w)-\n\s*(\w)")
_SOFT_LINEBREAK_RE = re.compile(r"[ \t]*\n[ \t]*")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")


def detect_heading(line: str) -> str | None:
    """Return the canonical section name if `line` looks like a section heading."""
    stripped = line.strip()
    if not stripped or len(stripped) > 80:
        return None

    core = _LEADING_NUMBERING_RE.sub("", stripped).strip().rstrip(":").strip()
    if not core:
        return None

    if core.lower() in KNOWN_SECTIONS:
        return core if core.isupper() and len(core) <= 4 else core.title()

    return None


def normalize_text(text: str) -> str:
    """Collapse PDF-extraction line noise into clean paragraph text.

    Rejoins hyphen-broken words across line wraps, folds single line breaks
    (mid-paragraph wraps) into spaces, and preserves paragraph breaks.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)

    paragraph_break = " "
    text = re.sub(r"\n{2,}", paragraph_break, text)
    text = _SOFT_LINEBREAK_RE.sub(" ", text)
    text = text.replace(paragraph_break, "\n\n")

    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()
