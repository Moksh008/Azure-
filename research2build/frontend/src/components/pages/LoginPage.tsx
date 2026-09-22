import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Bird,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  BookOpen,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../../lib/AuthContext";
import { Button } from "../ui/button";

export default function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resetEmailSent, setResetEmailSent] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetLoading, setResetLoading] = useState(false);

  const { currentUser, signInWithGoogle, signInWithEmail, signUpWithEmail, resetPassword } =
    useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || "/chat";

  React.useEffect(() => {
    if (currentUser) {
      navigate(from, { replace: true });
    }
  }, [currentUser, navigate, from]);

  function formatFirebaseError(error: any): string {
    const code = error?.code || "";
    switch (code) {
      case "auth/invalid-email":
        return "Please enter a valid email address.";
      case "auth/user-disabled":
        return "This account has been disabled. Please contact support.";
      case "auth/user-not-found":
      case "auth/wrong-password":
      case "auth/invalid-credential":
        return "Invalid email or password. Please try again.";
      case "auth/email-already-in-use":
        return "An account with this email already exists. Sign in instead.";
      case "auth/weak-password":
        return "Password should be at least 6 characters long.";
      case "auth/popup-closed-by-user":
        return "Google sign-in popup was closed before completion.";
      default:
        return error.message || "Authentication failed. Please check your credentials.";
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError("Please fill in all required fields.");
      return;
    }

    if (isSignUp && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
      } else {
        await signInWithEmail(email, password);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(formatFirebaseError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setError(null);
    setLoading(true);
    try {
      await signInWithGoogle();
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(formatFirebaseError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword(e: React.FormEvent) {
    e.preventDefault();
    if (!resetEmail.trim()) return;
    setResetLoading(true);
    setError(null);
    try {
      await resetPassword(resetEmail);
      setResetEmailSent(true);
    } catch (err: any) {
      setError(formatFirebaseError(err));
    } finally {
      setResetLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg text-ink flex flex-col justify-center selection:bg-[#FF6B2C] selection:text-white font-mono">
      {/* Background Subtle Accent Grids */}
      <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none opacity-60" />

      {/* Top Simple Bar */}
      <div className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-10">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="p-1.5 bg-[#FF6B2C] text-white">
            <Bird className="h-5 w-5" />
          </div>
          <span className="font-mono text-base font-bold tracking-tight text-ink">
            Research<span className="text-[#FF6B2C]">2</span>Build
          </span>
        </Link>
        <Link
          to="/"
          className="text-xs uppercase tracking-wider text-muted hover:text-ink transition-colors"
        >
          &larr; Back to Home
        </Link>
      </div>

      <div className="container mx-auto px-4 py-16 relative z-10">
        <div className="max-w-4xl mx-auto grid md:grid-cols-[1.1fr_1fr] bg-card border border-border shadow-2xl overflow-hidden">
          {/* Left Hero Branding Panel */}
          <div className="hidden md:flex flex-col justify-between p-10 bg-panel-dark text-white border-r border-panel-line">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 bg-[#FF6B2C]/10 border border-[#FF6B2C]/30 text-[#FF6B2C] text-[10px] uppercase tracking-widest font-semibold mb-6">
                <Sparkles className="w-3.5 h-3.5" /> Firebase Auth Secured
              </div>
              <h2 className="text-3xl font-bold tracking-tight leading-tight">
                Turn research papers into production reality.
              </h2>
              <p className="text-muted-foreground text-xs mt-3 leading-relaxed">
                Log in to access your saved workspace, indexed citation chunks,
                cross-paper comparison matrices, and feasibility-scored project roadmaps.
              </p>
            </div>

            <div className="space-y-3 my-8">
              <div className="flex items-start gap-3 p-3 bg-panel-dark-2 border border-panel-line">
                <ShieldCheck className="w-5 h-5 text-[#FF6B2C] shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-white">
                    Evidence-Grounded Citations
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Zero hallucinations. Every claim carries page & section citations.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-panel-dark-2 border border-panel-line">
                <BookOpen className="w-5 h-5 text-mint-deep shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-white">
                    250M+ Academic Literature
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Direct integration with OpenAlex and CORE search indices.
                  </div>
                </div>
              </div>
            </div>

            <div className="text-[10px] text-muted uppercase tracking-widest pt-4 border-t border-panel-line flex items-center justify-between">
              <span>Research2Build Platform</span>
              <span className="text-mint-deep flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-mint-deep animate-pulse" />
                Auth Online
              </span>
            </div>
          </div>

          {/* Right Form Panel */}
          <div className="p-8 sm:p-10 flex flex-col justify-center bg-card">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-ink tracking-tight">
                {isSignUp ? "Create your account" : "Sign in to workspace"}
              </h1>
              <p className="text-xs text-muted mt-1">
                {isSignUp
                  ? "Enter your details to create an account"
                  : "Welcome back! Please enter your credentials"}
              </p>
            </div>

            {/* Google OAuth Button */}
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-border hover:bg-pill-bg transition-colors text-xs font-bold text-ink cursor-pointer disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>

            <div className="relative my-6 text-center">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <span className="relative px-3 bg-card text-[10px] uppercase tracking-wider text-muted font-semibold">
                Or with email
              </span>
            </div>

            {/* Error Notification */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
                  <span className="leading-tight">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs uppercase font-bold text-ink mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-4 h-4 text-muted" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="researcher@university.edu"
                    required
                    className="w-full pl-9 pr-3 py-2.5 border border-border bg-background text-ink text-xs focus:outline-none focus:border-[#FF6B2C] transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs uppercase font-bold text-ink">
                    Password
                  </label>
                  {!isSignUp && (
                    <button
                      type="button"
                      onClick={() => {
                        setResetEmail(email);
                        setShowResetModal(true);
                      }}
                      className="text-[11px] text-[#FF6B2C] hover:underline cursor-pointer"
                    >
                      Forgot?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 w-4 h-4 text-muted" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full pl-9 pr-10 py-2.5 border border-border bg-background text-ink text-xs focus:outline-none focus:border-[#FF6B2C] transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-muted hover:text-ink cursor-pointer"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {isSignUp && (
                <div>
                  <label className="block text-xs uppercase font-bold text-ink mb-1.5">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 w-4 h-4 text-muted" />
                    <input
                      type={showPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full pl-9 pr-3 py-2.5 border border-border bg-background text-ink text-xs focus:outline-none focus:border-[#FF6B2C] transition-colors"
                    />
                  </div>
                </div>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full rounded-none bg-[#FF6B2C] hover:bg-[#FF6B2C]/90 text-white font-bold py-2.5 text-xs uppercase tracking-wider shadow-sm mt-2 cursor-pointer disabled:opacity-50"
              >
                {loading
                  ? "Processing..."
                  : isSignUp
                  ? "Create Account"
                  : "Sign In"}
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </Button>
            </form>

            <div className="mt-6 pt-4 border-t border-border text-center text-xs text-muted">
              {isSignUp ? (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setIsSignUp(false);
                      setError(null);
                    }}
                    className="text-[#FF6B2C] font-bold hover:underline cursor-pointer"
                  >
                    Sign In
                  </button>
                </>
              ) : (
                <>
                  Don't have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setIsSignUp(true);
                      setError(null);
                    }}
                    className="text-[#FF6B2C] font-bold hover:underline cursor-pointer"
                  >
                    Create Account
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Password Reset Modal */}
      <AnimatePresence>
        {showResetModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-card border border-border p-6 max-w-md w-full shadow-2xl font-mono relative"
            >
              <h3 className="text-lg font-bold text-ink mb-2">
                Reset Password
              </h3>
              <p className="text-xs text-muted mb-4">
                Enter your registered email address and we'll send you a link to reset your password.
              </p>

              {resetEmailSent ? (
                <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 mb-4">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Password reset email sent! Check your inbox.</span>
                </div>
              ) : (
                <form onSubmit={handleResetPassword} className="space-y-4">
                  <div>
                    <label className="block text-xs uppercase font-bold text-ink mb-1.5">
                      Email
                    </label>
                    <input
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="researcher@university.edu"
                      required
                      className="w-full px-3 py-2 border border-border text-xs focus:outline-none focus:border-[#FF6B2C]"
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setShowResetModal(false);
                        setResetEmailSent(false);
                      }}
                      className="px-4 py-2 border border-border text-xs uppercase hover:bg-pill-bg cursor-pointer"
                    >
                      Cancel
                    </button>
                    <Button
                      type="submit"
                      disabled={resetLoading}
                      className="rounded-none bg-[#FF6B2C] text-white text-xs uppercase font-bold px-4 py-2"
                    >
                      {resetLoading ? "Sending..." : "Send Reset Link"}
                    </Button>
                  </div>
                </form>
              )}

              {resetEmailSent && (
                <div className="flex justify-end pt-2">
                  <Button
                    onClick={() => {
                      setShowResetModal(false);
                      setResetEmailSent(false);
                    }}
                    className="rounded-none bg-ink text-white text-xs uppercase px-4 py-2"
                  >
                    Done
                  </Button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
