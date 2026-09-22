import type { OpenAlexPaper } from "../../types";

const STOP_WORDS = new Set([
  "a", "an", "and", "are", "as", "at", "based", "by", "for", "from", "in",
  "into", "is", "it", "its", "of", "on", "or", "the", "to", "using", "via",
  "with", "study", "analysis", "approach", "towards", "toward", "new",
]);

function topTopics(papers: OpenAlexPaper[], limit = 6): { term: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const paper of papers) {
    const words = new Set(
      paper.title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, " ")
        .split(/\s+/)
        .filter((w) => w.length > 3 && !STOP_WORDS.has(w)),
    );
    for (const word of words) counts.set(word, (counts.get(word) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .filter(([, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([term, count]) => ({ term, count }));
}

function yearBuckets(papers: OpenAlexPaper[]): { year: number; count: number }[] {
  const counts = new Map<number, number>();
  for (const paper of papers) {
    if (paper.year == null) continue;
    counts.set(paper.year, (counts.get(paper.year) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .sort(([a], [b]) => a - b)
    .map(([year, count]) => ({ year, count }));
}

/**
 * Lightweight client-side topic/timeline summary of a discovery result set —
 * built entirely from fields OpenAlex already returns (title, year), no
 * extra backend call.
 */
export default function DiscoveryInsights({ papers }: { papers: OpenAlexPaper[] }) {
  if (papers.length === 0) return null;

  const topics = topTopics(papers);
  const years = yearBuckets(papers);
  const maxYearCount = Math.max(1, ...years.map((y) => y.count));

  return (
    <div className="bg-white rounded-2xl border border-border p-5 mb-6">
      <p className="font-display font-bold text-ink mb-4">
        {papers.length} papers analyzed
      </p>

      {topics.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">
            Recurring topics
          </p>
          <div className="flex flex-wrap gap-2">
            {topics.map((t) => (
              <span
                key={t.term}
                className="text-sm rounded-full bg-pill-bg text-ink px-3 py-1"
              >
                {t.term} · {Math.round((t.count / papers.length) * 100)}%
              </span>
            ))}
          </div>
        </div>
      )}

      {years.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">
            Publication timeline
          </p>
          <div className="flex items-end gap-2 h-16">
            {years.map((y) => (
              <div key={y.year} className="flex flex-col items-center justify-end gap-1 flex-1 h-full">
                <div
                  className="w-full rounded-t bg-mint-deep"
                  style={{ height: `${Math.max(6, Math.round((y.count / maxYearCount) * 48))}px` }}
                  title={`${y.count} paper${y.count > 1 ? "s" : ""} in ${y.year}`}
                />
                <span className="text-[10px] text-muted">{y.year}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
