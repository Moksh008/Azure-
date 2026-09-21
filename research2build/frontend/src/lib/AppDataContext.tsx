import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type {
  EvidenceChunk,
  LibraryPaper,
  OpenAlexPaper,
  PaperAnalysis,
  ProjectProposal,
  ResearchOpportunity,
} from "../types";

interface AppDataValue {
  analyses: PaperAnalysis[];
  addAnalysis: (analysis: PaperAnalysis) => void;
  opportunities: ResearchOpportunity[];
  setOpportunities: (opportunities: ResearchOpportunity[]) => void;
  proposals: ProjectProposal[];
  setProposals: (proposals: ProjectProposal[]) => void;

  library: LibraryPaper[];
  addUploadedPaper: (chunks: EvidenceChunk[]) => void;
  addDiscoveredPapers: (papers: OpenAlexPaper[]) => void;
  selectedPaperIds: Set<string>;
  toggleSelected: (paperId: string) => void;
  selectedEvidence: EvidenceChunk[];
  setFullText: (paperId: string, chunks: EvidenceChunk[]) => void;
}

const AppDataContext = createContext<AppDataValue | null>(null);

/**
 * Session-only (in-memory, not persisted) store so pages can chain the
 * pipeline — analysis -> comparison -> opportunities -> proposals — without
 * a backend database. Matches the stateless design of the M4 modules: the
 * server never resolves IDs, callers always pass the objects they already
 * hold, and this context is just where the frontend keeps hold of them.
 *
 * `library`/`selectedPaperIds` extend this same pattern to the chat
 * workflow: every paper the user has uploaded or discovered lives here,
 * and the chunks of whichever ones are ticked are what gets sent to
 * /chat's ask/analyze intents.
 */
export function AppDataProvider({ children }: { children: ReactNode }) {
  const [analysesById, setAnalysesById] = useState<Record<string, PaperAnalysis>>({});
  const [opportunities, setOpportunities] = useState<ResearchOpportunity[]>([]);
  const [proposals, setProposals] = useState<ProjectProposal[]>([]);

  const [libraryById, setLibraryById] = useState<Record<string, LibraryPaper>>({});
  const [selectedPaperIds, setSelectedPaperIds] = useState<Set<string>>(new Set());

  const value = useMemo<AppDataValue>(() => {
    const library = Object.values(libraryById);
    const selectedEvidence = library
      .filter((p) => selectedPaperIds.has(p.paper_id))
      .flatMap((p) => p.evidence);

    return {
      analyses: Object.values(analysesById),
      addAnalysis: (analysis) =>
        setAnalysesById((prev) => ({ ...prev, [analysis.paper_id]: analysis })),
      opportunities,
      setOpportunities,
      proposals,
      setProposals,

      library,
      addUploadedPaper: (chunks) => {
        if (chunks.length === 0) return;
        const { paper_id, paper_title } = chunks[0];
        setLibraryById((prev) => ({
          ...prev,
          [paper_id]: { paper_id, title: paper_title, source: "upload", evidence: chunks },
        }));
        setSelectedPaperIds((prev) => new Set(prev).add(paper_id));
      },
      addDiscoveredPapers: (papers) => {
        setLibraryById((prev) => {
          const next = { ...prev };
          for (const paper of papers) {
            if (next[paper.paper_id]) continue;
            const text = paper.abstract?.trim() || paper.title;
            const evidence: EvidenceChunk[] = [
              {
                chunk_id: `${paper.paper_id}-abstract`,
                paper_id: paper.paper_id,
                paper_title: paper.title,
                section: "Abstract",
                page: null,
                text,
              },
            ];
            next[paper.paper_id] = {
              paper_id: paper.paper_id,
              title: paper.title,
              source: "discovery",
              abstract: paper.abstract,
              evidence,
              pdf_url: paper.pdf_url,
            };
          }
          return next;
        });
      },
      selectedPaperIds,
      toggleSelected: (paperId) =>
        setSelectedPaperIds((prev) => {
          const next = new Set(prev);
          if (next.has(paperId)) next.delete(paperId);
          else next.add(paperId);
          return next;
        }),
      selectedEvidence,
      setFullText: (paperId, chunks) =>
        setLibraryById((prev) => {
          const existing = prev[paperId];
          if (!existing) return prev;
          return {
            ...prev,
            [paperId]: { ...existing, evidence: chunks, fullTextFetched: true },
          };
        }),
    };
  }, [analysesById, opportunities, proposals, libraryById, selectedPaperIds]);

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData(): AppDataValue {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used inside AppDataProvider");
  return ctx;
}
