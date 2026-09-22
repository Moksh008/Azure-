import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Bird,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  FileCheck,
  FileText,
  Home,
  Layers,
  LogIn,
  LogOut,
  Menu,
  MessageSquare,
  Plus,
  Sparkles,
  Target,
  Trash2,
  Upload,
  User as UserIcon,
  X,
  Zap,
} from "lucide-react";
import { useAppData } from "../lib/AppDataContext";
import { useAuth } from "../lib/AuthContext";
import {
  loadUserChatSessions,
  deleteChatSession,
  type ChatSessionMeta,
} from "../lib/chatService";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [
      // { to: "/", label: "Home Landing", icon: Home },
      { to: "/chat", label: "AI Copilot & Chat", icon: MessageSquare, badge: "New" },
    ],
  },
  {
    title: "Research Intelligence",
    items: [
      { to: "/analysis", label: "Paper Analysis", icon: BookOpen },
      { to: "/qa", label: "Grounded Q&A", icon: FileCheck },
      { to: "/compare", label: "Comparative Matrix", icon: Layers },
      { to: "/opportunities", label: "Opportunity Finder", icon: Target },
    ],
  },
  {
    title: "Engineering & Delivery",
    items: [
      { to: "/projects", label: "Project Generator", icon: Zap },
      { to: "/feasibility", label: "Feasibility Scorer", icon: Compass },
      { to: "/deliverables", label: "PRD & Roadmap", icon: FileText },
    ],
  },
];

export default function PageShell({
  title,
  description,
  children,
  actionButton,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  actionButton?: ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatSessionMeta[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const { library, selectedPaperIds } = useAppData();
  const { currentUser, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Load chat history for the sidebar
  async function fetchSidebarHistory() {
    if (!currentUser) {
      setChatHistory([]);
      return;
    }
    setLoadingHistory(true);
    try {
      const sessions = await loadUserChatSessions(currentUser.uid);
      setChatHistory(sessions);
    } catch (err) {
      console.warn("Failed to load sidebar chat history", err);
    } finally {
      setLoadingHistory(false);
    }
  }

  useEffect(() => {
    fetchSidebarHistory();
  }, [currentUser, location.pathname]);

  async function handleLogout() {
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      console.error("Logout error", err);
    }
  }

  async function handleDeleteSidebarSession(e: React.MouseEvent, sessionId: string) {
    e.preventDefault();
    e.stopPropagation();
    if (!currentUser) return;
    try {
      await deleteChatSession(currentUser.uid, sessionId);
      setChatHistory((prev) => prev.filter((s) => s.id !== sessionId));
      if (location.search.includes(sessionId)) {
        navigate("/chat");
      }
    } catch (err) {
      console.error("Failed to delete chat session", err);
    }
  }

  return (
    <div className="min-h-screen bg-bg text-ink flex flex-col lg:flex-row antialiased">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between border-b border-border bg-white/95 backdrop-blur-md px-4 py-3">
        <Link to="/" className="flex items-center gap-2">
          <div className="p-1 bg-[#FF6B2C]/10 text-[#FF6B2C]">
            <Bird className="h-5 w-5" />
          </div>
          <span className="font-mono text-base font-bold tracking-tight">
            Research<span className="text-[#FF6B2C]">2</span>Build
          </span>
        </Link>
        <div className="flex items-center gap-2">
          {currentUser ? (
            <button
              onClick={handleLogout}
              className="p-2 text-muted hover:text-red-500"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          ) : (
            <Link
              to="/login"
              className="p-2 text-muted hover:text-[#FF6B2C]"
              title="Sign In"
            >
              <LogIn className="w-4 h-4" />
            </Link>
          )}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 text-ink hover:bg-pill-bg transition-colors"
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar (Desktop + Mobile Drawer) */}
      <aside
        className={`fixed lg:sticky top-0 z-40 h-screen flex flex-col border-r border-panel-line bg-panel-dark text-white transition-all duration-300 ${
          collapsed ? "lg:w-20" : "lg:w-64 w-72"
        } ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-panel-line">
          <Link
            to="/"
            className={`flex items-center gap-3 overflow-hidden ${
              collapsed ? "justify-center w-full" : ""
            }`}
          >
            <div className="p-1.5 bg-[#FF6B2C] text-white shrink-0 shadow-xs">
              <Bird className="h-5 w-5" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-mono text-sm font-bold tracking-tight whitespace-nowrap">
                  Research<span className="text-[#FF6B2C]">2</span>Build
                </span>
                <span className="text-[9px] font-mono tracking-widest text-muted uppercase -mt-0.5">
                  Firestore History
                </span>
              </div>
            )}
          </Link>

          {/* Desktop Collapse Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex h-7 w-7 items-center justify-center text-muted hover:text-white hover:bg-panel-dark-2 transition-colors cursor-pointer"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1 text-muted hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-panel-line scrollbar-track-transparent">
          {NAV_SECTIONS.map((section, sIdx) => (
            <div key={sIdx}>
              {!collapsed && (
                <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-wider text-muted font-semibold">
                  {section.title}
                </div>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive =
                    item.to === "/"
                      ? location.pathname === "/"
                      : location.pathname.startsWith(item.to);

                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      onClick={() => setMobileOpen(false)}
                      title={collapsed ? item.label : undefined}
                      className={`flex items-center gap-3 px-3 py-2 text-xs font-mono transition-all rounded-none ${
                        isActive
                          ? "bg-[#FF6B2C] text-white font-semibold shadow-xs"
                          : "text-muted-foreground hover:bg-panel-dark-2 hover:text-white"
                      } ${collapsed ? "justify-center px-0" : ""}`}
                    >
                      <Icon
                        className={`h-4 w-4 shrink-0 ${
                          isActive ? "text-white" : "text-[#FF6B2C]"
                        }`}
                      />
                      {!collapsed && (
                        <div className="flex items-center justify-between w-full">
                          <span className="truncate">{item.label}</span>
                          {item.badge && (
                            <span className="text-[9px] uppercase px-1.5 py-0.2 bg-[#FF6B2C]/20 text-[#FF6B2C] border border-[#FF6B2C]/40 font-mono">
                              {item.badge}
                            </span>
                          )}
                        </div>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}

          {/* CHAT HISTORY SECTION IN SIDEBAR */}
          {currentUser && (
            <div className="pt-2 border-t border-panel-line">
              {!collapsed ? (
                <div className="flex items-center justify-between px-3 mb-2">
                  <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-muted font-semibold">
                    <Clock className="w-3 h-3 text-[#FF6B2C]" />
                    <span>Recent Chats</span>
                  </div>
                  <Link
                    to="/chat"
                    onClick={() => setMobileOpen(false)}
                    className="text-[10px] uppercase font-mono text-[#FF6B2C] hover:text-white flex items-center gap-1"
                    title="Start new research chat"
                  >
                    <Plus className="w-3 h-3" /> New
                  </Link>
                </div>
              ) : (
                <div className="flex justify-center mb-2">
                  <Link
                    to="/chat"
                    title="Recent Chats"
                    className="p-1.5 text-muted hover:text-[#FF6B2C]"
                  >
                    <Clock className="w-4 h-4" />
                  </Link>
                </div>
              )}

              {!collapsed && (
                <div className="space-y-1">
                  {loadingHistory ? (
                    <div className="px-3 py-2 text-[11px] font-mono text-muted animate-pulse">
                      Loading history...
                    </div>
                  ) : chatHistory.length === 0 ? (
                    <div className="px-3 py-2 text-[11px] font-mono text-muted">
                      No saved chats yet.
                    </div>
                  ) : (
                    chatHistory.slice(0, 8).map((session) => {
                      const isSelected = location.search.includes(session.id);
                      return (
                        <Link
                          key={session.id}
                          to={`/chat?session=${session.id}`}
                          onClick={() => setMobileOpen(false)}
                          className={`flex items-center justify-between gap-2 px-3 py-1.5 text-xs font-mono transition-all group ${
                            isSelected
                              ? "bg-panel-dark-2 text-[#FF6B2C] font-semibold border-l-2 border-[#FF6B2C]"
                              : "text-muted hover:bg-panel-dark-2 hover:text-white"
                          }`}
                        >
                          <div className="flex items-center gap-2 overflow-hidden">
                            <MessageSquare className="w-3 h-3 shrink-0 opacity-60 group-hover:opacity-100" />
                            <span className="truncate text-[11px]">{session.title}</span>
                          </div>
                          <button
                            onClick={(e) => handleDeleteSidebarSession(e, session.id)}
                            className="opacity-0 group-hover:opacity-100 text-muted hover:text-red-400 p-0.5 transition-opacity"
                            title="Delete chat"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </Link>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar Library & System Widget */}
        <div className="p-3 border-t border-panel-line bg-panel-dark-2/60 space-y-3">
          {!collapsed ? (
            <>
              <div className="p-2.5 bg-panel-dark border border-panel-line text-xs font-mono space-y-1.5">
                <div className="flex items-center justify-between text-muted">
                  <span className="text-[10px] uppercase tracking-wider">Library Index</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-mint-deep animate-pulse" />
                </div>
                <div className="flex items-center justify-between font-bold text-white">
                  <span>{library.length} Papers Loaded</span>
                  <span className="text-[#FF6B2C] text-[11px]">
                    {selectedPaperIds.size} Selected
                  </span>
                </div>
                <Link
                  to="/upload"
                  className="block text-center text-[10px] uppercase text-[#FF6B2C] hover:underline pt-1"
                >
                  + Add more PDFs
                </Link>
              </div>

              {/* User Auth Info in Sidebar */}
              <div className="pt-2 border-t border-panel-line flex items-center justify-between font-mono text-xs">
                {currentUser ? (
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <div className="w-6 h-6 rounded-full bg-[#FF6B2C] text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                        {currentUser.email ? currentUser.email[0].toUpperCase() : "U"}
                      </div>
                      <span className="truncate text-white text-[11px]">
                        {currentUser.displayName || currentUser.email}
                      </span>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="p-1 text-muted hover:text-red-400 cursor-pointer"
                      title="Sign Out"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <Link
                    to="/login"
                    className="flex items-center justify-center gap-1.5 w-full py-1.5 px-2 bg-panel-dark border border-panel-line text-white hover:border-[#FF6B2C] text-xs transition-colors"
                  >
                    <LogIn className="w-3.5 h-3.5 text-[#FF6B2C]" />
                    <span>Sign In</span>
                  </Link>
                )}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center gap-2 py-1">
              <Link
                to="/upload"
                title={`${library.length} papers in library`}
                className="w-8 h-8 flex items-center justify-center bg-panel-dark border border-panel-line text-[#FF6B2C] hover:bg-panel-dark-2 text-xs font-mono font-bold"
              >
                {library.length}
              </Link>
              {currentUser ? (
                <button
                  onClick={handleLogout}
                  title={`Sign out (${currentUser.email})`}
                  className="w-8 h-8 flex items-center justify-center text-muted hover:text-red-400 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              ) : (
                <Link
                  to="/login"
                  title="Sign In"
                  className="w-8 h-8 flex items-center justify-center text-[#FF6B2C] hover:bg-panel-dark-2"
                >
                  <LogIn className="w-4 h-4" />
                </Link>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="hidden lg:flex sticky top-0 z-20 h-16 items-center justify-between border-b border-border bg-white/90 backdrop-blur-md px-6 xl:px-10">
          <div className="flex items-center gap-3">
            <h2 className="font-mono text-sm font-semibold uppercase tracking-wider text-muted">
              Workspace / <span className="text-ink font-bold">{title}</span>
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/chat"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#1F2023] text-white hover:bg-black font-mono text-xs transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#FF6B2C]" />
              <span>Ask Copilot</span>
            </Link>
            <Link
              to="/upload"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border bg-white hover:bg-pill-bg font-mono text-xs text-ink transition-colors"
            >
              <Upload className="w-3.5 h-3.5 text-[#FF6B2C]" />
              <span>Upload PDF</span>
            </Link>
            {currentUser ? (
              <div className="flex items-center gap-2 pl-2 border-l border-border font-mono text-xs">
                <div className="w-7 h-7 rounded-full bg-[#1F2023] text-white flex items-center justify-center text-xs font-bold">
                  {currentUser.email ? currentUser.email[0].toUpperCase() : "U"}
                </div>
                <button
                  onClick={handleLogout}
                  className="px-2 py-1 text-muted hover:text-red-600 transition-colors cursor-pointer"
                  title="Sign out"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#FF6B2C] text-white hover:bg-[#FF6B2C]/90 font-mono text-xs transition-colors"
              >
                <UserIcon className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
            )}
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 max-w-[1280px] w-full mx-auto px-4 sm:px-6 md:px-8 xl:px-10 py-6 md:py-8">
          <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-border/70">
            <div>
              <h1 className="font-mono font-bold text-2xl sm:text-3xl text-ink tracking-tight">
                {title}
              </h1>
              {description && (
                <p className="text-muted font-mono text-xs sm:text-sm mt-1.5 max-w-3xl leading-relaxed">
                  {description}
                </p>
              )}
            </div>
            {actionButton && <div className="shrink-0">{actionButton}</div>}
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
