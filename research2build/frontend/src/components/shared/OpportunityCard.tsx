import type { ResearchOpportunity } from "../../types";

export default function OpportunityCard({
  opportunity,
  onGenerateProject,
}: {
  opportunity: ResearchOpportunity;
  onGenerateProject?: () => void;
}) {
  return (
    <div className="bg-white rounded-2xl border border-border p-6">
      <span className="inline-block rounded-full bg-periwinkle/30 text-ink text-xs font-semibold px-3 py-1 mb-3">
        Potential research opportunity
      </span>
      <p className="font-display font-bold text-lg text-ink">{opportunity.title}</p>
      <p className="text-ink/80 text-sm mt-2">{opportunity.description}</p>

      {opportunity.keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {opportunity.keywords.map((k) => (
            <span key={k} className="text-xs bg-pill-bg text-muted rounded-full px-2.5 py-1">
              {k}
            </span>
          ))}
        </div>
      )}

      <p className="text-xs text-muted mt-4">
        Inferred from recurring limitations in {opportunity.paper_ids.length} supplied paper(s).
        Novelty confidence: {opportunity.novelty_confidence}.
      </p>

      {onGenerateProject && (
        <button
          onClick={onGenerateProject}
          className="mt-4 rounded-[10px] bg-ink text-white text-sm font-semibold px-4 py-2.5 cursor-pointer hover:opacity-90"
        >
          Generate project proposals
        </button>
      )}
    </div>
  );
}
