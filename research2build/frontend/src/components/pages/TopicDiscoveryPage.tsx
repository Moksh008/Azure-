import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { discoverTopics } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { OpenAlexPaper } from "../../types";
import DiscoveryInsights from "../shared/DiscoveryInsights";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PaperCard from "../shared/PaperCard";
import PageShell from "../PageShell";

export default function TopicDiscoveryPage() {
  const { addDiscoveredPapers, selectedPaperIds, toggleSelected } = useAppData();
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<OpenAlexPaper[]>([]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [addedCount, setAddedCount] = useState(0);

  async function runSearch(term: string) {
    if (!term.trim()) return;
    setStatus("loading");
    setError(null);
    setAddedCount(0);
    try {
      const papers = await discoverTopics(term.trim());
      setResults(papers);
      setPicked(new Set());
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

  function togglePicked(id: string) {
    setPicked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleAddToLibrary() {
    const chosen = results.filter((p) => picked.has(p.paper_id));
    if (chosen.length === 0) return;
    addDiscoveredPapers(chosen);
    for (const paper of chosen) {
      if (!selectedPaperIds.has(paper.paper_id)) toggleSelected(paper.paper_id);
    }
    setAddedCount(chosen.length);
    setPicked(new Set());
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
        <div className="mt-8">
          {addedCount > 0 && (
            <p className="text-sm text-mint-deep font-semibold mb-4">
              Added {addedCount} paper{addedCount > 1 ? "s" : ""} to your{" "}
              <Link to="/chat" className="underline">
                library
              </Link>
              .
            </p>
          )}

          <DiscoveryInsights papers={results} />

          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted">
              {results.length === 0
                ? `No results for "${query}".`
                : `${picked.size} of ${results.length} selected`}
            </p>
            {results.length > 0 && (
              <button
                onClick={handleAddToLibrary}
                disabled={picked.size === 0}
                className="rounded-[10px] bg-ink text-white font-semibold px-4 py-2 text-sm cursor-pointer hover:opacity-90 disabled:opacity-40"
              >
                Add {picked.size > 0 ? picked.size : ""} selected to library
              </button>
            )}
          </div>

          <div className="space-y-4">
            {results.map((paper) => (
              <PaperCard
                key={paper.paper_id}
                paper={paper}
                selected={picked.has(paper.paper_id)}
                onToggle={() => togglePicked(paper.paper_id)}
              />
            ))}
          </div>
        </div>
      )}
    </PageShell>
  );
}
