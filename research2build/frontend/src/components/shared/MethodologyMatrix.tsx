import type { PaperAnalysis } from "../../types";

function cellText(claim: { claim: string } | null | undefined, fallback = "—"): string {
  const text = claim?.claim?.trim();
  return text || fallback;
}

/**
 * Paper x Method x Dataset x Result x Limitation grid, built directly from
 * already-analyzed papers (PaperAnalysis[] in AppDataContext) — no extra
 * backend call needed, since every field here is already grounded with
 * citations from /analysis.
 */
export default function MethodologyMatrix({ analyses }: { analyses: PaperAnalysis[] }) {
  if (analyses.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl border border-border p-6 overflow-x-auto">
      <p className="font-display font-bold text-lg text-ink mb-1">Methodology matrix</p>
      <p className="text-muted text-sm mb-4">
        Every cell is grounded in the paper's own analysis — hover a paper's title to see its ID.
      </p>
      <table className="w-full text-sm border-collapse min-w-[640px]">
        <thead>
          <tr className="text-left border-b border-row-border">
            <th className="py-2 pr-4 font-semibold text-ink">Paper</th>
            <th className="py-2 pr-4 font-semibold text-ink">Method</th>
            <th className="py-2 pr-4 font-semibold text-ink">Dataset</th>
            <th className="py-2 pr-4 font-semibold text-ink">Key result</th>
            <th className="py-2 pr-4 font-semibold text-ink">Limitation</th>
          </tr>
        </thead>
        <tbody>
          {analyses.map((a) => (
            <tr key={a.paper_id} className="border-b border-row-border last:border-b-0 align-top">
              <td className="py-3 pr-4 font-medium text-ink" title={a.paper_id}>
                {a.paper_title}
              </td>
              <td className="py-3 pr-4 text-ink/80 max-w-[220px]">{cellText(a.methodology)}</td>
              <td className="py-3 pr-4 text-ink/80 max-w-[180px]">{cellText(a.dataset)}</td>
              <td className="py-3 pr-4 text-ink/80 max-w-[240px]">{cellText(a.results[0])}</td>
              <td className="py-3 pr-4 text-ink/80 max-w-[240px]">{cellText(a.limitations[0])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
