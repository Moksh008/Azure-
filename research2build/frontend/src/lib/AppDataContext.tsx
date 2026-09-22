import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type {
  EvidenceChunk,
  FeasibilityAssessment,
  LibraryPaper,
  OpenAlexPaper,
  PaperAnalysis,
  PaperComparison,
  PRDDocument,
  ProjectProposal,
  ResearchOpportunity,
} from "../types";

interface AppDataValue {
  analyses: PaperAnalysis[];
  addAnalysis: (analysis: PaperAnalysis) => void;
  addAnalyses: (analyses: PaperAnalysis[]) => void;
  comparison: PaperComparison | null;
  setComparison: (comparison: PaperComparison | null) => void;
  opportunities: ResearchOpportunity[];
  setOpportunities: (opportunities: ResearchOpportunity[]) => void;
  proposals: ProjectProposal[];
  setProposals: (proposals: ProjectProposal[]) => void;
  feasibility: FeasibilityAssessment | null;
  setFeasibility: (feasibility: FeasibilityAssessment | null) => void;
  prd: PRDDocument | null;
  setPrd: (prd: PRDDocument | null) => void;

  library: LibraryPaper[];
  addUploadedPaper: (chunks: EvidenceChunk[]) => void;
  addDiscoveredPapers: (papers: OpenAlexPaper[]) => void;
  selectedPaperIds: Set<string>;
  toggleSelected: (paperId: string) => void;
  selectedEvidence: EvidenceChunk[];
  setFullText: (paperId: string, chunks: EvidenceChunk[]) => void;
}

const AppDataContext = createContext<AppDataValue | null>(null);

export function AppDataProvider({ children }: { children: ReactNode }) {
  const [analysesById, setAnalysesById] = useState<Record<string, PaperAnalysis>>({});
  const [comparison, setComparison] = useState<PaperComparison | null>(null);
  const [opportunities, setOpportunities] = useState<ResearchOpportunity[]>([]);
  const [proposals, setProposals] = useState<ProjectProposal[]>([]);
  const [feasibility, setFeasibility] = useState<FeasibilityAssessment | null>(null);
  const [prd, setPrd] = useState<PRDDocument | null>(null);

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
      addAnalyses: (analysesList) =>
        setAnalysesById((prev) => {
          const next = { ...prev };
          for (const a of analysesList) next[a.paper_id] = a;
          return next;
        }),
      comparison,
      setComparison,
      opportunities,
      setOpportunities,
      proposals,
      setProposals,
      feasibility,
      setFeasibility,
      prd,
      setPrd,

      library,
      addUploadedPaper: (chunks) => {
        if (chunks.length === 0) return;
        const chunksByPaper = new Map<string, { title: string; chunks: EvidenceChunk[] }>();
        for (const chunk of chunks) {
          const entry = chunksByPaper.get(chunk.paper_id);
          if (entry) {
            entry.chunks.push(chunk);
          } else {
            chunksByPaper.set(chunk.paper_id, {
              title: chunk.paper_title,
              chunks: [chunk],
            });
          }
        }

        setLibraryById((prev) => {
          const next = { ...prev };
          for (const [paperId, info] of chunksByPaper.entries()) {
            next[paperId] = {
              paper_id: paperId,
              title: info.title,
              source: "upload",
              evidence: info.chunks,
            };
          }
          return next;
        });

        setSelectedPaperIds((prev) => {
          const next = new Set(prev);
          for (const paperId of chunksByPaper.keys()) {
            next.add(paperId);
          }
          return next;
        });
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
  }, [
    analysesById,
    comparison,
    opportunities,
    proposals,
    feasibility,
    prd,
    libraryById,
    selectedPaperIds,
  ]);

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData(): AppDataValue {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used inside AppDataProvider");
  return ctx;
}
