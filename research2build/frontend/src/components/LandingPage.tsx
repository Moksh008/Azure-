import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const TABS = ["Ingestion", "Analysis", "Q&A", "Opportunities", "Feasibility"];

function IconDocument({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v5h5" />
      <path d="M9 13h6M9 17h6M9 9h2" />
    </svg>
  );
}

function IconLink({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M9 15 15 9" />
      <path d="M11 6.5 12.5 5a4 4 0 1 1 5.5 5.5L16.5 12" />
      <path d="M13 17.5 11.5 19A4 4 0 1 1 6 13.5L7.5 12" />
    </svg>
  );
}

function IconCompass({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" />
      <path d="m14.5 9.5-1.8 4.7-4.7 1.8 1.8-4.7Z" />
    </svg>
  );
}

const FEATURES = [
  {
    Icon: IconDocument,
    iconBg: "bg-yellow text-ink",
    title: "Ingest any paper",
    body: "Upload PDFs and get clean, normalized text — chunked by section and page, ready for retrieval.",
    highlight: false,
  },
  {
    Icon: IconLink,
    iconBg: "bg-ink text-white",
    title: "Every claim, cited",
    body: "Q&A answers and analysis fields carry citations back to the exact paper, section, and page that support them.",
    highlight: true,
  },
  {
    Icon: IconCompass,
    iconBg: "bg-mint text-ink",
    title: "From evidence to roadmap",
    body: "Recurring limitations become potential opportunities, then feasibility-scored project proposals.",
    highlight: false,
  },
];

const CITATIONS = [
  {
    quote: "Latency remains the primary bottleneck in distributed training.",
    paper: "Federated Learning at Scale",
    section: "Limitations",
    page: 7,
  },
  {
    quote: "We reduce communication overhead via gradient sparsification.",
    paper: "Federated Learning at Scale",
    section: "Method",
    page: 4,
  },
  {
    quote: "Accuracy drops by 2% under non-IID data splits.",
    paper: "Edge Inference Survey",
    section: "Results",
    page: 6,
  },
  {
    quote: "Cross-silo settings are left for future exploration.",
    paper: "Privacy-Preserving ML",
    section: "Future Work",
    page: 11,
  },
  {
    quote: "Evaluation only covers a single datacenter.",
    paper: "Federated Learning at Scale",
    section: "Limitations",
    page: 9,
  },
  {
    quote: "Our approach cuts inference latency by 38% on edge devices.",
    paper: "Edge Inference Survey",
    section: "Results",
    page: 5,
  },
];

function Button({
  children,
  light = false,
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { light?: boolean }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[10px] px-6 py-3.5 font-semibold text-[15px] cursor-pointer transition-transform duration-150 hover:-translate-y-0.5 hover:opacity-90 ${
        light ? "bg-white text-ink border border-border" : "bg-ink text-white border-none"
      } ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

function Banner({ onClose }: { onClose: () => void }) {
  return (
    <div className="relative bg-yellow text-center font-semibold text-sm py-3 px-5 md:px-10">
      📚 Built for AI-103 — evidence-grounded research analysis.{" "}
      <a href="#pipeline" className="underline">
        See how it works →
      </a>
      <button
        onClick={onClose}
        className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-lg bg-none border-none w-11 h-11 flex items-center justify-center"
        aria-label="Dismiss banner"
      >
        ✕
      </button>
    </div>
  );
}

function Nav() {
  return (
    <header className="flex items-center justify-between max-w-[1280px] mx-auto px-5 md:px-10 py-7">
      <div className="flex items-center gap-2.5 font-display font-bold text-[22px]">
        <span className="w-[34px] h-[34px] rounded-full bg-ink flex items-center justify-center text-white text-sm">
          R²
        </span>
        Research2Build
      </div>
      <Link to="/upload">
        <Button light>Upload a paper</Button>
      </Link>
    </header>
  );
}

function Hero() {
  const [citations, setCitations] = useState(0);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;
    const interval = setInterval(() => setCitations((c) => c + 1), 600);
    return () => clearInterval(interval);
  }, [running]);

  return (
    <section className="relative text-center max-w-[1100px] mx-auto px-5 md:px-10 pt-16 pb-10">
      <div
        className="absolute opacity-90 -left-[60px] top-[120px] w-10 h-10 bg-mint-deep"
        style={{ borderRadius: "60% 40% 55% 45%" }}
      />
      <div
        className="absolute opacity-90 -right-[30px] top-[60px] w-[50px] h-[50px] bg-blue"
        style={{ borderRadius: "50% 60% 40% 55%" }}
      />

      <h1 className="font-display font-bold leading-[1.05] text-[clamp(36px,6vw,68px)]">
        Turn research papers{" "}
        <span className="inline-block align-middle w-[0.9em] h-[0.9em] bg-yellow rounded-full mx-1.5" /> into
        grounded projects
      </h1>

      <div className="flex items-center justify-center gap-4 mx-auto mt-8 mb-5 max-w-[560px] bg-white rounded-2xl p-2.5 shadow-[0_10px_30px_rgba(21,27,49,0.06)]">
        <Link to="/upload" className="flex-1">
          <Button className="w-full py-4">Upload a paper</Button>
        </Link>
        <div className="flex items-center gap-2.5 px-3.5 font-semibold text-muted">
          {citations} citations
          <button
            onClick={() => setRunning((r) => !r)}
            className="w-11 h-11 rounded-full bg-mint-deep text-white flex items-center justify-center border-none cursor-pointer"
            aria-label={running ? "Pause live demo" : "Start live demo"}
          >
            {running ? "⏸" : "▶"}
          </button>
        </div>
      </div>

      <div className="font-display font-bold text-[clamp(28px,4.5vw,44px)] mt-2">
        you'll actually <span className="text-coral">trust</span>
      </div>
      <p className="text-muted max-w-[520px] mx-auto mt-4.5 text-base">
        Upload PDFs, get structured analysis, ask grounded questions, and generate
        feasibility-checked project proposals — every claim traceable to a paper, section, and
        page.
      </p>
    </section>
  );
}

function Showcase() {
  const [activeTab, setActiveTab] = useState(0);

  const rows: [string, string][] = [
    ["Evaluation only covers a single datacenter.", "Limitations · p.9"],
    ["We reduce communication overhead via gradient sparsification.", "Method · p.4"],
    ["Accuracy drops by 2% under non-IID data splits.", "Results · p.6"],
    ["Future work should explore cross-silo settings.", "Future Work · p.11"],
  ];

  return (
    <section id="pipeline" className="bg-panel-dark rounded-[28px] max-w-[1200px] mx-auto my-[70px] p-5 md:p-10">
      <div className="flex gap-9 justify-center border-b border-panel-line pb-4.5 mb-7.5 flex-wrap">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`relative bg-none border-none text-base font-semibold cursor-pointer py-1.5 px-0.5 ${
              activeTab === i
                ? "text-white after:content-[''] after:absolute after:left-0 after:right-0 after:-bottom-[19px] after:h-[3px] after:bg-coral after:rounded-[3px]"
                : "text-tab-inactive"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-2xl overflow-hidden shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
        <div className="flex justify-between items-center py-4 px-5.5 border-b border-border text-sm text-muted">
          <span>{TABS[activeTab]}</span>
          <span>Share live ↗</span>
        </div>
        <div className="flex min-h-[340px]">
          <div className="w-[220px] border-r border-border p-4.5 text-sm text-muted max-md:hidden">
            <div className="py-2 px-2.5 rounded-lg mb-1 bg-pill-bg text-ink font-semibold">
              Federated Learning at Scale
            </div>
            <div className="py-2 px-2.5 rounded-lg mb-1">Overview</div>
            <div className="py-2 px-2.5 rounded-lg mb-1">Citations</div>
            <div className="py-2 px-2.5 rounded-lg mb-1">Export</div>
          </div>
          <div className="flex-1 p-5.5 px-6.5">
            <h3 className="font-display font-bold text-lg mb-3.5">Evidence chunks</h3>
            {rows.map(([label, pill]) => (
              <div key={label} className="flex justify-between items-center py-3 border-b border-row-border text-sm gap-4">
                <span>{label}</span>
                <span className="bg-pill-bg rounded-full py-1 px-2.5 text-xs font-semibold text-muted whitespace-nowrap">
                  {pill}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function SectionTitle({ title, sub, small = false }: { title: string; sub: string; small?: boolean }) {
  return (
    <div className="text-center max-w-[640px] mx-auto my-[50px] px-5 md:px-10">
      <h2 className={`font-display font-bold ${small ? "text-[22px]" : "text-[clamp(28px,4vw,42px)]"}`}>{title}</h2>
      <p className="text-muted mt-3 text-base">{sub}</p>
    </div>
  );
}

function FeatureGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-[1200px] mx-auto px-5 md:px-10">
      {FEATURES.map((f) => (
        <div
          key={f.title}
          className={`rounded-2xl p-7.5 border border-border ${f.highlight ? "bg-[#EFEFEF]" : "bg-card"}`}
        >
          <div className={`w-13 h-13 rounded-[14px] flex items-center justify-center mb-5.5 ${f.iconBg}`}>
            <f.Icon className="w-6 h-6" />
          </div>
          <h4 className="font-display font-bold text-[19px] mb-2">{f.title}</h4>
          <p className="text-muted text-sm leading-relaxed">{f.body}</p>
        </div>
      ))}
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 py-2.5 px-3 border border-border rounded-[10px] text-sm">
      <span className="text-coral font-semibold text-xs uppercase tracking-[0.04em] w-[92px] flex-shrink-0">
        {label}
      </span>
      <span className="text-ink truncate">{value}</span>
    </div>
  );
}

function CitationChip({ paper, section, page }: { paper: string; section: string; page: number }) {
  return (
    <span className="inline-block bg-pill-bg rounded-full py-1 px-2.5 text-xs font-semibold text-muted mr-2 mb-2">
      {paper} · {section} · p.{page}
    </span>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return <div className="text-coral uppercase text-sm font-bold tracking-[0.06em] mb-3.5">{children}</div>;
}

function Split({
  reverse = false,
  art,
  eyebrow,
  badge,
  title,
  body,
  cta,
}: {
  reverse?: boolean;
  art: React.ReactNode;
  eyebrow?: string;
  badge?: string;
  title: string;
  body: string;
  cta: string;
}) {
  const artEl = (
    <div className="bg-white rounded-[20px] border border-border p-6.5 min-h-[320px] flex flex-col justify-center gap-3 shadow-[0_16px_40px_rgba(21,27,49,0.06)]">
      {art}
    </div>
  );
  const textEl = (
    <div>
      {badge && (
        <span className="inline-block bg-yellow text-ink text-xs font-bold py-1.5 px-3 rounded-full mb-3.5">
          {badge}
        </span>
      )}
      {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
      <h2 className="font-display font-bold text-[clamp(24px,3.2vw,34px)] mb-3.5">{title}</h2>
      <p className="text-muted text-base leading-relaxed mb-6">{body}</p>
      <Button>{cta}</Button>
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-12.5 max-w-[1200px] mx-auto my-[110px] px-5 md:px-10 items-center">
      {reverse ? (
        <>
          {artEl}
          {textEl}
        </>
      ) : (
        <>
          {textEl}
          {artEl}
        </>
      )}
    </div>
  );
}

function Testimonials() {
  return (
    <div className="max-w-[1200px] mx-auto my-[110px] px-5 md:px-10 text-center">
      <h2 className="font-display font-bold text-[clamp(28px,4vw,42px)]">Every claim, traced to its source</h2>
      <p className="text-muted mt-3 text-base">
        A sample of the evidence chunks our pipeline pulls straight from uploaded papers.
      </p>
      <div className="flex gap-5 overflow-hidden mt-10">
        {CITATIONS.map((c) => (
          <div
            key={c.quote}
            className="bg-white border border-border rounded-2xl p-6 min-w-[280px] text-left flex-shrink-0"
          >
            <p className="text-ink text-sm leading-relaxed mb-4">"{c.quote}"</p>
            <div className="flex items-center gap-2.5 text-[13px] text-muted">
              <div className="w-8 h-8 rounded-full bg-periwinkle flex items-center justify-center text-ink text-xs font-bold">
                p.{c.page}
              </div>
              <span>
                {c.paper} · {c.section}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Marquee() {
  const words = ["Evidence-grounded", "No claim without a citation", "Paper → Section → Page"];
  const chunk = words.join(" • ") + " • ";
  const repeated = chunk.repeat(6);
  return (
    <div className="bg-ink text-white py-5.5 overflow-hidden whitespace-nowrap mt-[110px]">
      <div className="inline-block animate-marquee font-display font-bold text-[22px]">
        {(repeated + repeated).split("• ").map((part, i, arr) =>
          i === arr.length - 1 ? (
            part
          ) : (
            <span key={i}>
              {part}
              <span className="text-coral">•</span>
            </span>
          ),
        )}
      </div>
    </div>
  );
}

function Footer() {
  return (
    <footer className="max-w-[1200px] mx-auto px-5 md:px-10 pt-[70px] pb-10 text-center">
      <h2 className="font-display font-bold text-[clamp(28px,4vw,44px)] mb-6.5">
        Ready to turn papers into projects? 📚
      </h2>
      <Button>Upload your first paper</Button>
      <div className="flex justify-between items-center mt-[70px] pt-6 border-t border-border text-muted text-[13px] flex-wrap gap-2.5">
        <span>© 2026 Research2Build. An AI-103 project.</span>
        <span>
          <a href="#" className="underline">
            GitHub
          </a>{" "}
          &nbsp;·&nbsp;{" "}
          <a href="#" className="underline">
            Architecture docs
          </a>
        </span>
      </div>
    </footer>
  );
}

export default function LandingPage() {
  const [bannerVisible, setBannerVisible] = useState(true);

  return (
    <div className="min-h-screen bg-bg text-ink font-sans overflow-x-hidden">
      {bannerVisible && <Banner onClose={() => setBannerVisible(false)} />}
      <Nav />
      <Hero />
      <Showcase />

      <SectionTitle
        title="Grounded research, without the busywork"
        sub="Let's have a sneak peek here to get the idea."
      />
      <SectionTitle
        title="So what can you do with Research2Build?"
        sub="Upload a stack of papers — see what you can build from them."
        small
      />

      <FeatureGrid />

      <Split
        eyebrow="One extraction, reused everywhere"
        title="Know each paper cold"
        body="Every paper is broken into problem, method, results, limitations, and future work — extracted once and reused across Q&A, opportunities, and feasibility checks."
        cta="See an analysis"
        art={
          <>
            <strong className="font-display">Federated Learning at Scale</strong>
            <FieldRow label="Problem" value="Communication cost dominates training time." />
            <FieldRow label="Method" value="Gradient sparsification + async updates." />
            <FieldRow label="Results" value="38% latency reduction on edge devices." />
            <FieldRow label="Limitations" value="Single-datacenter evaluation only." />
          </>
        }
      />

      <Split
        reverse
        eyebrow="Ask, and verify"
        title="Evidence-based Q&A"
        body="Ask a question across your paper set and get an answer with citations attached — paper, section, and page for every supporting claim."
        cta="Ask a question"
        art={
          <>
            <strong className="font-display">Q: What limitations recur across papers?</strong>
            <p className="text-sm text-muted leading-relaxed">
              A: Latency and single-datacenter evaluation are repeatedly cited as limitations.
            </p>
            <div>
              <CitationChip paper="Federated Learning at Scale" section="Limitations" page={7} />
              <CitationChip paper="Federated Learning at Scale" section="Limitations" page={9} />
              <CitationChip paper="Edge Inference Survey" section="Limitations" page={4} />
            </div>
          </>
        }
      />

      <Split
        badge="Inferred, not asserted"
        title="Potential research opportunities"
        body="Recurring limitations across papers surface as potential opportunities — inferred from the evidence, never stated as fact."
        cta="View opportunities"
        art={
          <>
            <strong className="font-display">Potential opportunity</strong>
            <div className="flex justify-between items-center py-3 border-b border-row-border text-sm">
              <span>Latency mentioned as a limitation in 4 of 6 papers</span>
              <span className="bg-pill-bg rounded-full py-1 px-2.5 text-xs font-semibold text-muted">
                Recurring
              </span>
            </div>
            <p className="text-xs text-muted italic mt-1">
              Novelty confidence: requires human validation.
            </p>
          </>
        }
      />

      <Split
        reverse
        eyebrow="Plan it out"
        title="Feasibility & roadmap"
        body="Tell us your team size, timeline, budget, and skills — get a feasibility score and a basic roadmap for turning an opportunity into a project."
        cta="Check feasibility"
        art={
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr>
                <th className="text-left text-muted font-semibold p-2 border-b border-border">Constraint</th>
                <th className="text-left text-muted font-semibold p-2 border-b border-border">Value</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Team size", "3 members"],
                ["Timeline", "6 weeks"],
                ["Budget", "$100 credit"],
                ["Feasibility score", "72%"],
              ].map(([constraint, value]) => (
                <tr key={constraint}>
                  <td className="p-2.5 border-b border-hairline">{constraint}</td>
                  <td className="p-2.5 border-b border-hairline">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />

      <Testimonials />
      <Marquee />
      <Footer />
    </div>
  );
}
