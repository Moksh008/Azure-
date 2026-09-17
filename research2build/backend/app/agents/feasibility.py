"""Member 5 — Feasibility Engine & Roadmap Generator.

Scores a ProjectProposal against user-supplied constraints (team size,
time budget, money budget, skills) and generates a step-by-step milestone
roadmap tailored to the proposal's complexity.

Operates deterministically and locally without LLM or external
dependencies, matching the ``project_generator.py`` convention: cheap,
reproducible, and gradeable without burning API calls.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.research_intelligence.models import ProjectProposal

# ---------------------------------------------------------------------------
# Complexity heuristics
# ---------------------------------------------------------------------------

# Roughly: person-weeks of effort needed per unit of proposal "surface area"
# (objectives + key features + technical approaches). Calibrated so a
# 3-objective / 3-feature / 3-tool student project lands around 8-10 weeks
# with a 2-person team.
EFFORT_WEEKS_PER_UNIT = 0.9

GPU_HEAVY_TERMS = frozenset({
    "pytorch", "gpu", "cuda", "training", "fine-tuning", "distillation",
    "quantization", "distributed", "deepspeed", "diffusion", "diffusers",
})

# Baseline roadmap phases in execution order, with relative weight used to
# split the total estimated timeline across phases.
ROADMAP_PHASES: tuple[tuple[str, float], ...] = (
    ("Research", 0.10),
    ("Dataset", 0.15),
    ("Backend", 0.20),
    ("AI", 0.25),
    ("Frontend", 0.15),
    ("Testing", 0.10),
    ("Deployment", 0.05),
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class FeasibilityConstraints(BaseModel):
    """User-supplied constraints the proposal is evaluated against."""

    team_size: int = Field(..., ge=1, description="Number of contributors available.")
    weeks_available: float = Field(..., gt=0, description="Total calendar weeks available.")
    budget_usd: float = Field(default=0.0, ge=0, description="Total money budget in USD.")
    skills: list[str] = Field(
        default_factory=list,
        description="Skills/technologies the team already has (free text, matched case-insensitively).",
    )


class Milestone(BaseModel):
    """One step in the generated roadmap."""

    phase: str
    description: str
    deliverables: list[str] = Field(default_factory=list)
    duration_weeks: float = Field(..., ge=0)
    start_week: float = Field(..., ge=0)
    end_week: float = Field(..., ge=0)


class Roadmap(BaseModel):
    """A step-by-step milestone schedule for a proposal."""

    total_weeks: float
    milestones: list[Milestone] = Field(default_factory=list)


class FeasibilityAssessment(BaseModel):
    """Structured feasibility verdict for a ProjectProposal."""

    proposal_id: str
    score: int = Field(..., ge=0, le=100)
    level: str = Field(..., description="one of: high, medium, low, not_feasible")
    estimated_effort_weeks: float
    skill_coverage: float = Field(..., ge=0, le=1)
    risks: list[str] = Field(default_factory=list)
    constraint_notes: list[str] = Field(default_factory=list)
    roadmap: Roadmap


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _estimate_effort_weeks(proposal: ProjectProposal) -> float:
    """Estimate person-weeks of effort from the proposal's stated scope."""

    surface_area = (
        len(proposal.objectives)
        + len(proposal.key_features)
        + len(proposal.technical_approach)
    )
    # Floor of 3 units so a sparsely-filled proposal doesn't look free.
    surface_area = max(surface_area, 3)
    return round(surface_area * EFFORT_WEEKS_PER_UNIT, 1)


def _skill_coverage(proposal: ProjectProposal, constraints: FeasibilityConstraints) -> float:
    """Fraction of the proposal's named technologies the team already has."""

    required = {t.lower() for t in proposal.technical_approach}
    if not required:
        return 1.0

    have = {s.lower() for s in constraints.skills}
    matched = sum(
        1 for tech in required
        if any(tech in skill or skill in tech for skill in have)
    )
    return round(matched / len(required), 2)


def _is_gpu_heavy(proposal: ProjectProposal) -> bool:
    text = " ".join(proposal.technical_approach + proposal.proposed_methods).lower()
    return any(term in text for term in GPU_HEAVY_TERMS)


def _budget_notes(proposal: ProjectProposal, constraints: FeasibilityConstraints) -> list[str]:
    notes: list[str] = []
    if _is_gpu_heavy(proposal) and constraints.budget_usd < 50:
        notes.append(
            "Proposal involves GPU-heavy work (training/fine-tuning/quantization) "
            f"but budget is ${constraints.budget_usd:.0f}; plan around free-tier "
            "compute (Colab, Kaggle) or a smaller model/dataset."
        )
    return notes


def score_feasibility(
    proposal: ProjectProposal,
    constraints: FeasibilityConstraints,
) -> FeasibilityAssessment:
    """Score a ProjectProposal's feasibility against team/time/budget/skill constraints.

    Returns a structured score (0-100), a feasibility level, concrete risks,
    and a tailored roadmap. Never raises on "bad" inputs — a poor fit simply
    scores low with explanatory risks, since that's a legitimate outcome the
    caller needs to see.
    """

    effort_weeks = _estimate_effort_weeks(proposal)
    capacity_weeks = constraints.team_size * constraints.weeks_available
    time_ratio = capacity_weeks / effort_weeks if effort_weeks > 0 else 1.0
    skill_coverage = _skill_coverage(proposal, constraints)

    # Component scores, each 0-100.
    time_score = min(time_ratio, 1.5) / 1.5 * 100
    skill_score = skill_coverage * 100
    budget_penalty = 20 if _budget_notes(proposal, constraints) else 0
    budget_score = max(0, 100 - budget_penalty)

    # Time fit matters most for a fixed-deadline student project.
    score = round(0.5 * time_score + 0.3 * skill_score + 0.2 * budget_score)
    score = max(0, min(100, score))

    if score >= 75:
        level = "high"
    elif score >= 50:
        level = "medium"
    elif score >= 25:
        level = "low"
    else:
        level = "not_feasible"

    risks: list[str] = []
    if time_ratio < 1.0:
        risks.append(
            f"Estimated effort (~{effort_weeks:.1f} person-weeks) exceeds available "
            f"capacity ({capacity_weeks:.1f} person-weeks); scope will need to be cut "
            "or the timeline extended."
        )
    if skill_coverage < 0.5:
        missing = sorted(
            t for t in proposal.technical_approach
            if not any(t.lower() in s.lower() or s.lower() in t.lower() for s in constraints.skills)
        )
        if missing:
            risks.append(
                "Team lacks experience with: " + ", ".join(missing) + ". "
                "Budget ramp-up time or swap for a familiar alternative."
            )
    if constraints.team_size == 1 and effort_weeks > constraints.weeks_available:
        risks.append("Solo team with a multi-person-week estimate; consider narrowing scope first.")

    constraint_notes = _budget_notes(proposal, constraints)

    roadmap = generate_roadmap(proposal, constraints, effort_weeks=effort_weeks)

    return FeasibilityAssessment(
        proposal_id=proposal.proposal_id,
        score=score,
        level=level,
        estimated_effort_weeks=effort_weeks,
        skill_coverage=skill_coverage,
        risks=risks,
        constraint_notes=constraint_notes,
        roadmap=roadmap,
    )


# ---------------------------------------------------------------------------
# Roadmap generation
# ---------------------------------------------------------------------------

_PHASE_DELIVERABLES: dict[str, list[str]] = {
    "Research": ["Finalized problem statement", "Literature/evidence recap"],
    "Dataset": ["Data collection or access plan", "Cleaned/prepared dataset"],
    "Backend": ["API scaffold", "Core data models", "Persistence layer"],
    "AI": ["Core model/algorithm implementation", "Initial evaluation results"],
    "Frontend": ["UI for primary user flow", "Integration with backend API"],
    "Testing": ["Test suite for core paths", "Bug-fix pass"],
    "Deployment": ["Deployed demo build", "Basic runbook/README"],
}


def generate_roadmap(
    proposal: ProjectProposal,
    constraints: FeasibilityConstraints,
    *,
    effort_weeks: float | None = None,
) -> Roadmap:
    """Generate a Research -> Deployment milestone schedule sized to the timeline.

    The schedule always fits within ``constraints.weeks_available`` — if the
    raw effort estimate is larger, phases are compressed proportionally
    rather than silently extending the calendar; that mismatch is instead
    surfaced as a risk by ``score_feasibility``.
    """

    if effort_weeks is None:
        effort_weeks = _estimate_effort_weeks(proposal)

    total_weeks = max(constraints.weeks_available, 1.0)

    key_features = list(proposal.key_features) or ["Core functionality"]

    milestones: list[Milestone] = []
    cursor = 0.0
    for phase, weight in ROADMAP_PHASES:
        duration = round(total_weeks * weight, 1)
        deliverables = list(_PHASE_DELIVERABLES.get(phase, []))
        if phase == "AI" and proposal.proposed_methods:
            deliverables = deliverables + list(proposal.proposed_methods[:2])
        if phase == "Frontend":
            deliverables = deliverables + key_features[:1]

        milestones.append(
            Milestone(
                phase=phase,
                description=f"{phase} phase for '{proposal.title}'.",
                deliverables=deliverables,
                duration_weeks=duration,
                start_week=round(cursor, 1),
                end_week=round(cursor + duration, 1),
            )
        )
        cursor += duration

    return Roadmap(total_weeks=round(cursor, 1), milestones=milestones)
