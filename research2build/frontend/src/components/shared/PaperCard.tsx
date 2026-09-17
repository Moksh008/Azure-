import type { OpenAlexPaper } from "../../types";

export default function PaperCard({
  paper,
  selected = false,
  onToggle,
}: {
  paper: OpenAlexPaper;
  selected?: boolean;
  onToggle?: () => void;
}) {
  return (
    <div
      className={`bg-white rounded-2xl border p-5 transition-colors ${
        selected ? "border-mint-deep ring-2 ring-mint-deep/30" : "border-border"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="font-display font-bold text-ink leading-snug">{paper.title}</p>
        {onToggle && (
          <button
            onClick={onToggle}
            aria-pressed={selected}
            className={`shrink-0 rounded-[10px] text-xs font-semibold px-3 py-2 cursor-pointer border ${
              selected ? "bg-ink text-white border-ink" : "bg-white text-ink border-border hover:bg-pill-bg"
            }`}
          >
            {selected ? "Selected" : "Select"}
          </button>
        )}
      </div>
      <p className="text-muted text-sm mt-1.5">
        {paper.authors.join(", ")}
        {paper.year ? ` · ${paper.year}` : ""}
      </p>
      {paper.abstract && <p className="text-sm text-ink/80 mt-3 line-clamp-3">{paper.abstract}</p>}
      {paper.url && (
        <a
          href={paper.url}
          target="_blank"
          rel="noreferrer"
          className="inline-block mt-3 text-sm font-semibold text-blue underline"
        >
          View on OpenAlex ↗
        </a>
      )}
    </div>
  );
}
