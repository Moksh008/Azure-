import { useState } from "react";
import { ApiError, uploadPapersBatch } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { EvidenceChunk } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

export default function UploadPage() {
  const { addUploadedPaper } = useAppData();
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [chunks, setChunks] = useState<EvidenceChunk[]>([]);

  async function handleUpload() {
    if (files.length === 0) return;
    setStatus("loading");
    setError(null);
    try {
      const result = await uploadPapersBatch(files);
      setChunks(result);
      addUploadedPaper(result);
      setStatus("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Is the backend running?");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Upload papers"
      description="Upload one or multiple PDFs to extract and chunk their text — every chunk carries paper, section, and page metadata so later analysis and Q&A can cite it exactly."
    >
      <div className="bg-white rounded-2xl border border-border p-8">
        <label
          htmlFor="paper-upload"
          className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-border rounded-2xl py-14 cursor-pointer hover:border-mint-deep transition-colors"
        >
          <span className="font-display font-bold text-ink">
            {files.length > 0
              ? `${files.length} PDF(s) selected: ${files.map((f) => f.name).join(", ")}`
              : "Click to choose PDF(s)"}
          </span>
          <span className="text-muted text-sm">or drag and drop — choose multiple PDFs at once</span>
          <input
            id="paper-upload"
            type="file"
            accept="application/pdf"
            multiple
            className="sr-only"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
        </label>

        <button
          onClick={handleUpload}
          disabled={files.length === 0 || status === "loading"}
          className="mt-6 w-full rounded-[10px] bg-ink text-white font-semibold py-3.5 cursor-pointer hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {status === "loading" ? "Uploading…" : `Upload and extract (${files.length} file${files.length === 1 ? "" : "s"})`}
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
          <p className="font-semibold text-ink mb-3">{chunks.length} chunks extracted</p>
          <ul className="space-y-3 max-h-96 overflow-y-auto">
            {chunks.map((c) => (
              <li key={c.chunk_id} className="text-sm border-b border-row-border pb-3 last:border-b-0">
                <p className="text-xs text-muted mb-1">
                  {c.section ?? "Unknown section"} · Page {c.page ?? "?"}
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
