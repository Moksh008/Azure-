import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Bird } from "lucide-react";
import { useAuth } from "../../lib/AuthContext";

export default function ProtectedRoute({ children }: { children?: React.ReactNode }) {
  const { currentUser, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#151b31] flex flex-col items-center justify-center text-white font-mono">
        <div className="relative mb-4">
          <div className="w-12 h-12 bg-[#FF6B2C] flex items-center justify-center animate-pulse">
            <Bird className="w-7 h-7 text-white" />
          </div>
          <div className="absolute -inset-1 border border-[#FF6B2C]/40 animate-ping pointer-events-none" />
        </div>
        <div className="text-sm font-bold tracking-wider uppercase text-white">
          Authenticating Workspace...
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Verifying Firebase session credentials
        </p>
      </div>
    );
  }

  if (!currentUser) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
