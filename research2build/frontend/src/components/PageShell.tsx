import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";

const NAV_LINKS: { to: string; label: string }[] = [
  { to: "/upload", label: "Upload" },
  { to: "/discover", label: "Discover" },
  { to: "/analysis", label: "Analysis" },
  { to: "/qa", label: "Q&A" },
  { to: "/compare", label: "Compare" },
  { to: "/opportunities", label: "Opportunities" },
  { to: "/projects", label: "Projects" },
  { to: "/feasibility", label: "Feasibility" },
  { to: "/deliverables", label: "Deliverables" },
];

export default function PageShell({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-border bg-white">
        <div className="max-w-[1280px] mx-auto px-5 md:px-10 py-5 flex items-center justify-between gap-6">
          <Link to="/" className="flex items-center gap-2.5 font-display font-bold text-lg shrink-0">
            <span className="w-8 h-8 rounded-full bg-ink flex items-center justify-center text-white text-xs">
              R²
            </span>
            Research2Build
          </Link>
          <nav className="flex flex-wrap gap-1 justify-end">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `text-sm font-semibold px-3 py-2 rounded-[8px] ${
                    isActive ? "bg-ink text-white" : "text-muted hover:bg-pill-bg"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-[1100px] mx-auto px-5 md:px-10 py-10">
        <div className="mb-8">
          <h1 className="font-display font-bold text-3xl text-ink">{title}</h1>
          {description && <p className="text-muted mt-2 max-w-2xl">{description}</p>}
        </div>
        {children}
      </main>
    </div>
  );
}
