import { useState } from "react";
import { ApiError, uploadPaper } from "../../lib/api";
import type { EvidenceChunk } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [chunks, setChunks] = useState<EvidenceChunk[]>([]);

  async function handleUpload() {
    if (!file) return;
    setStatus("loading");
    setError(null);
    try {
      const result = await uploadPaper(file);
      setChunks(result);
      setStatus("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Is the backend running?");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Upload a paper"
      description="Upload a PDF to extract and chunk its text — every chunk carries paper, section, and page metadata so later analysis and Q&A can cite it exactly."
    >
      <div className="bg-white rounded-2xl border border-border p-8">
        <label
          htmlFor="paper-upload"
          className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-border rounded-2xl py-14 cursor-pointer hover:border-mint-deep transition-colors"
        >
          <span className="font-display font-bold text-ink">
            {file ? file.name : "Click to choose a PDF"}
          </span>
          <span className="text-muted text-sm">or drag and drop — max 25MB</span>
          <input
            id="paper-upload"
            type="file"
            accept="application/pdf"
            className="sr-only"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        <button
          onClick={handleUpload}
          disabled={!file || status === "loading"}
          className="mt-6 w-full rounded-[10px] bg-ink text-white font-semibold py-3.5 cursor-pointer hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {status === "loading" ? "Uploading…" : "Upload and extract"}
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
