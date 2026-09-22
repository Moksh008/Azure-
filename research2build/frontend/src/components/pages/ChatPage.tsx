import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  analyzePaper,
  ApiError,
  comparePapers,
  downloadPRDMarkdown,
  fetchFullText,
  generatePRD,
  generateProposals,
  getOpportunities,
  scoreFeasibility,
  sendChatMessage,
  uploadPaper,
  uploadPapersBatch,
} from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import { useAuth } from "../../lib/AuthContext";
import {
  saveChatSession,
  loadUserChatSessions,
  loadChatSession,
  deleteChatSession,
  type Turn,
  type ChatSessionMeta,
} from "../../lib/chatService";
import type {
  ChatMessage as ChatMessageType,
  FeasibilityConstraints,
} from "../../types";
import AnalysisCard from "../shared/AnalysisCard";
import {
  CitationList,
  CitationModalProvider,
  EvidencePanel,
} from "../shared/Citation";
import ComparisonTable from "../shared/ComparisonTable";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import OpportunityCard from "../shared/OpportunityCard";
import PaperCard from "../shared/PaperCard";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import ProjectCard from "../shared/ProjectCard";
import PromptInputBox from "../shared/PromptInputBox";
import ScoreCard from "../shared/ScoreCard";
import PageShell from "../PageShell";
import {
  ArrowRight,
  BookOpen,
  Clock,
  Compass,
  Download,
  FileCheck,
  FileText,
  Globe,
  Layers,
  Plus,
  Sparkles,
  Target,
  Trash2,
  Upload,
  Zap,
} from "lucide-react";

const INITIAL_GREETING: Turn = {
  kind: "text",
  role: "assistant",
  content:
    "Welcome to Research2Build Connected Intelligence Copilot. Select papers from your context library, then use the pipeline banner above or ask questions to automatically analyze, compare, discover research opportunities, score feasibility, and generate production PRDs.",
};

const DEFAULT_CONSTRAINTS: FeasibilityConstraints = {
  team_size: 3,
  weeks_available: 8,
  budget_usd: 500,
  skills: ["Python", "FastAPI", "React", "TypeScript", "PyTorch", "NLP"],
};

function generateNewChatId(): string {
  return `chat_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
}

export default function ChatPage() {
  const {
    library,
    addUploadedPaper,
    addDiscoveredPapers,
    selectedPaperIds,
    toggleSelected,
    selectedEvidence,
    setFullText,
    analyses,
    addAnalyses,
    setComparison,
    opportunities,
    setOpportunities,
    proposals,
    setProposals,
    feasibility,
    setFeasibility,
    setPrd,
  } = useAppData();
  const { currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const sessionParam = searchParams.get("session");

  const [activeTab, setActiveTab] = useState<"library" | "history">("library");
  const [currentChatId, setCurrentChatId] = useState<string>(
    sessionParam || generateNewChatId()
  );
  const [chatSessions, setChatSessions] = useState<ChatSessionMeta[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const [turns, setTurns] = useState<Turn[]>([INITIAL_GREETING]);
  const [sending, setSending] = useState(false);
  const [runningAction, setRunningAction] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchingFullTextIds, setFetchingFullTextIds] = useState<Set<string>>(
    new Set()
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load user previous chat sessions from Firestore
  async function refreshHistory() {
    if (!currentUser) return;
    setLoadingHistory(true);
    try {
      const sessions = await loadUserChatSessions(currentUser.uid);
      setChatSessions(sessions);
    } catch (err) {
      console.warn("Failed to load chat history from Firestore:", err);
    } finally {
      setLoadingHistory(false);
    }
  }

  // Persist to Firestore best-effort. The action that produced `updatedTurns`
  // (upload, chat reply, analysis, comparison, ...) has already succeeded
  // and is already reflected in UI state by the time this runs — a Firestore
  // write failure here (e.g. permission rules) must never be reported as if
  // that action itself failed.
  async function persistSession(updatedTurns: Turn[]) {
    if (!currentUser) return;
    try {
      await saveChatSession(
        currentUser.uid,
        currentChatId,
        updatedTurns,
        undefined,
        Array.from(selectedPaperIds)
      );
      refreshHistory();
    } catch (persistErr) {
      console.warn("Failed to save chat session to Firestore", persistErr);
    }
  }

  useEffect(() => {
    if (currentUser) {
      refreshHistory();
    } else {
      setChatSessions([]);
    }
  }, [currentUser]);

  // Sync with URL session query parameter if present
  useEffect(() => {
    async function loadParamSession() {
      if (!currentUser || !sessionParam) return;
      if (sessionParam === currentChatId && turns.length > 1) return;
      try {
        const session = await loadChatSession(currentUser.uid, sessionParam);
        if (session && session.turns.length > 0) {
          setCurrentChatId(session.id);
          setTurns(session.turns);
        }
      } catch (err) {
        console.warn("Failed to load session from URL param", err);
      }
    }
    loadParamSession();
  }, [sessionParam, currentUser]);

  function historyForApi(): ChatMessageType[] {
    return turns
      .filter((t): t is Extract<Turn, { kind: "text" }> => t.kind === "text")
      .map((t) => ({ role: t.role, content: t.content }));
  }

  // General chat message sending
  async function handleSend(
    messageText: string,
    files?: File[],
    _mode?: "chat" | "search" | "think" | "canvas"
  ) {
    const message = messageText.trim();
    if (!message && (!files || files.length === 0)) return;
    if (sending) return;

    setError(null);
    setSending(true);

    const pdfFiles = (files || []).filter(
      (f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf")
    );

    let currentWorkingTurns = [...turns];
    let workingSelectedEvidence = [...selectedEvidence];

    try {
      // If PDF files were attached directly in the prompt box, upload & ingest them in a batch
      if (pdfFiles.length > 0) {
        const uploadUserTurn: Turn = {
          kind: "text",
          role: "user",
          content: `Attached ${pdfFiles.length} paper PDF(s): ${pdfFiles.map((f) => f.name).join(", ")}`,
        };
        currentWorkingTurns = [...currentWorkingTurns, uploadUserTurn];
        setTurns(currentWorkingTurns);

        const chunks =
          pdfFiles.length === 1
            ? await uploadPaper(pdfFiles[0])
            : await uploadPapersBatch(pdfFiles);

        addUploadedPaper(chunks);
        workingSelectedEvidence = [...workingSelectedEvidence, ...chunks];

        const titles = Array.from(new Set(chunks.map((c) => c.paper_title))).filter(Boolean);
        const paperCount = titles.length || pdfFiles.length;
        const displayTitles =
          titles.length <= 3
            ? titles.map((t) => `"${t}"`).join(", ")
            : `${titles.slice(0, 3).map((t) => `"${t}"`).join(", ")} and ${titles.length - 3} more`;

        const uploadAssistantTurn: Turn = {
          kind: "text",
          role: "assistant",
          content: `Uploaded and indexed ${paperCount} paper(s) (${displayTitles}) — extracted ${chunks.length} evidence chunk(s) and added them to your active library context.`,
        };
        currentWorkingTurns = [...currentWorkingTurns, uploadAssistantTurn];
        setTurns(currentWorkingTurns);
      }

      if (message) {
        const userTurn: Turn = { kind: "text", role: "user", content: message };
        currentWorkingTurns = [...currentWorkingTurns, userTurn];
        setTurns(currentWorkingTurns);

        const libraryRefs = library.map((p) => ({
          paper_id: p.paper_id,
          title: p.title,
          source: p.source,
        }));
        const res = await sendChatMessage(
          message,
          historyForApi(),
          libraryRefs,
          workingSelectedEvidence
        );

        const assistantTurn: Turn = {
          kind: "text",
          role: "assistant",
          content: res.reply,
        };
        const finalTurns: Turn[] = [...currentWorkingTurns, assistantTurn];

        if (res.action === "search" && res.discovered_papers?.length) {
          addDiscoveredPapers(res.discovered_papers);
          finalTurns.push({ kind: "papers", papers: res.discovered_papers });
        } else if (res.action === "ask" && res.answer) {
          finalTurns.push({
            kind: "answer",
            question: message,
            answer: res.answer,
          });
        } else if (res.action === "analyze" && res.analyses?.length) {
          addAnalyses(res.analyses);
          finalTurns.push({ kind: "analyses", analyses: res.analyses });
        }

        setTurns(finalTurns);
        await persistSession(finalTurns);
      } else if (currentUser) {
        await persistSession(currentWorkingTurns);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Chat request failed. Is the backend service running?"
      );
    } finally {
      setSending(false);
    }
  }

  // Step-Wise Pipeline Execution triggered from banner or smart chips
  async function handlePipelineAction(actionId: string) {
    setError(null);
    setSending(true);
    setRunningAction(actionId);

    try {
      if (actionId === "analysis") {
        const selectedPapers = library.filter((p) =>
          selectedPaperIds.has(p.paper_id)
        );
        if (selectedPapers.length === 0) {
          setError("Please select at least one paper from the context library.");
          return;
        }

        const userMsg: Turn = {
          kind: "text",
          role: "user",
          content: `Run structured paper analysis on ${selectedPapers.length} selected paper(s).`,
        };
        setTurns((prev) => [...prev, userMsg]);

        const analyzedList = [];
        for (const p of selectedPapers) {
          const res = await analyzePaper(p.paper_id, p.title, p.evidence);
          analyzedList.push(res);
        }

        addAnalyses(analyzedList);
        const resultTurn: Turn = { kind: "analyses", analyses: analyzedList };
        const updated = [...turns, userMsg, resultTurn];
        setTurns(updated);

        await persistSession(updated);
      } else if (actionId === "compare") {
        if (analyses.length < 2) {
          setError(
            "Comparative analysis requires at least 2 analyzed papers. Run paper analysis first."
          );
          return;
        }

        const userMsg: Turn = {
          kind: "text",
          role: "user",
          content: "Generate cross-paper comparative matrix across analyzed literature.",
        };
        setTurns((prev) => [...prev, userMsg]);

        const compResult = await comparePapers(analyses);
        setComparison(compResult);

        const compTurn: Turn = { kind: "comparison", comparison: compResult };
        const updated = [...turns, userMsg, compTurn];
        setTurns(updated);

        await persistSession(updated);
      } else if (actionId === "opportunities") {
        if (analyses.length === 0) {
          setError("Analyze papers first before discovering research opportunities.");
          return;
        }

        const userMsg: Turn = {
          kind: "text",
          role: "user",
          content: "Synthesize recurring limitations and identify potential research opportunities.",
        };
        setTurns((prev) => [...prev, userMsg]);

        const oppResult = await getOpportunities(analyses);
        setOpportunities(oppResult);

        const oppTurn: Turn = { kind: "opportunities", opportunities: oppResult };
        const updated = [...turns, userMsg, oppTurn];
        setTurns(updated);

        await persistSession(updated);
      } else if (actionId === "projects") {
        if (opportunities.length === 0) {
          setError("Identify research opportunities first before generating project proposals.");
          return;
        }

        const userMsg: Turn = {
          kind: "text",
          role: "user",
          content: "Generate concrete engineering project proposals grounded in identified opportunities.",
        };
        setTurns((prev) => [...prev, userMsg]);

        const propResult = await generateProposals(opportunities);
        setProposals(propResult);

        const propTurn: Turn = { kind: "proposals", proposals: propResult };
        const updated = [...turns, userMsg, propTurn];
        setTurns(updated);

        await persistSession(updated);
      } else if (actionId === "feasibility") {
        if (proposals.length === 0) {
          setError("Generate a project proposal first before assessing feasibility.");
          return;
        }

        const targetProposal = proposals[0];
        const userMsg: Turn = {
          kind: "text",
          role: "user",
          content: `Assess feasibility and risk score for proposal: "${targetProposal.title}".`,
        };
        setTurns((prev) => [...prev, userMsg]);

        const scoreResult = await scoreFeasibility(targetProposal, DEFAULT_CONSTRAINTS);
        setFeasibility(scoreResult);

        const feasTurn: Turn = {
          kind: "feasibility",
          proposal: targetProposal,
          assessment: scoreResult,
        };
        const updated = [...turns, userMsg, feasTurn];
        setTurns(updated);

        await persistSession(updated);
      } else if (actionId === "deliverables") {
        if (proposals.length === 0) {
          setError("Generate project proposals first to build the PRD and roadmap.");
          return;
        }

        const targetProposal = proposals[0];
        const targetOpp = opportunities[0];
        const userMsg: Turn = {
          kind: "text",
          role: "user",
          content: `Generate production-ready PRD and engineering roadmap for "${targetProposal.title}".`,
        };
        setTurns((prev) => [...prev, userMsg]);

        const prdResult = await generatePRD(targetProposal, targetOpp, feasibility || undefined);
        setPrd(prdResult);

        const prdTurn: Turn = {
          kind: "prd",
          prd: prdResult,
          proposal: targetProposal,
        };
        const updated = [...turns, userMsg, prdTurn];
        setTurns(updated);

        await persistSession(updated);
      }
    } catch (err: any) {
      setError(err instanceof ApiError ? err.message : "Pipeline step execution failed.");
    } finally {
      setSending(false);
      setRunningAction("");
    }
  }

  function handleNewChat() {
    const newId = generateNewChatId();
    setCurrentChatId(newId);
    setTurns([INITIAL_GREETING]);
    setError(null);
    setSearchParams({});
  }

  async function handleSelectSession(sessionMeta: ChatSessionMeta) {
    if (!currentUser) return;
    setError(null);
    try {
      const session = await loadChatSession(currentUser.uid, sessionMeta.id);
      if (session && session.turns.length > 0) {
        setCurrentChatId(session.id);
        setTurns(session.turns);
        setSearchParams({ session: session.id });
      }
    } catch (err) {
      setError("Failed to load conversation history from Firestore.");
    }
  }

  async function handleDeleteSession(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation();
    if (!currentUser) return;
    try {
      await deleteChatSession(currentUser.uid, sessionId);
      setChatSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentChatId === sessionId) {
        handleNewChat();
      }
    } catch (err) {
      console.error("Failed to delete chat session", err);
    }
  }

  async function handleFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files;
    e.target.value = "";
    if (!fileList || fileList.length === 0) return;

    const selectedFiles = Array.from(fileList);
    setUploading(true);
    setError(null);
    try {
      const chunks =
        selectedFiles.length === 1
          ? await uploadPaper(selectedFiles[0])
          : await uploadPapersBatch(selectedFiles);

      addUploadedPaper(chunks);
      const titles = Array.from(new Set(chunks.map((c) => c.paper_title))).filter(Boolean);
      const paperCount = titles.length || selectedFiles.length;
      const displayTitle =
        titles.length <= 3
          ? titles.map((t) => `"${t}"`).join(", ")
          : `${titles.slice(0, 3).map((t) => `"${t}"`).join(", ")} and ${titles.length - 3} more`;

      const newTurns: Turn[] = [
        ...turns,
        {
          kind: "text",
          role: "assistant",
          content: `Uploaded and indexed ${paperCount} paper(s) (${displayTitle}) — extracted ${chunks.length} chunk(s) and selected them for your active workspace. You can now ask questions, compare, or run analysis.`,
        },
      ];
      setTurns(newTurns);
      await persistSession(newTurns);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Upload failed. Is the backend service running?"
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleFetchFullText(
    paperId: string,
    title: string,
    pdfUrl: string
  ) {
    setFetchingFullTextIds((prev) => new Set(prev).add(paperId));
    setError(null);
    try {
      const chunks = await fetchFullText(paperId, title, pdfUrl);
      setFullText(paperId, chunks);
      const newTurns: Turn[] = [
        ...turns,
        {
          kind: "text",
          role: "assistant",
          content: `Fetched the full text of "${title}" (${chunks.length} chunk(s)) — questions and analysis will now use the whole paper, not just its abstract.`,
        },
      ];
      setTurns(newTurns);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Couldn't fetch the full PDF — it may not be freely accessible."
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
      title="AI Research Copilot"
      description="Integrated end-to-end intelligence workflow. Run structured analysis, comparative matrices, opportunity discovery, feasibility scoring, and PRDs step-by-step in chat."
    >
      <CitationModalProvider>
        {/* Top Interactive Pipeline Workflow Banner */}
        <PipelineWorkflowBanner
          onRunAction={handlePipelineAction}
          isRunning={sending}
          runningAction={runningAction}
        />

        <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
          {/* Workspace Left Drawer: Library & Chat History */}
          <aside className="bg-card rounded-none border border-border p-4 h-fit lg:sticky lg:top-24 space-y-4 shadow-2xs font-mono">
            {/* New Chat Button */}
            <button
              onClick={handleNewChat}
              className="w-full bg-[#FF6B2C] hover:bg-[#FF6B2C]/90 text-white text-xs font-bold py-2.5 px-4 flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>New Research Chat</span>
            </button>

            {/* Tab Selector: Context Library vs History */}
            <div className="flex border border-border bg-foreground/5 p-0.5">
              <button
                onClick={() => setActiveTab("library")}
                className={`flex-1 py-1.5 text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  activeTab === "library"
                    ? "bg-card text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <BookOpen className="w-3.5 h-3.5 text-[#FF6B2C]" />
                <span>Library ({library.length})</span>
              </button>
              <button
                onClick={() => setActiveTab("history")}
                className={`flex-1 py-1.5 text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  activeTab === "history"
                    ? "bg-card text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Clock className="w-3.5 h-3.5 text-[#FF6B2C]" />
                <span>History ({chatSessions.length})</span>
              </button>
            </div>

            {/* TAB 1: Context Library */}
            {activeTab === "library" && (
              <div className="space-y-3 pt-1">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  multiple
                  className="sr-only"
                  onChange={handleFileChosen}
                />

                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="w-full bg-[#1F2023] hover:bg-black text-white text-xs font-bold py-2 px-3 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
                >
                  <Upload className="w-3.5 h-3.5 text-[#FF6B2C]" />
                  {uploading ? "Extracting Chunks..." : "Upload PDFs (Multiple)"}
                </button>

                {library.length === 0 ? (
                  <div className="text-center py-6 px-2 text-muted-foreground text-xs space-y-1.5">
                    <p>No papers in active context.</p>
                    <p className="text-[11px]">
                      Search a topic or upload a PDF to index chunks into memory.
                    </p>
                  </div>
                ) : (
                  <ul className="space-y-2 max-h-[50vh] overflow-y-auto pr-1">
                    {library.map((p) => {
                      const fetchingFullText = fetchingFullTextIds.has(p.paper_id);
                      const canFetchFullText =
                        p.source === "discovery" &&
                        p.pdf_url &&
                        !p.fullTextFetched;
                      const isSelected = selectedPaperIds.has(p.paper_id);

                      return (
                        <li key={p.paper_id} className="space-y-1">
                          <button
                            onClick={() => toggleSelected(p.paper_id)}
                            aria-pressed={isSelected}
                            className={`w-full text-left p-2.5 border text-xs transition-all cursor-pointer ${
                              isSelected
                                ? "border-[#FF6B2C] bg-[#FF6B2C]/5 text-foreground font-semibold"
                                : "border-border hover:bg-foreground/5 text-muted-foreground"
                            }`}
                          >
                            <p className="line-clamp-2 leading-tight">{p.title}</p>
                            <div className="flex items-center justify-between mt-1 text-[10px] text-muted-foreground uppercase">
                              <span>{p.source}</span>
                              {p.fullTextFetched && (
                                <span className="text-[#FF6B2C] font-semibold">
                                  Full Text
                                </span>
                              )}
                            </div>
                          </button>
                          {canFetchFullText && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleFetchFullText(
                                  p.paper_id,
                                  p.title,
                                  p.pdf_url!
                                );
                              }}
                              disabled={fetchingFullText}
                              className="w-full text-left text-[11px] font-semibold text-[#FF6B2C] hover:underline px-1 cursor-pointer disabled:opacity-50"
                            >
                              {fetchingFullText
                                ? "Fetching PDF..."
                                : "Fetch Full Text"}
                            </button>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            )}

            {/* TAB 2: Firestore Chat History */}
            {activeTab === "history" && (
              <div className="space-y-2 pt-1">
                {loadingHistory ? (
                  <div className="py-8 text-center text-xs text-muted-foreground animate-pulse">
                    Loading Firestore history...
                  </div>
                ) : chatSessions.length === 0 ? (
                  <div className="text-center py-6 px-2 text-muted-foreground text-xs space-y-1">
                    <p>No saved conversations yet.</p>
                    <p className="text-[11px]">
                      Your chats will automatically be saved to Firestore.
                    </p>
                  </div>
                ) : (
                  <ul className="space-y-2 max-h-[50vh] overflow-y-auto pr-1">
                    {chatSessions.map((session) => {
                      const isActive = session.id === currentChatId;
                      return (
                        <li key={session.id}>
                          <div
                            onClick={() => handleSelectSession(session)}
                            className={`p-2.5 border text-xs transition-all cursor-pointer flex items-center justify-between group ${
                              isActive
                                ? "border-[#FF6B2C] bg-[#FF6B2C]/10 text-foreground font-bold"
                                : "border-border hover:bg-foreground/5 text-muted-foreground"
                            }`}
                          >
                            <div className="overflow-hidden pr-2">
                              <p className="line-clamp-1 text-foreground">
                                {session.title}
                              </p>
                              <p className="text-[10px] text-muted-foreground mt-0.5">
                                {new Date(session.updatedAt).toLocaleDateString()}{" "}
                                • {session.messageCount} turns
                              </p>
                            </div>
                            <button
                              onClick={(e) => handleDeleteSession(e, session.id)}
                              className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-500 p-0.5 transition-opacity cursor-pointer shrink-0"
                              title="Delete conversation"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            )}
          </aside>

          {/* Main Chat Stream & Input Area */}
          <div className="flex flex-col min-h-[600px] justify-between">
            <div className="space-y-5 mb-6">
              {/* Quick Pipeline Navigation Chips */}
              <div className="flex flex-wrap items-center gap-2 p-3 bg-card border border-border/80 font-mono text-xs">
                <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-[#FF6B2C]" /> Quick Actions:
                </span>
                <button
                  onClick={() => handlePipelineAction("analysis")}
                  disabled={selectedPaperIds.size === 0 || sending}
                  className="px-2.5 py-1 bg-foreground/5 hover:bg-[#FF6B2C] hover:text-white border border-border text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40"
                >
                  🔍 Analyze Papers
                </button>
                <button
                  onClick={() => handlePipelineAction("compare")}
                  disabled={analyses.length < 2 || sending}
                  className="px-2.5 py-1 bg-foreground/5 hover:bg-[#FF6B2C] hover:text-white border border-border text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40"
                >
                  📊 Compare Matrix
                </button>
                <button
                  onClick={() => handlePipelineAction("opportunities")}
                  disabled={analyses.length === 0 || sending}
                  className="px-2.5 py-1 bg-foreground/5 hover:bg-[#FF6B2C] hover:text-white border border-border text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40"
                >
                  💡 Find Opportunities
                </button>
                <button
                  onClick={() => handlePipelineAction("projects")}
                  disabled={opportunities.length === 0 || sending}
                  className="px-2.5 py-1 bg-foreground/5 hover:bg-[#FF6B2C] hover:text-white border border-border text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40"
                >
                  🚀 Generate Projects
                </button>
                <button
                  onClick={() => handlePipelineAction("feasibility")}
                  disabled={proposals.length === 0 || sending}
                  className="px-2.5 py-1 bg-foreground/5 hover:bg-[#FF6B2C] hover:text-white border border-border text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40"
                >
                  ⚖️ Score Feasibility
                </button>
                <button
                  onClick={() => handlePipelineAction("deliverables")}
                  disabled={proposals.length === 0 || sending}
                  className="px-2.5 py-1 bg-foreground/5 hover:bg-[#FF6B2C] hover:text-white border border-border text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40"
                >
                  📋 Build PRD
                </button>
              </div>

              {/* Turns Stream */}
              {turns.map((turn, i) => {
                if (turn.kind === "text") {
                  const isUser = turn.role === "user";
                  return (
                    <div
                      key={i}
                      className={`max-w-[90%] rounded-none p-4 font-mono text-sm leading-relaxed ${
                        isUser
                          ? "bg-[#1F2023] text-white ml-auto border border-black shadow-xs"
                          : "bg-card border border-border text-foreground shadow-2xs"
                      }`}
                    >
                      <div className="text-[10px] uppercase tracking-wider mb-1 font-bold text-muted-foreground">
                        {isUser ? "You" : "Research2Build Copilot"}
                      </div>
                      <div className="whitespace-pre-wrap">{turn.content}</div>
                    </div>
                  );
                }

                if (turn.kind === "papers") {
                  return (
                    <div key={i} className="space-y-3 font-mono">
                      <div className="text-xs uppercase font-bold text-[#FF6B2C] flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5" /> Discovered Academic Papers ({turn.papers.length})
                      </div>
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
                    <div
                      key={i}
                      className="bg-card rounded-none border border-border p-6 font-mono space-y-3 shadow-sm"
                    >
                      <div className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                        <FileCheck className="w-4 h-4" /> Grounded Evidence Answer
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Q: {turn.question}
                      </p>
                      <p className="text-sm text-foreground leading-relaxed">
                        {turn.answer.answer}
                      </p>
                      {!turn.answer.evidence_sufficient && (
                        <p className="text-xs text-red-500 font-semibold">
                          Evidence insufficient — treat this answer with caution.
                        </p>
                      )}
                      <CitationList citations={turn.answer.citations} />
                      <EvidencePanel citations={turn.answer.citations} />
                    </div>
                  );
                }

                if (turn.kind === "analyses") {
                  return (
                    <div key={i} className="space-y-4 font-mono">
                      <div className="flex items-center justify-between p-3 bg-card border border-border">
                        <span className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                          <BookOpen className="w-4 h-4" /> Structured Paper Analyses ({turn.analyses.length})
                        </span>
                        <Link
                          to="/analysis"
                          className="text-xs font-bold uppercase text-ink hover:text-[#FF6B2C] flex items-center gap-1"
                        >
                          Open in Full Analysis Tab <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                      <div className="space-y-4">
                        {turn.analyses.map((a) => (
                          <AnalysisCard key={a.paper_id} analysis={a} />
                        ))}
                      </div>
                    </div>
                  );
                }

                if (turn.kind === "comparison") {
                  return (
                    <div key={i} className="space-y-3 font-mono">
                      <div className="flex items-center justify-between p-3 bg-card border border-border">
                        <span className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                          <Layers className="w-4 h-4" /> Cross-Paper Comparative Matrix
                        </span>
                        <Link
                          to="/compare"
                          className="text-xs font-bold uppercase text-ink hover:text-[#FF6B2C] flex items-center gap-1"
                        >
                          Open in Matrix Tab <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                      <div className="bg-card border border-border p-4 shadow-sm overflow-x-auto">
                        <ComparisonTable comparison={turn.comparison} />
                      </div>
                    </div>
                  );
                }

                if (turn.kind === "opportunities") {
                  return (
                    <div key={i} className="space-y-3 font-mono">
                      <div className="flex items-center justify-between p-3 bg-card border border-border">
                        <span className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                          <Target className="w-4 h-4" /> Identified Research Opportunities ({turn.opportunities.length})
                        </span>
                        <Link
                          to="/opportunities"
                          className="text-xs font-bold uppercase text-ink hover:text-[#FF6B2C] flex items-center gap-1"
                        >
                          Open in Opportunities Tab <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                      {turn.opportunities.length > 0 ? (
                        <div className="space-y-3">
                          {turn.opportunities.map((opp) => (
                            <OpportunityCard key={opp.opportunity_id} opportunity={opp} />
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground p-3">
                          No recurring opportunities — a limitation only counts once it appears in at
                          least two analyzed papers. Analyze another related paper and try again.
                        </p>
                      )}
                    </div>
                  );
                }

                if (turn.kind === "proposals") {
                  return (
                    <div key={i} className="space-y-3 font-mono">
                      <div className="flex items-center justify-between p-3 bg-card border border-border">
                        <span className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                          <Zap className="w-4 h-4" /> Generated Project Proposals ({turn.proposals.length})
                        </span>
                        <Link
                          to="/projects"
                          className="text-xs font-bold uppercase text-ink hover:text-[#FF6B2C] flex items-center gap-1"
                        >
                          Open in Projects Tab <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                      <div className="space-y-3">
                        {turn.proposals.map((proj) => (
                          <ProjectCard key={proj.proposal_id} proposal={proj} />
                        ))}
                      </div>
                    </div>
                  );
                }

                if (turn.kind === "feasibility") {
                  return (
                    <div key={i} className="space-y-3 font-mono">
                      <div className="flex items-center justify-between p-3 bg-card border border-border">
                        <span className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                          <Compass className="w-4 h-4" /> Feasibility & Risk Assessment
                        </span>
                        <Link
                          to="/feasibility"
                          className="text-xs font-bold uppercase text-ink hover:text-[#FF6B2C] flex items-center gap-1"
                        >
                          Open in Feasibility Dashboard <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                      <ScoreCard
                        assessment={turn.assessment}
                      />
                    </div>
                  );
                }

                if (turn.kind === "prd") {
                  return (
                    <div key={i} className="space-y-3 font-mono">
                      <div className="flex items-center justify-between p-3 bg-card border border-border">
                        <span className="text-xs font-bold uppercase text-[#FF6B2C] flex items-center gap-1.5">
                          <FileText className="w-4 h-4" /> Production PRD Document
                        </span>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() =>
                              downloadPRDMarkdown(
                                turn.prd,
                                `# ${turn.prd.title}\n\n${turn.prd.problem_statement}\n\n## Solution Summary\n${turn.prd.solution_summary}\n\n## Feasibility\n${turn.prd.feasibility_summary}`
                              )
                            }
                            className="text-xs font-bold uppercase text-[#FF6B2C] hover:underline flex items-center gap-1 cursor-pointer"
                          >
                            <Download className="w-3.5 h-3.5" /> Download .md
                          </button>
                          <Link
                            to="/deliverables"
                            className="text-xs font-bold uppercase text-ink hover:text-[#FF6B2C] flex items-center gap-1"
                          >
                            Open in Deliverables Tab <ArrowRight className="w-3 h-3" />
                          </Link>
                        </div>
                      </div>
                      <div className="bg-card border border-border p-6 shadow-sm space-y-4">
                        <h4 className="text-base font-bold text-ink">
                          {turn.prd.title}
                        </h4>
                        <div>
                          <p className="text-[10px] uppercase font-bold text-muted-foreground">
                            Problem Statement
                          </p>
                          <p className="text-xs text-ink leading-relaxed mt-1">
                            {turn.prd.problem_statement}
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-bold text-muted-foreground">
                            Solution Architecture & Summary
                          </p>
                          <p className="text-xs text-ink leading-relaxed mt-1">
                            {turn.prd.solution_summary}
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-bold text-muted-foreground">
                            Feasibility Summary
                          </p>
                          <p className="text-xs text-ink leading-relaxed mt-1">
                            {turn.prd.feasibility_summary}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                }

                return null;
              })}

              {sending && (
                <LoadingState
                  label={
                    runningAction
                      ? `Running ${runningAction} across research evidence...`
                      : "Synthesizing citations and reasoning across evidence..."
                  }
                />
              )}
              {error && <ErrorState message={error} onRetry={() => {}} />}
            </div>

            {/* Bottom Multi-Modal PromptInputBox */}
            <div className="sticky bottom-4 pt-2">
              <PromptInputBox
                isLoading={sending}
                onSend={handleSend}
                placeholder="Ask a question, search literature, or run any pipeline step..."
              />
            </div>
          </div>
        </div>
      </CitationModalProvider>
    </PageShell>
  );
}
