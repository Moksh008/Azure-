import type { PaperComparison } from "../../types";

function Row({ label, items, tone = "default" }: { label: string; items: string[]; tone?: "default" | "warn" }) {
  if (!items.length) return null;
  return (
    <div className="py-4 border-b border-row-border last:border-b-0">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">{label}</p>
      <ul className="flex flex-wrap gap-2">
        {items.map((item, i) => (
          <li
            key={i}
            className={`text-sm rounded-full px-3 py-1 ${
              tone === "warn" ? "bg-coral/10 text-coral" : "bg-pill-bg text-ink"
            }`}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ComparisonTable({ comparison }: { comparison: PaperComparison }) {
  return (
    <div className="bg-white rounded-2xl border border-border p-6">
      <p className="font-display font-bold text-lg text-ink mb-1">Paper comparison</p>
      <p className="text-muted text-sm mb-2">{comparison.paper_ids.length} papers compared</p>
      <Row label="Shared themes" items={comparison.shared_themes} />
      <Row label="Methodological overlaps" items={comparison.methodological_overlaps} />
      <Row label="Methodological differences" items={comparison.methodological_differences} />
      <Row label="Shared datasets" items={comparison.shared_datasets} />
      <Row label="Key findings" items={comparison.key_findings} />
      <Row label="Common limitations" items={comparison.common_limitations} tone="warn" />
      <Row label="Contradictions" items={comparison.contradictions} tone="warn" />
    </div>
  );
}
