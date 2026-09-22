import { useRef, useState } from "react";
import { ApiError, fetchFullText, sendChatMessage, uploadPapersBatch } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { ChatMessage as ChatMessageType, OpenAlexPaper } from "../../types";
import AnalysisCard from "../shared/AnalysisCard";
import { CitationList, CitationModalProvider, EvidencePanel } from "../shared/Citation";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PaperCard from "../shared/PaperCard";
import PageShell from "../PageShell";

type Turn =
  | { kind: "text"; role: "user" | "assistant"; content: string }
  | { kind: "papers"; papers: OpenAlexPaper[] }
  | { kind: "answer"; question: string; answer: import("../../types").GroundedAnswer }
  | { kind: "analyses"; analyses: import("../../types").PaperAnalysis[] };

export default function ChatPage() {
  const {
    library,
    addUploadedPaper,
    addDiscoveredPapers,
    selectedPaperIds,
    toggleSelected,
    selectedEvidence,
    setFullText,
  } = useAppData();

  const [turns, setTurns] = useState<Turn[]>([
    {
      kind: "text",
      role: "assistant",
      content:
        "Hi! Upload a PDF or tell me a topic to search, then tick the papers you want and ask me anything about them.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchingFullTextIds, setFetchingFullTextIds] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  function historyForApi(): ChatMessageType[] {
    return turns
      .filter((t): t is Extract<Turn, { kind: "text" }> => t.kind === "text")
      .map((t) => ({ role: t.role, content: t.content }));
  }

  async function handleSend() {
    const message = input.trim();
    if (!message || sending) return;
    setInput("");
    setError(null);
    setTurns((prev) => [...prev, { kind: "text", role: "user", content: message }]);
    setSending(true);
    try {
      const libraryRefs = library.map((p) => ({ paper_id: p.paper_id, title: p.title, source: p.source }));
      const res = await sendChatMessage(message, historyForApi(), libraryRefs, selectedEvidence);

      setTurns((prev) => [...prev, { kind: "text", role: "assistant", content: res.reply }]);

      if (res.action === "search" && res.discovered_papers?.length) {
        addDiscoveredPapers(res.discovered_papers);
        setTurns((prev) => [...prev, { kind: "papers", papers: res.discovered_papers! }]);
      } else if (res.action === "ask" && res.answer) {
        setTurns((prev) => [...prev, { kind: "answer", question: message, answer: res.answer! }]);
      } else if (res.action === "analyze" && res.analyses?.length) {
        setTurns((prev) => [...prev, { kind: "analyses", analyses: res.analyses! }]);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Chat request failed. Is the backend running?");
    } finally {
      setSending(false);
    }
  }

  async function handleFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;
    const files = Array.from(fileList);
    e.target.value = "";
    setUploading(true);
    setError(null);
    try {
      const chunks = await uploadPapersBatch(files);
      addUploadedPaper(chunks);
      const count = files.length;
      const label = count === 1 ? `Uploaded "${files[0].name}"` : `Uploaded ${count} PDFs`;
      setTurns((prev) => [
        ...prev,
        {
          kind: "text",
          role: "assistant",
          content: `${label} — extracted ${chunks.length} total chunk(s) and selected them for you. Ask me anything about them.`,
        },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  }

  async function handleFetchFullText(paperId: string, title: string, pdfUrl: string) {
    setFetchingFullTextIds((prev) => new Set(prev).add(paperId));
    setError(null);
    try {
      const chunks = await fetchFullText(paperId, title, pdfUrl);
      setFullText(paperId, chunks);
      setTurns((prev) => [
        ...prev,
        {
          kind: "text",
          role: "assistant",
          content: `Fetched the full text of "${title}" (${chunks.length} chunk(s)) — questions and analysis will now use the whole paper, not just its abstract.`,
        },
      ]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Couldn't fetch the full PDF — it may not be freely accessible.",
      );
    } finally {
      setFetchingFullTextIds((prev) => {
        const next = new Set(prev);
        next.delete(paperId);
        return next;
      });
    }
  }

  return (
    <PageShell
      title="Chat"
      description="Upload a paper or search by topic, tick the ones you want, then ask questions — everything grounded in exactly the papers you selected."
    >
      <CitationModalProvider>
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="bg-white rounded-2xl border border-border p-4 h-fit lg:sticky lg:top-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                Papers in context
              </p>
              <span className="text-xs font-semibold text-muted">{selectedPaperIds.size} selected</span>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              multiple
              className="sr-only"
              onChange={handleFileChosen}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full rounded-[10px] bg-ink text-white text-sm font-semibold py-2.5 mb-4 cursor-pointer hover:opacity-90 disabled:opacity-40"
            >
              {uploading ? "Uploading…" : "Upload PDF(s)"}
            </button>

            {library.length === 0 && (
              <p className="text-sm text-muted">No papers yet — upload one or search for a topic below.</p>
            )}
            <ul className="space-y-2 max-h-[60vh] overflow-y-auto">
              {library.map((p) => {
                const fetchingFullText = fetchingFullTextIds.has(p.paper_id);
                const canFetchFullText = p.source === "discovery" && p.pdf_url && !p.fullTextFetched;
                return (
                  <li key={p.paper_id}>
                    <button
                      onClick={() => toggleSelected(p.paper_id)}
                      aria-pressed={selectedPaperIds.has(p.paper_id)}
                      className={`w-full text-left rounded-[10px] border p-3 cursor-pointer transition-colors ${
                        selectedPaperIds.has(p.paper_id)
                          ? "border-mint-deep bg-mint/10 ring-1 ring-mint-deep/30"
                          : "border-border hover:bg-pill-bg"
                      }`}
                    >
                      <p className="text-sm font-semibold text-ink line-clamp-2">{p.title}</p>
                      <p className="text-xs text-muted mt-1 capitalize">
                        {p.source}
                        {p.fullTextFetched && " · full text"}
                      </p>
                    </button>
                    {canFetchFullText && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFetchFullText(p.paper_id, p.title, p.pdf_url!);
                        }}
                        disabled={fetchingFullText}
                        className="mt-1.5 w-full text-xs font-semibold text-blue underline cursor-pointer disabled:opacity-40 disabled:no-underline"
                      >
                        {fetchingFullText ? "Fetching full text…" : "Get full text"}
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          </aside>

          <div className="flex flex-col">
            <div className="space-y-4 mb-4">
              {turns.map((turn, i) => {
                if (turn.kind === "text") {
                  return (
                    <div
                      key={i}
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        turn.role === "user"
                          ? "bg-ink text-white ml-auto"
                          : "bg-white border border-border text-ink"
                      }`}
                    >
                      {turn.content}
                    </div>
                  );
                }
                if (turn.kind === "papers") {
                  return (
                    <div key={i} className="space-y-3">
                      {turn.papers.map((paper) => (
                        <PaperCard
                          key={paper.paper_id}
                          paper={paper}
                          selected={selectedPaperIds.has(paper.paper_id)}
                          onToggle={() => toggleSelected(paper.paper_id)}
                        />
                      ))}
                    </div>
                  );
                }
                if (turn.kind === "answer") {
                  return (
                    <div key={i} className="bg-white rounded-2xl border border-border p-6">
                      <p className="text-sm font-semibold text-muted mb-2">{turn.question}</p>
                      <p className="text-ink">{turn.answer.answer}</p>
                      {!turn.answer.evidence_sufficient && (
                        <p className="text-xs text-coral font-semibold mt-2">
                          Evidence insufficient — treat this answer with caution.
                        </p>
                      )}
                      <CitationList citations={turn.answer.citations} />
                      <EvidencePanel citations={turn.answer.citations} />
                    </div>
                  );
                }
                return (
                  <div key={i} className="space-y-4">
                    {turn.analyses.map((a) => (
                      <AnalysisCard key={a.paper_id} analysis={a} />
                    ))}
                  </div>
                );
              })}

              {sending && <LoadingState label="Thinking…" />}
              {error && <ErrorState message={error} onRetry={handleSend} />}
            </div>

            <div className="sticky bottom-6 flex gap-3 bg-bg pt-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder='e.g. "search for federated learning papers" or "what are the main limitations?"'
                className="flex-1 rounded-[10px] border border-border px-4 py-3 bg-white text-ink focus:outline-none focus:ring-2 focus:ring-mint-deep"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || sending}
                className="rounded-[10px] bg-ink text-white font-semibold px-6 cursor-pointer hover:opacity-90 disabled:opacity-40"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </CitationModalProvider>
    </PageShell>
  );
}
