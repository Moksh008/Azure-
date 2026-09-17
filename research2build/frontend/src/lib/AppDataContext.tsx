import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { PaperAnalysis, ProjectProposal, ResearchOpportunity } from "../types";

interface AppDataValue {
  analyses: PaperAnalysis[];
  addAnalysis: (analysis: PaperAnalysis) => void;
  opportunities: ResearchOpportunity[];
  setOpportunities: (opportunities: ResearchOpportunity[]) => void;
  proposals: ProjectProposal[];
  setProposals: (proposals: ProjectProposal[]) => void;
}

const AppDataContext = createContext<AppDataValue | null>(null);

/**
 * Session-only (in-memory, not persisted) store so pages can chain the
 * pipeline — analysis -> comparison -> opportunities -> proposals — without
 * a backend database. Matches the stateless design of the M4 modules: the
 * server never resolves IDs, callers always pass the objects they already
 * hold, and this context is just where the frontend keeps hold of them.
 */
export function AppDataProvider({ children }: { children: ReactNode }) {
  const [analysesById, setAnalysesById] = useState<Record<string, PaperAnalysis>>({});
  const [opportunities, setOpportunities] = useState<ResearchOpportunity[]>([]);
  const [proposals, setProposals] = useState<ProjectProposal[]>([]);

  const value = useMemo<AppDataValue>(
    () => ({
      analyses: Object.values(analysesById),
      addAnalysis: (analysis) =>
        setAnalysesById((prev) => ({ ...prev, [analysis.paper_id]: analysis })),
      opportunities,
      setOpportunities,
      proposals,
      setProposals,
    }),
    [analysesById, opportunities, proposals],
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData(): AppDataValue {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used inside AppDataProvider");
  return ctx;
}
