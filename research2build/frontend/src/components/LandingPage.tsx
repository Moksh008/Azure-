import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  BarChart,
  Bird,
  BookOpen,
  ChevronRight,
  Compass,
  FileCheck,
  FileText,
  Layers,
  Menu,
  MessageSquare,
  Plug,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  Zap,
  LogOut,
  User as UserIcon,
} from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { motion, useAnimation, useInView } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useAuth } from "../lib/AuthContext";

const navigationItems = [
  { title: "ANALYSIS", href: "/analysis" },
  { title: "Q&A", href: "/qa" },
  { title: "OPPORTUNITIES", href: "/opportunities" },
  { title: "ROADMAP", href: "/feasibility" },
];

const labels = [
  { icon: Sparkles, label: "Predictive Analytics" },
  { icon: Plug, label: "Machine Learning" },
  { icon: Activity, label: "Natural Language Processing" },
  { icon: FileCheck, label: "Evidence-Grounded Citations" },
];

const features = [
  {
    icon: BarChart,
    label: "Advanced Analytics",
    description:
      "Deconstruct complex academic literature into structured findings, methodology comparisons, and limitation matrices.",
    actionUrl: "/analysis",
    actionLabel: "Explore Analysis",
  },
  {
    icon: Zap,
    label: "Intelligent Automation",
    description:
      "Transform recurring paper limitations into validated research opportunities and feasibility-scored project blueprints.",
    actionUrl: "/opportunities",
    actionLabel: "View Opportunities",
  },
  {
    icon: Activity,
    label: "Real-time Insights",
    description:
      "Ask nuanced questions across your research library with verified page & section citations and zero hallucinations.",
    actionUrl: "/qa",
    actionLabel: "Ask Library",
  },
];

const platformModules = [
  {
    icon: Search,
    title: "Multi-Source Discovery",
    desc: "Search over 250M+ academic papers across OpenAlex and CORE with instant relevance filtering.",
    href: "/discover",
    tag: "OpenAlex & CORE",
  },
  {
    icon: Upload,
    title: "PDF Ingestion & Extraction",
    desc: "Upload PDFs with automatic section detection, OCR fallback, and structured chunk indexing.",
    href: "/upload",
    tag: "ChromaDB / Azure",
  },
  {
    icon: BookOpen,
    title: "Paper Deep-Dive",
    desc: "Extract problems, methodologies, key findings, limitations, and future directions automatically.",
    href: "/analysis",
    tag: "Structured JSON",
  },
  {
    icon: Layers,
    title: "Comparative Matrix",
    desc: "Side-by-side comparative analysis of datasets, baselines, compute constraints, and trade-offs.",
    href: "/compare",
    tag: "Multi-Paper",
  },
  {
    icon: MessageSquare,
    title: "Grounded Q&A Engine",
    desc: "Pose complex questions and receive synthesized answers with direct verbatim quotes and page numbers.",
    href: "/qa",
    tag: "Traceable Citations",
  },
  {
    icon: Target,
    title: "Opportunity Discovery",
    desc: "Identify cross-paper research gaps, recurring roadblocks, and promising unexplored engineering avenues.",
    href: "/opportunities",
    tag: "Novelty Hedge",
  },
  {
    icon: Compass,
    title: "Feasibility Assessment",
    desc: "Score project proposals against team size, timelines, budget, and required technical skills.",
    href: "/feasibility",
    tag: "Risk Matrix",
  },
  {
    icon: FileText,
    title: "PRD & Roadmap Generator",
    desc: "Generate production-ready Product Requirement Documents and step-by-step engineering sprints.",
    href: "/deliverables",
    tag: "Export Ready",
  },
];

const sampleCitations = [
  {
    quote:
      "Latency and communication overhead remain the primary bottleneck in distributed LLM fine-tuning.",
    paper: "Federated Learning at Scale: Communication-Efficient Algorithms",
    section: "Limitations & Scaling Challenges",
    page: 7,
    tag: "Verified Evidence",
  },
  {
    quote:
      "We achieve 4.2x speedup by quantizing attention weights and caching intermediate KV activations.",
    paper: "Efficient Cross-Attention with Low-Rank Approximation",
    section: "Empirical Results",
    page: 12,
    tag: "Verified Evidence",
  },
  {
    quote:
      "Current multimodal architectures fail to preserve topological constraints in spatial reasoning tasks.",
    paper: "Multimodal Geospatial Reasoning & Tool-Augmented Agents",
    section: "Discussion",
    page: 5,
    tag: "Verified Evidence",
  },
];

export function MynaHero() {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const controls = useAnimation();
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });
  const [activeEvidenceIndex, setActiveEvidenceIndex] = React.useState(0);

  React.useEffect(() => {
    if (isInView) {
      controls.start("visible");
    }
  }, [controls, isInView]);

  const titleWords = [
    "THE",
    "AI",
    "REVOLUTION",
    "FOR",
    "BUSINESS",
    "INTELLIGENCE",
  ];

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-[#FF6B2C] selection:text-white">
      {/* Top Header */}
      <header className="sticky top-0 z-40 w-full border-b border-border/80 bg-background/95 backdrop-blur-md">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 bg-[#FF6B2C]/10 text-[#FF6B2C] group-hover:bg-[#FF6B2C] group-hover:text-white transition-all">
                  <Bird className="h-6 w-6" />
                </div>
                <div className="flex flex-col">
                  <span className="font-mono text-xl font-bold tracking-tight text-foreground">
                    Research<span className="text-[#FF6B2C]">2</span>Build
                  </span>
                  <span className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground -mt-1">
                    Myna AI Core
                  </span>
                </div>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center space-x-6 xl:space-x-8">
              {navigationItems.map((item) => (
                <Link
                  key={item.title}
                  to={item.href}
                  className="text-xs font-mono uppercase tracking-wider text-muted-foreground hover:text-[#FF6B2C] transition-colors py-1 relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-[2px] after:bg-[#FF6B2C] hover:after:w-full after:transition-all"
                >
                  {item.title}
                </Link>
              ))}
            </nav>

            <div className="flex items-center space-x-3 sm:space-x-4">
              <Link to="/chat" className="hidden sm:inline-block">
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-none border-foreground/20 font-mono text-xs hover:border-[#FF6B2C] hover:text-[#FF6B2C]"
                >
                  <MessageSquare className="w-3.5 h-3.5 mr-1.5 text-[#FF6B2C]" />
                  AI COPILOT
                </Button>
              </Link>
              {currentUser ? (
                <div className="hidden md:flex items-center gap-2 font-mono text-xs">
                  <div className="w-7 h-7 rounded-full bg-[#1F2023] text-white flex items-center justify-center text-xs font-bold">
                    {currentUser.email ? currentUser.email[0].toUpperCase() : "U"}
                  </div>
                  <button
                    onClick={() => logout()}
                    className="p-1.5 text-muted-foreground hover:text-red-500 cursor-pointer"
                    title="Sign Out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <Link to="/login" className="hidden md:inline-block">
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-none font-mono text-xs uppercase"
                  >
                    <UserIcon className="w-3.5 h-3.5 mr-1.5 text-[#FF6B2C]" />
                    SIGN IN
                  </Button>
                </Link>
              )}
              <Button
                onClick={() => navigate(currentUser ? "/chat" : "/discover")}
                variant="default"
                size="sm"
                className="rounded-none hidden md:inline-flex bg-[#FF6B2C] hover:bg-[#FF6B2C]/90 font-mono text-xs uppercase tracking-wider font-semibold shadow-xs"
              >
                GET STARTED <ArrowRight className="ml-1.5 w-3.5 h-3.5" />
              </Button>

              {/* Mobile Drawer */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" className="lg:hidden rounded-none">
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle menu</span>
                  </Button>
                </SheetTrigger>
                <SheetContent side="right">
                  <div className="flex flex-col gap-6 mt-6">
                    <div className="flex items-center space-x-2 pb-4 border-b border-border">
                      <Bird className="h-6 w-6 text-[#FF6B2C]" />
                      <span className="font-mono text-lg font-bold">Research2Build</span>
                    </div>
                    <nav className="flex flex-col gap-3">
                      {navigationItems.map((item) => (
                        <Link
                          key={item.title}
                          to={item.href}
                          className="text-sm font-mono uppercase text-foreground hover:text-[#FF6B2C] transition-colors p-2 hover:bg-foreground/5"
                        >
                          {item.title}
                        </Link>
                      ))}
                      <Link
                        to="/chat"
                        className="text-sm font-mono uppercase text-foreground hover:text-[#FF6B2C] transition-colors p-2 hover:bg-foreground/5 flex items-center justify-between"
                      >
                        <span>AI RESEARCH COPILOT</span>
                        <Sparkles className="w-4 h-4 text-[#FF6B2C]" />
                      </Link>
                    </nav>
                    <div className="pt-4 border-t border-border flex flex-col gap-2">
                      <Button
                        onClick={() => navigate("/discover")}
                        className="w-full cursor-pointer rounded-none bg-[#FF6B2C] hover:bg-[#FF6B2C]/90 font-mono text-xs uppercase font-bold"
                      >
                        GET STARTED <ArrowRight className="ml-1 w-4 h-4" />
                      </Button>
                      <Button
                        onClick={() => navigate("/upload")}
                        variant="outline"
                        className="w-full rounded-none font-mono text-xs uppercase"
                      >
                        UPLOAD PAPERS
                      </Button>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-24 md:pt-24 md:pb-32">
          <div className="flex flex-col items-center text-center max-w-5xl mx-auto">
            {/* Live badge */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 mb-8 border border-[#FF6B2C]/30 bg-[#FF6B2C]/5 font-mono text-xs uppercase tracking-widest text-[#FF6B2C]"
            >
              <span className="inline-block w-2 h-2 rounded-full bg-[#FF6B2C] animate-pulse" />
              Evidence-Grounded Research & Engineering Engine
            </motion.div>

            {/* Staggered Animated Title Words */}
            <motion.h1
              initial={{ filter: "blur(10px)", opacity: 0, y: 40 }}
              animate={{ filter: "blur(0px)", opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="relative font-mono text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl max-w-4xl mx-auto leading-tight md:leading-none text-foreground"
            >
              {titleWords.map((text, index) => (
                <motion.span
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    delay: index * 0.12,
                    duration: 0.5,
                  }}
                  className={`inline-block mx-1.5 sm:mx-2.5 md:mx-3 ${
                    text === "AI" || text === "INTELLIGENCE"
                      ? "text-[#FF6B2C]"
                      : ""
                  }`}
                >
                  {text}
                </motion.span>
              ))}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9, duration: 0.6 }}
              className="mx-auto mt-8 max-w-2xl text-base sm:text-lg md:text-xl text-muted-foreground font-mono leading-relaxed"
            >
              We empower researchers and engineering teams with cutting-edge AI solutions to transform
              unstructured research papers into evidence-backed, feasibility-scored product blueprints.
            </motion.p>

            {/* Feature Label Badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2, duration: 0.6 }}
              className="mt-10 flex flex-wrap justify-center gap-3 sm:gap-4 md:gap-6"
            >
              {labels.map((feature, index) => (
                <motion.div
                  key={feature.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    delay: 1.2 + index * 0.1,
                    duration: 0.5,
                    type: "spring",
                    stiffness: 100,
                    damping: 10,
                  }}
                  className="flex items-center gap-2 px-3.5 py-1.5 bg-background border border-border/80 shadow-2xs hover:border-[#FF6B2C]/60 transition-colors"
                >
                  <feature.icon className="h-4 w-4 text-[#FF6B2C]" />
                  <span className="text-xs sm:text-sm font-mono text-foreground font-medium">
                    {feature.label}
                  </span>
                </motion.div>
              ))}
            </motion.div>

            {/* Hero CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 1.6,
                duration: 0.6,
                type: "spring",
                stiffness: 100,
                damping: 10,
              }}
              className="mt-10 flex flex-col sm:flex-row items-center gap-4 w-full justify-center"
            >
              <Button
                onClick={() => navigate(currentUser ? "/chat" : "/login")}
                size="lg"
                className="w-full sm:w-auto cursor-pointer rounded-none bg-[#FF6B2C] hover:bg-[#FF6B2C]/90 font-mono text-sm uppercase tracking-wider font-bold shadow-md h-12 px-8"
              >
                GET STARTED <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <Button
                onClick={() => navigate(currentUser ? "/upload" : "/login")}
                variant="outline"
                size="lg"
                className="w-full sm:w-auto rounded-none font-mono text-sm uppercase tracking-wider border-foreground/30 hover:border-foreground h-12 px-8"
              >
                UPLOAD YOUR PAPERS
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Core Pillars Section */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-border/80" ref={ref}>
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <span className="font-mono text-xs uppercase tracking-widest text-[#FF6B2C] font-semibold">
                Autonomous Intelligence Layer
              </span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-mono font-bold text-foreground mt-2 tracking-tight">
                Unlock the Power of AI
              </h2>
              <p className="text-muted-foreground font-mono text-sm sm:text-base max-w-xl mx-auto mt-3">
                High-precision reasoning engines built for rigorous literature review and defensible system design.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={isInView ? { opacity: 1 } : {}}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="grid md:grid-cols-3 gap-6"
            >
              {features.map((feature, index) => (
                <motion.div
                  key={feature.label}
                  initial={{ opacity: 0, y: 40 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{
                    delay: 0.3 + index * 0.15,
                    duration: 0.6,
                    type: "spring",
                    stiffness: 100,
                    damping: 10,
                  }}
                  className="flex flex-col items-center text-center p-8 bg-card border border-border/80 hover:border-[#FF6B2C] hover:shadow-lg transition-all group relative overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-full h-[3px] bg-transparent group-hover:bg-[#FF6B2C] transition-colors" />
                  <div className="mb-6 rounded-full bg-[#FF6B2C]/10 p-4 group-hover:scale-110 transition-transform">
                    <feature.icon className="h-8 w-8 text-[#FF6B2C]" />
                  </div>
                  <h3 className="mb-3 text-xl font-mono font-bold text-foreground">
                    {feature.label}
                  </h3>
                  <p className="text-muted-foreground font-mono text-sm leading-relaxed mb-6 grow">
                    {feature.description}
                  </p>
                  <Link
                    to={feature.actionUrl}
                    className="inline-flex items-center text-xs font-mono uppercase font-bold text-[#FF6B2C] group-hover:translate-x-1 transition-transform"
                  >
                    {feature.actionLabel} <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Live Grounding & Citations Showcase */}
        <section className="bg-foreground/5 py-20 border-y border-border/80">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
            <div className="flex flex-col lg:flex-row items-center gap-12">
              <div className="lg:w-1/2 space-y-6">
                <div className="inline-flex items-center gap-2 px-3 py-1 border border-[#FF6B2C]/30 bg-[#FF6B2C]/10 font-mono text-xs uppercase text-[#FF6B2C]">
                  <ShieldCheck className="w-4 h-4" /> Zero-Hallucination Grounding
                </div>
                <h3 className="font-mono text-3xl sm:text-4xl font-bold tracking-tight text-foreground leading-tight">
                  Every claim is backed by exact page & section citations.
                </h3>
                <p className="font-mono text-sm sm:text-base text-muted-foreground leading-relaxed">
                  Unlike generic language models that hallucinate research findings, Research2Build extracts
                  verifiable quotes from indexed PDF chunks and validates every statement before presenting it.
                </p>
                <div className="pt-2 flex flex-col sm:flex-row gap-3">
                  <Button
                    onClick={() => navigate("/qa")}
                    className="rounded-none bg-[#FF6B2C] hover:bg-[#FF6B2C]/90 font-mono text-xs uppercase tracking-wider font-bold"
                  >
                    TEST Q&A RETRIEVAL <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                  </Button>
                  <Button
                    onClick={() => navigate("/compare")}
                    variant="outline"
                    className="rounded-none font-mono text-xs uppercase tracking-wider"
                  >
                    COMPARE PAPERS
                  </Button>
                </div>
              </div>

              <div className="lg:w-1/2 w-full">
                <div className="bg-card border border-border p-6 shadow-md font-mono">
                  <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
                    <span className="text-xs uppercase font-bold text-muted-foreground flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      Live Evidence Inspector
                    </span>
                    <span className="text-[11px] px-2 py-0.5 bg-[#FF6B2C]/10 text-[#FF6B2C] font-semibold">
                      Chunk {activeEvidenceIndex + 1} of {sampleCitations.length}
                    </span>
                  </div>

                  <div className="min-h-[140px] flex items-center">
                    <p className="text-sm italic text-foreground leading-relaxed border-l-2 border-[#FF6B2C] pl-4 py-1">
                      "{sampleCitations[activeEvidenceIndex].quote}"
                    </p>
                  </div>

                  <div className="mt-4 pt-4 border-t border-border/80 flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div>
                      <div className="font-bold text-foreground">
                        {sampleCitations[activeEvidenceIndex].paper}
                      </div>
                      <div className="text-muted-foreground text-[11px] mt-0.5">
                        Section: {sampleCitations[activeEvidenceIndex].section} • Page {sampleCitations[activeEvidenceIndex].page}
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {sampleCitations.map((_, i) => (
                        <button
                          key={i}
                          onClick={() => setActiveEvidenceIndex(i)}
                          className={`w-2.5 h-2.5 rounded-none transition-all ${
                            activeEvidenceIndex === i
                              ? "bg-[#FF6B2C] w-6"
                              : "bg-muted-foreground/30 hover:bg-muted-foreground/60"
                          }`}
                          aria-label={`Show quote ${i + 1}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Interactive Capability Directory */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
              <div>
                <span className="font-mono text-xs uppercase tracking-widest text-[#FF6B2C] font-semibold">
                  Modular Workflow
                </span>
                <h2 className="text-3xl sm:text-4xl font-mono font-bold text-foreground mt-1">
                  Complete End-to-End Pipeline
                </h2>
              </div>
              <p className="font-mono text-xs text-muted-foreground max-w-sm">
                From broad keyword discovery to verified PRD deliverables in one unified workflow.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {platformModules.map((item) => (
                <Link
                  key={item.title}
                  to={item.href}
                  className="p-5 bg-card border border-border/80 hover:border-[#FF6B2C] hover:shadow-md transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="p-2 bg-foreground/5 text-foreground group-hover:bg-[#FF6B2C] group-hover:text-white transition-colors">
                        <item.icon className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 bg-foreground/5 text-muted-foreground group-hover:text-foreground">
                        {item.tag}
                      </span>
                    </div>
                    <h4 className="font-mono font-bold text-sm text-foreground mb-1.5 group-hover:text-[#FF6B2C] transition-colors">
                      {item.title}
                    </h4>
                    <p className="font-mono text-xs text-muted-foreground leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs font-mono font-bold text-muted-foreground group-hover:text-[#FF6B2C]">
                    <span>LAUNCH</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Bottom CTA Banner */}
        <section className="bg-foreground text-background py-16">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl text-center">
            <h2 className="font-mono text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight mb-4">
              Ready to turn research papers into reality?
            </h2>
            <p className="font-mono text-sm sm:text-base text-background/80 max-w-xl mx-auto mb-8">
              Start by discovering new publications or uploading your local PDF library.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button
                onClick={() => navigate("/discover")}
                size="lg"
                className="rounded-none bg-[#FF6B2C] text-white hover:bg-[#FF6B2C]/90 font-mono text-sm uppercase tracking-wider font-bold h-12 px-8"
              >
                DISCOVER PAPERS <Search className="w-4 h-4 ml-2" />
              </Button>
              <Button
                onClick={() => navigate("/upload")}
                variant="outline"
                size="lg"
                className="rounded-none border-background/30 text-background hover:bg-background/10 font-mono text-sm uppercase tracking-wider h-12 px-8"
              >
                UPLOAD LOCAL PDFS <Upload className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-12 bg-background font-mono text-xs">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Bird className="h-5 w-5 text-[#FF6B2C]" />
              <span className="font-bold text-sm">Research2Build</span>
              <span className="text-muted-foreground">• Myna AI Interface</span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-6 text-muted-foreground">
              <Link to="/discover" className="hover:text-foreground">Discovery</Link>
              <Link to="/analysis" className="hover:text-foreground">Analysis</Link>
              <Link to="/qa" className="hover:text-foreground">Grounded Q&A</Link>
              <Link to="/opportunities" className="hover:text-foreground">Opportunities</Link>
              <Link to="/feasibility" className="hover:text-foreground">Feasibility</Link>
              <Link to="/chat" className="hover:text-foreground">Copilot</Link>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>All Systems Operational</span>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-border/60 text-center text-muted-foreground text-[11px]">
            &copy; {new Date().getFullYear()} Research2Build. AI-powered evidence synthesis & project planning.
          </div>
        </div>
      </footer>
    </div>
  );
}

export default MynaHero;
