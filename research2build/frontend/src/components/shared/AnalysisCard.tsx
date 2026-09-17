import type { GroundedClaim, PaperAnalysis } from "../../types";
import { CitationList } from "./Citation";

function Field({ label, claim }: { label: string; claim: GroundedClaim | null }) {
  if (!claim) return null;
  return (
    <div className="py-3 border-b border-row-border last:border-b-0">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="text-ink mt-1">{claim.claim}</p>
      <CitationList citations={claim.citations} />
    </div>
  );
}

function ClaimList({ label, claims }: { label: string; claims: GroundedClaim[] }) {
  if (!claims.length) return null;
  return (
    <div className="py-3 border-b border-row-border last:border-b-0">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">{label}</p>
      <ul className="space-y-3">
        {claims.map((c, i) => (
          <li key={i}>
            <p className="text-ink">{c.claim}</p>
            <CitationList citations={c.citations} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AnalysisCard({ analysis }: { analysis: PaperAnalysis }) {
  return (
    <div className="bg-white rounded-2xl border border-border p-6">
      <p className="font-display font-bold text-lg text-ink mb-2">{analysis.paper_title}</p>
      <Field label="Problem" claim={analysis.problem} />
      <Field label="Objective" claim={analysis.objective} />
      <Field label="Methodology" claim={analysis.methodology} />
      <Field label="Dataset" claim={analysis.dataset} />
      <Field label="Models" claim={analysis.models} />
      <ClaimList label="Results" claims={analysis.results} />
      <ClaimList label="Limitations" claims={analysis.limitations} />
      <ClaimList label="Future work" claims={analysis.future_work} />
    </div>
  );
}
