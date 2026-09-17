"""Member 5 — Deliverables Engine.

Packages a validated ProjectProposal into two real developer assets:

1. A Research PRD (Product Requirements Document) synthesizing the
   Problem, Evidence, Potential Opportunity, Solution, Expected
   Contribution, Feasibility, and Roadmap.
2. An honest MVP starter scaffold — a clean repository skeleton with
   stubs, not a fake completed app.

Operates deterministically and locally, no LLM or external dependencies,
matching the ``project_generator.py`` / ``feasibility.py`` convention.

Responsible AI constraints (see CLAUDE.md):
- Never claims a research gap was "discovered"; opportunities are
  "inferred from recurring limitations" and require human validation.
- The PRD always carries the novelty disclaimer in its own text, not
  just as UI chrome around it.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from backend.app.agents.feasibility import FeasibilityAssessment
from backend.app.research_intelligence.models import (
    ProjectProposal,
    ResearchOpportunity,
)


# ---------------------------------------------------------------------------
# PRD generation
# ---------------------------------------------------------------------------

class PRDDocument(BaseModel):
    """A generated Product Requirements Document for a ProjectProposal."""

    proposal_id: str
    title: str
    problem_statement: str
    evidence: list[str] = Field(default_factory=list)
    opportunity_summary: str
    solution_summary: str
    expected_contribution: list[str] = Field(default_factory=list)
    feasibility_summary: str
    roadmap_summary: list[str] = Field(default_factory=list)
    novelty_confidence: str

    def to_markdown(self) -> str:
        """Render the PRD as a single Markdown document."""

        lines: list[str] = [
            f"# {self.title}",
            "",
            f"*Novelty confidence: {self.novelty_confidence}*",
            "",
            "## Problem",
            self.problem_statement or "_Not specified._",
            "",
            "## Evidence",
        ]
        if self.evidence:
            lines += [f"- {e}" for e in self.evidence]
        else:
            lines.append("_No supporting evidence excerpts were attached._")

        lines += [
            "",
            "## Potential Opportunity",
            self.opportunity_summary,
            "",
            "## Solution",
            self.solution_summary,
            "",
            "## Expected Contribution",
        ]
        lines += [f"- {c}" for c in self.expected_contribution] or ["_None specified._"]

        lines += [
            "",
            "## Feasibility",
            self.feasibility_summary,
            "",
            "## Roadmap",
        ]
        lines += [f"- {step}" for step in self.roadmap_summary] or ["_No roadmap attached._"]

        lines += [
            "",
            "---",
            (
                "This document was generated automatically from recurring limitations "
                "observed across the supplied papers. It does not claim to have "
                "discovered a research gap; all opportunity and novelty statements "
                f"require human validation ({self.novelty_confidence})."
            ),
        ]
        return "\n".join(lines) + "\n"


def _opportunity_summary(
    proposal: ProjectProposal,
    opportunity: ResearchOpportunity | None,
) -> str:
    if opportunity is not None:
        return (
            f"{opportunity.description} "
            f"(inferred from recurring limitations in the provided papers; "
            f"novelty confidence: {opportunity.novelty_confidence})."
        )
    if proposal.source_opportunity_ids:
        return (
            "This proposal is derived from potential research opportunity "
            f"{', '.join(proposal.source_opportunity_ids)}, inferred from recurring "
            "limitations in the provided papers."
        )
    return "No source opportunity was attached to this proposal."


def _feasibility_summary(
    proposal: ProjectProposal,
    feasibility: FeasibilityAssessment | None,
) -> tuple[str, list[str]]:
    if feasibility is not None:
        summary = (
            f"Feasibility: {feasibility.level} (score {feasibility.score}/100). "
            f"Estimated effort: {feasibility.estimated_effort_weeks} person-weeks. "
            f"Skill coverage: {feasibility.skill_coverage * 100:.0f}%."
        )
        if feasibility.risks:
            summary += " Risks: " + "; ".join(feasibility.risks)
        roadmap_lines = [
            f"{m.phase} (weeks {m.start_week}-{m.end_week}): "
            + ", ".join(m.deliverables)
            for m in feasibility.roadmap.milestones
        ]
        return summary, roadmap_lines

    summary = proposal.feasibility_notes or "Feasibility has not yet been scored."
    return summary, []


def generate_prd(
    proposal: ProjectProposal,
    opportunity: ResearchOpportunity | None = None,
    feasibility: FeasibilityAssessment | None = None,
) -> PRDDocument:
    """Synthesize a PRD from a ProjectProposal and its optional upstream context.

    ``opportunity`` and ``feasibility`` are optional so the PRD can be
    generated at any pipeline stage; when omitted, the PRD falls back to
    the fields already carried on the proposal itself.
    """

    feasibility_summary, roadmap_lines = _feasibility_summary(proposal, feasibility)

    return PRDDocument(
        proposal_id=proposal.proposal_id,
        title=proposal.title,
        problem_statement=proposal.problem_statement or proposal.summary,
        evidence=list(proposal.evidence),
        opportunity_summary=_opportunity_summary(proposal, opportunity),
        solution_summary=proposal.summary,
        expected_contribution=list(proposal.expected_outcomes),
        feasibility_summary=feasibility_summary,
        roadmap_summary=roadmap_lines,
        novelty_confidence=proposal.novelty_confidence,
    )


# ---------------------------------------------------------------------------
# MVP scaffold generation
# ---------------------------------------------------------------------------

def _slugify(title: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in title)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "project"


def _requirements_txt(proposal: ProjectProposal) -> str:
    py_libs = {
        "fastapi", "uvicorn", "pydantic", "python-dotenv",
    }
    known_pip_names = {
        "python": None,
        "pytorch": "torch",
        "scikit-learn": "scikit-learn",
        "fastapi": "fastapi",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
    }
    for tech in proposal.technical_approach:
        pip_name = known_pip_names.get(tech.lower())
        if pip_name:
            py_libs.add(pip_name)
    return "\n".join(sorted(py_libs)) + "\n"


def generate_mvp_scaffold(proposal: ProjectProposal) -> dict[str, str]:
    """Generate an honest starter-repo file manifest for a ProjectProposal.

    Returns a mapping of relative file path -> file content. This is a
    clean, buildable *starting point* (routes/components are TODO stubs),
    never a fake finished implementation — the point is to let a developer
    jump straight into building the idea, not to pretend it's already built.
    """

    slug = _slugify(proposal.title)
    objectives_md = "\n".join(f"- {o}" for o in proposal.objectives) or "- TODO: define objectives"
    features_md = "\n".join(f"- [ ] {f}" for f in proposal.key_features) or "- [ ] TODO: define key features"

    manifest: dict[str, str] = {}

    manifest["README.md"] = f"""# {proposal.title}

{proposal.summary}

## Problem

{proposal.problem_statement or "TODO: describe the problem this project solves."}

## Objectives

{objectives_md}

## Key Features (MVP checklist)

{features_md}

## Getting started

Backend:

```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```
cd frontend
npm install
npm run dev
```

## Status

This is a starter scaffold, not a finished implementation. Routes, models,
and UI are stubs — build out the logic described above.
"""

    manifest["requirements.txt"] = _requirements_txt(proposal)

    manifest[".gitignore"] = (
        "__pycache__/\n*.pyc\n.env\nnode_modules/\ndist/\n.venv/\n"
    )

    manifest["backend/requirements.txt"] = _requirements_txt(proposal)

    manifest["backend/.env.example"] = (
        "# Copy to .env and fill in real values. Never commit .env.\n"
        "LLM_API_KEY=\n"
        "LLM_MODEL=\n"
    )

    manifest["backend/app/main.py"] = f'''"""FastAPI entrypoint for {proposal.title}.

Starter stub — implement the routes this project needs.
"""

from fastapi import FastAPI

app = FastAPI(title="{proposal.title}")


@app.get("/health")
def health() -> dict:
    return {{"status": "ok", "service": "{slug}"}}


# TODO: implement routes for:
{chr(10).join(f"# - {o}" for o in proposal.objectives) or "# - (no objectives specified)"}
'''

    manifest["backend/app/__init__.py"] = ""

    manifest["frontend/package.json"] = f"""{{
  "name": "{slug}-frontend",
  "private": true,
  "version": "0.0.1",
  "scripts": {{
    "dev": "vite",
    "build": "vite build"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "vite": "^5.0.0"
  }}
}}
"""

    manifest["frontend/.env.example"] = "VITE_API_BASE_URL=http://localhost:8000\n"

    manifest["frontend/README.md"] = (
        f"# {proposal.title} — Frontend\n\n"
        "Starter stub. Build the UI for the key features listed in the root README.\n"
    )

    manifest["frontend/src/App.stub.txt"] = (
        "TODO: implement the App component for the primary user flow:\n"
        + features_md
    )

    return manifest


def write_scaffold(manifest: dict[str, str], output_dir: Path) -> list[Path]:
    """Write a scaffold manifest to disk under ``output_dir``.

    Returns the list of paths written. Raises if any manifest path would
    resolve outside ``output_dir`` (defense against a malformed manifest).
    """

    output_dir = Path(output_dir).resolve()
    written: list[Path] = []

    for rel_path, content in manifest.items():
        dest = (output_dir / rel_path).resolve()
        if output_dir not in dest.parents and dest != output_dir:
            raise ValueError(f"Refusing to write outside scaffold directory: {rel_path}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written.append(dest)

    return written
