import { Link } from "react-router-dom";
import {
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Compass,
  FileCheck,
  FileText,
  Layers,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { useAppData } from "../../lib/AppDataContext";

interface PipelineStep {
  id: string;
  number: number;
  label: string;
  tabHref: string;
  icon: React.ComponentType<{ className?: string }>;
  isReady: boolean;
  statusLabel: string;
  canRun: boolean;
  actionName: string;
}

export default function PipelineWorkflowBanner({
  onRunAction,
  isRunning = false,
  runningAction = "",
}: {
  onRunAction?: (actionId: string) => void;
  isRunning?: boolean;
  runningAction?: string;
}) {
  const {
    library,
    selectedPaperIds,
    analyses,
    comparison,
    opportunities,
    proposals,
    feasibility,
    prd,
  } = useAppData();

  const selectedCount = selectedPaperIds.size;
  const hasPapers = selectedCount > 0;
  const hasAnalyses = analyses.length > 0;
  const hasMultipleAnalyses = analyses.length >= 2;
  const hasComparison = !!comparison;
  const hasOpportunities = opportunities.length > 0;
  const hasProposals = proposals.length > 0;
  const hasFeasibility = !!feasibility;
  const hasPrd = !!prd;

  const steps: PipelineStep[] = [
    {
      id: "papers",
      number: 1,
      label: "Papers Context",
      tabHref: "/chat",
      icon: BookOpen,
      isReady: hasPapers,
      statusLabel: hasPapers ? `${selectedCount} Active` : "Select Papers",
      canRun: false,
      actionName: "Select Papers",
    },
    {
      id: "analysis",
      number: 2,
      label: "Paper Analysis",
      tabHref: "/analysis",
      icon: BookOpen,
      isReady: hasAnalyses,
      statusLabel: hasAnalyses ? `${analyses.length} Done` : "Pending",
      canRun: hasPapers,
      actionName: "Analyze Papers",
    },
    {
      id: "qa",
      number: 3,
      label: "Grounded Q&A",
      tabHref: "/qa",
      icon: FileCheck,
      isReady: hasPapers,
      statusLabel: "Evidence Ready",
      canRun: hasPapers,
      actionName: "Ask Questions",
    },
    {
      id: "compare",
      number: 4,
      label: "Comparison",
      tabHref: "/compare",
      icon: Layers,
      isReady: hasComparison,
      statusLabel: hasComparison ? "Matrix Ready" : "Pending",
      canRun: hasMultipleAnalyses,
      actionName: "Compare Papers",
    },
    {
      id: "opportunities",
      number: 5,
      label: "Opportunities",
      tabHref: "/opportunities",
      icon: Target,
      isReady: hasOpportunities,
      statusLabel: hasOpportunities ? `${opportunities.length} Found` : "Pending",
      canRun: hasAnalyses,
      actionName: "Find Opportunities",
    },
    {
      id: "projects",
      number: 6,
      label: "Project Proposals",
      tabHref: "/projects",
      icon: Zap,
      isReady: hasProposals,
      statusLabel: hasProposals ? `${proposals.length} Proposals` : "Pending",
      canRun: hasOpportunities,
      actionName: "Generate Proposals",
    },
    {
      id: "feasibility",
      number: 7,
      label: "Feasibility",
      tabHref: "/feasibility",
      icon: Compass,
      isReady: hasFeasibility,
      statusLabel: hasFeasibility ? "Score: " + feasibility.score + "/100" : "Pending",
      canRun: hasProposals,
      actionName: "Score Feasibility",
    },
    {
      id: "deliverables",
      number: 8,
      label: "PRD & Roadmap",
      tabHref: "/deliverables",
      icon: FileText,
      isReady: hasPrd,
      statusLabel: hasPrd ? "PRD Ready" : "Pending",
      canRun: hasProposals,
      actionName: "Generate PRD",
    },
  ];

  return (
    <div className="bg-card border border-border p-4 mb-5 shadow-2xs font-mono">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-3 border-b border-border/70">
        <div className="flex items-center gap-2">
          <div className="p-1 bg-[#FF6B2C]/10 text-[#FF6B2C]">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Connected Intelligence Pipeline
            </h3>
            <p className="text-[11px] text-muted-foreground">
              Step-by-step progression from paper evidence to feasibility-checked PRD roadmap.
            </p>
          </div>
        </div>

        {/* Live Status indicator */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[11px] text-muted-foreground uppercase">
            Workspace Status:
          </span>
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-[#FF6B2C]/10 text-[#FF6B2C] border border-[#FF6B2C]/30 text-[10px] font-bold uppercase">
            {library.length} In Library • {analyses.length} Analyzed • {proposals.length} Proposals
          </span>
        </div>
      </div>

      {/* Stepper Horizontal Scroll Container */}
      <div className="overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
        <div className="flex items-center gap-2 min-w-[760px]">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isCurrentlyRunning = isRunning && runningAction === step.id;

            return (
              <div key={step.id} className="flex items-center shrink-0">
                <div
                  className={`p-2.5 border transition-all flex flex-col justify-between w-[138px] ${
                    isCurrentlyRunning
                      ? "border-[#FF6B2C] bg-[#FF6B2C]/10 ring-1 ring-[#FF6B2C] animate-pulse"
                      : step.isReady
                      ? "border-emerald-500/50 bg-emerald-500/5"
                      : step.canRun
                      ? "border-[#FF6B2C]/50 bg-card hover:border-[#FF6B2C]"
                      : "border-border/60 bg-foreground/5 opacity-60"
                  }`}
                >
                  {/* Step Top Info */}
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold text-muted-foreground">
                      0{step.number}
                    </span>
                    {step.isReady ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    ) : (
                      <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                    )}
                  </div>

                  {/* Title */}
                  <div className="text-[11px] font-bold text-foreground line-clamp-1">
                    {step.label}
                  </div>

                  {/* Status */}
                  <div
                    className={`text-[10px] mt-0.5 font-medium ${
                      step.isReady
                        ? "text-emerald-600 dark:text-emerald-400 font-semibold"
                        : "text-muted-foreground"
                    }`}
                  >
                    {isCurrentlyRunning ? "Generating..." : step.statusLabel}
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-2.5 pt-2 border-t border-border/60 flex items-center justify-between text-[10px]">
                    {step.canRun && onRunAction ? (
                      <button
                        onClick={() => onRunAction(step.id)}
                        disabled={isRunning}
                        className="text-[#FF6B2C] hover:underline font-bold uppercase cursor-pointer disabled:opacity-50"
                      >
                        Run in Chat
                      </button>
                    ) : (
                      <span className="text-muted-foreground uppercase text-[9px]">
                        {step.isReady ? "Ready" : "Waiting"}
                      </span>
                    )}
                    <Link
                      to={step.tabHref}
                      className="text-muted-foreground hover:text-foreground font-semibold flex items-center gap-0.5"
                      title={`Open ${step.label} Page`}
                    >
                      Tab &rarr;
                    </Link>
                  </div>
                </div>

                {idx < steps.length - 1 && (
                  <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 mx-0.5 shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
