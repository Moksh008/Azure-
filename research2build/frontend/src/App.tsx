import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppDataProvider } from "./lib/AppDataContext";
import { AuthProvider } from "./lib/AuthContext";
import ProtectedRoute from "./components/shared/ProtectedRoute";
import LandingPage from "./components/LandingPage";
import LoginPage from "./components/pages/LoginPage";
import ChatPage from "./components/pages/ChatPage";
import ComparisonPage from "./components/pages/ComparisonPage";
import DeliverablesPage from "./components/pages/DeliverablesPage";
import FeasibilityDashboardPage from "./components/pages/FeasibilityDashboardPage";
import OpportunityExplorerPage from "./components/pages/OpportunityExplorerPage";
import PaperAnalysisPage from "./components/pages/PaperAnalysisPage";
import ProjectGeneratorPage from "./components/pages/ProjectGeneratorPage";
import QAPage from "./components/pages/QAPage";
import TopicDiscoveryPage from "./components/pages/TopicDiscoveryPage";
import UploadPage from "./components/pages/UploadPage";

function App() {
  return (
    <AuthProvider>
      <AppDataProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<LoginPage />} />

            {/* Protected Dashboard & Intelligence Routes */}
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/discover" element={<TopicDiscoveryPage />} />
              <Route path="/analysis" element={<PaperAnalysisPage />} />
              <Route path="/qa" element={<QAPage />} />
              <Route path="/compare" element={<ComparisonPage />} />
              <Route path="/opportunities" element={<OpportunityExplorerPage />} />
              <Route path="/projects" element={<ProjectGeneratorPage />} />
              <Route path="/feasibility" element={<FeasibilityDashboardPage />} />
              <Route path="/deliverables" element={<DeliverablesPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AppDataProvider>
    </AuthProvider>
  );
}

export default App;
