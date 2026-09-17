import { createContext, useContext, useState, type ReactNode } from "react";
import type { Citation as CitationType } from "../../types";

interface CitationModalContextValue {
  open: (citation: CitationType) => void;
}

const CitationModalContext = createContext<CitationModalContextValue | null>(null);

/** Wrap a page/section in this once so any CitationBadge inside can open the shared modal. */
export function CitationModalProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<CitationType | null>(null);

  return (
    <CitationModalContext.Provider value={{ open: setActive }}>
      {children}
      {active && <CitationModal citation={active} onClose={() => setActive(null)} />}
    </CitationModalContext.Provider>
  );
}

function useCitationModal(): CitationModalContextValue {
  const ctx = useContext(CitationModalContext);
  if (!ctx) {
    throw new Error("CitationBadge must be rendered inside a CitationModalProvider");
  }
  return ctx;
}

function locationLabel(c: CitationType): string {
  const parts = [c.section, c.page ? `Page ${c.page}` : null].filter(Boolean);
  return parts.length ? parts.join(" · ") : "Location unknown";
}

/** Inline "[Paper 2 | Section | Page 7]"-style badge. Click opens the source passage. */
export function CitationBadge({ citation, index }: { citation: CitationType; index?: number }) {
  const { open } = useCitationModal();
  return (
    <button
      type="button"
      onClick={() => open(citation)}
      className="inline-flex items-center gap-1 rounded-full bg-pill-bg text-ink text-xs font-semibold px-2.5 py-1 mx-0.5 border border-border cursor-pointer hover:bg-mint hover:border-mint-deep transition-colors align-middle"
      title={`View source: ${citation.paper_title}`}
    >
      {typeof index === "number" ? `[${index + 1}]` : "[cite]"} {citation.paper_title}
    </button>
  );
}

/** Renders a row of citation badges for a claim/answer. */
export function CitationList({ citations }: { citations: CitationType[] }) {
  if (!citations.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {citations.map((c, i) => (
        <CitationBadge key={`${c.chunk_id}-${i}`} citation={c} index={i} />
      ))}
    </div>
  );
}

function CitationModal({ citation, onClose }: { citation: CitationType; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-5"
      role="dialog"
      aria-modal="true"
      aria-labelledby="citation-modal-title"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-[0_20px_60px_rgba(0,0,0,0.35)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p id="citation-modal-title" className="font-display font-bold text-lg text-ink">
              {citation.paper_title}
            </p>
            <p className="text-muted text-sm mt-1">{locationLabel(citation)}</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close citation detail"
            className="w-9 h-9 flex items-center justify-center rounded-full border border-border text-ink cursor-pointer hover:bg-pill-bg shrink-0"
          >
            ✕
          </button>
        </div>
        <blockquote className="mt-4 border-l-4 border-mint-deep pl-4 text-ink text-[15px] leading-relaxed italic">
          “{citation.quote}”
        </blockquote>
      </div>
    </div>
  );
}
