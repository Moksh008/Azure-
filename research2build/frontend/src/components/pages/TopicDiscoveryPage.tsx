import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { discoverTopics } from "../../lib/api";
import type { OpenAlexPaper } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PaperCard from "../shared/PaperCard";
import PageShell from "../PageShell";

export default function TopicDiscoveryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<OpenAlexPaper[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  async function runSearch(term: string) {
    if (!term.trim()) return;
    setStatus("loading");
    setError(null);
    try {
      const papers = await discoverTopics(term.trim());
      setResults(papers);
      setStatus("done");
    } catch {
      setError("Topic search failed. Try again in a moment.");
      setStatus("error");
    }
  }

  function handleSearch() {
    if (!query.trim()) return;
    if (searchParams.get("query")?.trim() === query.trim()) {
      // Same term already in the URL (e.g. retrying a failed search) — the
      // effect won't re-fire, so run the search directly.
      void runSearch(query);
    } else {
      setSearchParams({ query: query.trim() }, { replace: true });
    }
  }

  // A domain card on the landing page lands here with ?query= — auto-run discovery.
  const paramQuery = searchParams.get("query")?.trim() ?? "";
  useEffect(() => {
    if (!paramQuery) return;
    setQuery(paramQuery);
    void runSearch(paramQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramQuery]);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <PageShell
      title="Discover topics"
      description="Search OpenAlex for related papers to seed your evidence base without manual PDF hunting."
    >
      <div className="flex gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="e.g. federated learning communication efficiency"
          className="flex-1 rounded-[10px] border border-border px-4 py-3 bg-white text-ink focus:outline-none focus:ring-2 focus:ring-mint-deep"
        />
        <button
          onClick={handleSearch}
          disabled={!query.trim() || status === "loading"}
          className="rounded-[10px] bg-ink text-white font-semibold px-6 cursor-pointer hover:opacity-90 disabled:opacity-40"
        >
          Search
        </button>
      </div>

      {status === "loading" && <div className="mt-8"><LoadingState label="Searching OpenAlex…" /></div>}
      {status === "error" && error && (
        <div className="mt-8">
          <ErrorState message={error} onRetry={handleSearch} />
        </div>
      )}

      {status === "done" && (
        <div className="mt-8 space-y-4">
          {results.length === 0 && <p className="text-muted">No results for "{query}".</p>}
          {results.map((paper) => (
            <PaperCard
              key={paper.paper_id}
              paper={paper}
              selected={selected.has(paper.paper_id)}
              onToggle={() => toggle(paper.paper_id)}
            />
          ))}
        </div>
      )}
    </PageShell>
  );
}
