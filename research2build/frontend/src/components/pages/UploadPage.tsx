import { useState, type DragEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError, uploadPaper, uploadPapersBatch } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { EvidenceChunk } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

function groupByPaper(chunks: EvidenceChunk[]): Map<string, EvidenceChunk[]> {
  const groups = new Map<string, EvidenceChunk[]>();
  for (const chunk of chunks) {
    const list = groups.get(chunk.paper_id);
    if (list) list.push(chunk);
    else groups.set(chunk.paper_id, [chunk]);
  }
  return groups;
}

export default function UploadPage() {
  const { addUploadedPaper } = useAppData();
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [chunks, setChunks] = useState<EvidenceChunk[]>([]);

  function addFiles(incoming: FileList | File[]) {
    const pdfs = Array.from(incoming).filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
    if (pdfs.length === 0) return;
    setFiles((prev) => [...prev, ...pdfs]);
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function handleDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  }

  async function handleUpload() {
    if (files.length === 0) return;
    setStatus("loading");
    setError(null);
    try {
      const result = files.length === 1 ? await uploadPaper(files[0]) : await uploadPapersBatch(files);
      setChunks(result);
      for (const paperChunks of groupByPaper(result).values()) {
        addUploadedPaper(paperChunks);
      }
      setStatus("done");
      setFiles([]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Is the backend running?");
      setStatus("error");
    }
  }

  const paperCount = groupByPaper(chunks).size;

  return (
    <PageShell
      title="Upload papers"
      description="Upload one or more PDFs to extract and chunk their text — every chunk carries paper, section, and page metadata so later analysis and Q&A can cite it exactly. Uploaded papers are added to your library automatically."
    >
      <div className="bg-white rounded-2xl border border-border p-8">
        <label
          htmlFor="paper-upload"
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-2xl py-14 cursor-pointer transition-colors ${
            isDragging ? "border-mint-deep bg-mint-deep/5" : "border-border hover:border-mint-deep"
          }`}
        >
          <span className="font-display font-bold text-ink">
            {files.length > 0
              ? `${files.length} PDF${files.length > 1 ? "s" : ""} selected`
              : "Click to choose PDFs"}
          </span>
          <span className="text-muted text-sm">or drag and drop — max 25MB each</span>
          <input
            id="paper-upload"
            type="file"
            accept="application/pdf"
            multiple
            className="sr-only"
            onChange={(e) => {
              if (e.target.files?.length) addFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </label>

        {files.length > 0 && (
          <ul className="mt-4 space-y-2">
            {files.map((f, i) => (
              <li
                key={`${f.name}-${i}`}
                className="flex items-center justify-between text-sm bg-pill-bg rounded-[10px] px-3.5 py-2"
              >
                <span className="text-ink truncate">{f.name}</span>
                <button
                  onClick={() => removeFile(i)}
                  className="text-muted hover:text-ink cursor-pointer shrink-0 ml-3"
                  aria-label={`Remove ${f.name}`}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}

        <button
          onClick={handleUpload}
          disabled={files.length === 0 || status === "loading"}
          className="mt-6 w-full rounded-[10px] bg-ink text-white font-semibold py-3.5 cursor-pointer hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {status === "loading"
            ? "Uploading…"
            : files.length > 1
              ? `Upload ${files.length} papers and extract`
              : "Upload and extract"}
        </button>
      </div>

      {status === "loading" && <div className="mt-6"><LoadingState label="Extracting text and chunking…" /></div>}
      {status === "error" && error && (
        <div className="mt-6">
          <ErrorState message={error} onRetry={handleUpload} />
        </div>
      )}

      {status === "done" && (
        <div className="mt-6 bg-white rounded-2xl border border-border p-6">
          <p className="font-semibold text-ink mb-3">
            {chunks.length} chunks extracted from {paperCount} paper{paperCount === 1 ? "" : "s"} — added to your{" "}
            <Link to="/chat" className="underline">
              library
            </Link>
            .
          </p>
          <ul className="space-y-3 max-h-96 overflow-y-auto">
            {chunks.map((c) => (
              <li key={c.chunk_id} className="text-sm border-b border-row-border pb-3 last:border-b-0">
                <p className="text-xs text-muted mb-1">
                  {c.paper_title} · {c.section ?? "Unknown section"} · Page {c.page ?? "?"}
                </p>
                <p className="text-ink line-clamp-2">{c.text}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </PageShell>
  );
}
