import type { ProjectProposal } from "../../types";

export default function ProjectCard({
  proposal,
  onCheckFeasibility,
}: {
  proposal: ProjectProposal;
  onCheckFeasibility?: () => void;
}) {
  return (
    <div className="bg-white rounded-2xl border border-border p-6 flex flex-col">
      <p className="font-display font-bold text-lg text-ink">{proposal.title}</p>
      <p className="text-ink/80 text-sm mt-2">{proposal.summary}</p>

      {proposal.key_features.length > 0 && (
        <ul className="mt-3 space-y-1">
          {proposal.key_features.slice(0, 3).map((f, i) => (
            <li key={i} className="text-sm text-muted flex gap-2">
              <span className="text-mint-deep shrink-0" aria-hidden="true">✓</span>
              {f}
            </li>
          ))}
        </ul>
      )}

      {proposal.technical_approach.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {proposal.technical_approach.map((t) => (
            <span key={t} className="text-xs bg-pill-bg text-muted rounded-full px-2.5 py-1">
              {t}
            </span>
          ))}
        </div>
      )}

      <p className="text-xs text-muted mt-4">Novelty confidence: {proposal.novelty_confidence}.</p>

      {onCheckFeasibility && (
        <button
          onClick={onCheckFeasibility}
          className="mt-4 rounded-[10px] bg-ink text-white text-sm font-semibold px-4 py-2.5 cursor-pointer hover:opacity-90 self-start"
        >
          Check feasibility
        </button>
      )}
    </div>
  );
}
