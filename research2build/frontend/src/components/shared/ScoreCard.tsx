import type { FeasibilityAssessment, FeasibilityLevel } from "../../types";

const LEVEL_STYLE: Record<FeasibilityLevel, { bg: string; label: string }> = {
  high: { bg: "bg-mint text-ink", label: "High feasibility" },
  medium: { bg: "bg-yellow text-ink", label: "Medium feasibility" },
  low: { bg: "bg-peach text-ink", label: "Low feasibility" },
  not_feasible: { bg: "bg-coral text-white", label: "Not feasible as scoped" },
};

export default function ScoreCard({ assessment }: { assessment: FeasibilityAssessment }) {
  const style = LEVEL_STYLE[assessment.level];

  return (
    <div className="bg-white rounded-2xl border border-border p-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-panel-dark text-white flex items-center justify-center font-display font-bold text-xl shrink-0">
            {assessment.score}
          </div>
          <div>
            <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${style.bg}`}>
              {style.label}
            </span>
            <p className="text-muted text-sm mt-1">Score out of 100</p>
          </div>
        </div>
        <dl className="flex gap-6 text-sm">
          <div>
            <dt className="text-muted">Est. effort</dt>
            <dd className="font-semibold text-ink">{assessment.estimated_effort_weeks} person-weeks</dd>
          </div>
          <div>
            <dt className="text-muted">Skill coverage</dt>
            <dd className="font-semibold text-ink">{Math.round(assessment.skill_coverage * 100)}%</dd>
          </div>
        </dl>
      </div>

      {assessment.components.length > 0 && (
        <div className="mt-5 pt-5 border-t border-row-border">
          <p className="font-semibold text-sm text-ink mb-3">Feasibility breakdown</p>
          <div className="space-y-3">
            {assessment.components.map((component) => (
              <div key={component.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-ink font-medium">{component.label}</span>
                  <span className="text-muted">{component.score}/100</span>
                </div>
                <div className="h-2 rounded-full bg-row-border overflow-hidden">
                  <div
                    className="h-full rounded-full bg-mint-deep"
                    style={{ width: `${component.score}%` }}
                  />
                </div>
                <p className="text-xs text-muted mt-1">{component.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {assessment.risks.length > 0 && (
        <div className="mt-5 pt-5 border-t border-row-border">
          <p className="font-semibold text-sm text-ink mb-2">Risks</p>
          <ul className="space-y-1.5">
            {assessment.risks.map((risk, i) => (
              <li key={i} className="text-sm text-muted flex gap-2">
                <span className="text-coral shrink-0" aria-hidden="true">●</span>
                {risk}
              </li>
            ))}
          </ul>
        </div>
      )}

      {assessment.constraint_notes.length > 0 && (
        <div className="mt-4">
          <p className="font-semibold text-sm text-ink mb-2">Constraint notes</p>
          <ul className="space-y-1.5">
            {assessment.constraint_notes.map((note, i) => (
              <li key={i} className="text-sm text-muted flex gap-2">
                <span className="text-yellow-deep shrink-0" aria-hidden="true">●</span>
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
