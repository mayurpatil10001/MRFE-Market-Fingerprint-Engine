import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Activity, Bell, Bolt, LayoutGrid, LineChart, Library, Search, Shield, User } from "lucide-react";
import { Button } from "./components/ui/Button";
import DashboardPage from "./pages/DashboardPage";
import EventDetectionPage from "./pages/EventDetectionPage";
import ForecastPage from "./pages/ForecastPage";
import FingerprintPage from "./pages/FingerprintPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import { useAuth } from "./hooks/useAuth";
import { useRealtime } from "./hooks/useRealtime";
import { Toggle } from "./components/ui/Toggle";
import { OnboardingBanner } from "./components/OnboardingBanner";
import { useHealth } from "./hooks/useHealth";
import { useBackendActivity } from "./hooks/useBackendActivity";
import { LiveFeedPanel } from "./components/LiveFeedPanel";
import { Progress } from "./components/ui/Progress";

export default function App() {
  const { token, ensureLogin, login, logout } = useAuth();
  const { connected } = useRealtime("market");
  const { busy, pending } = useBackendActivity();
  const health = useHealth();
  const navigate = useNavigate();
  const searchRef = useRef<HTMLInputElement | null>(null);
  const [searchValue, setSearchValue] = useState("");
  const [compact, setCompact] = useState(localStorage.getItem("mrfe_compact") === "true");
  const [lowGlow, setLowGlow] = useState(localStorage.getItem("mrfe_low_glow") === "true");
  const autoLoginAttempted = useRef(false);
  const apiBase = import.meta.env.VITE_API_BASE_URL || window.location.origin;

  useEffect(() => {
    document.body.classList.add("theme-dark");
  }, []);

  useEffect(() => {
    document.body.classList.toggle("compact-mode", compact);
    localStorage.setItem("mrfe_compact", compact ? "true" : "false");
  }, [compact]);

  useEffect(() => {
    document.body.classList.toggle("reduce-glow", lowGlow);
    localStorage.setItem("mrfe_low_glow", lowGlow ? "true" : "false");
  }, [lowGlow]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "/" && searchRef.current) {
        event.preventDefault();
        searchRef.current.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    if (!token && !autoLoginAttempted.current) {
      autoLoginAttempted.current = true;
      void ensureLogin().catch(() => {
        autoLoginAttempted.current = false;
      });
    }
  }, [ensureLogin, token]);

  return (
    <div className="app-shell">
      <header className="top-nav">
        <div className="app-container top-nav-inner">
          <div className="nav-logo">
            <span>MRFE</span>
            <span>Market Reaction Fingerprint Engine</span>
          </div>
          <form
            className="nav-search"
            onSubmit={(event) => {
              event.preventDefault();
              if (searchValue.trim()) {
                navigate(`/events?query=${encodeURIComponent(searchValue.trim())}`);
              }
            }}
          >
            <Search size={14} className="text-tertiary" />
            <input
              ref={searchRef}
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              placeholder='Global search ("/")'
              aria-label="Global search"
            />
          </form>
          <div className="nav-actions">
            <button className="nav-icon" aria-label="Notifications">
              <Bell size={16} />
              <span className="nav-badge">3</span>
            </button>
            <button className="nav-icon" aria-label="System alerts">
              <Bolt size={16} />
            </button>
            <button className="nav-icon" aria-label="User profile">
              <User size={16} />
            </button>
            <div className="flex items-center gap-2">
              <Toggle checked={lowGlow} onChange={setLowGlow} label="Low Glow" />
              <Toggle checked={compact} onChange={setCompact} label="Compact" />
            </div>
            {token ? (
              <Button variant="secondary" onClick={logout}>Logout</Button>
            ) : (
              <Button onClick={() => void login("frontend_trader", ["trader"])}>Quick Login</Button>
            )}
          </div>
        </div>
      </header>

      <div className="app-container">
        <div className="status-strip">
          <span className="status-chip">
            <span className={`severity-dot ${health.data?.status === "ready" ? "severity-low" : "severity-medium"}`} />
            {health.data?.status === "ready" ? "API ready" : health.isLoading ? "API checking" : "API issue"}
          </span>
          <span className="status-chip">
            <span className={`severity-dot ${connected ? "severity-low" : "severity-medium"}`} />
            {connected ? "WS connected" : "WS offline"}
          </span>
          <span className="status-chip">
            <span className={`severity-dot ${busy ? "severity-medium" : "severity-low"}`} />
            {busy ? `Backend busy (${pending})` : "Backend idle"}
          </span>
          <span className="status-chip">
            <Shield size={12} className="text-tertiary" />
            {token ? "Authed" : "Guest"}
          </span>
          <span className="status-chip">API base: {apiBase}</span>
        </div>

        <div className="content-grid">
          <aside className="sidebar">
            <NavLink end to="/" className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}>
              <LayoutGrid size={16} /> Dashboard
            </NavLink>
            <NavLink to="/events" className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}>
              <Activity size={16} /> Event Feed
            </NavLink>
            <NavLink to="/forecasts" className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}>
              <LineChart size={16} /> Forecasts
            </NavLink>
            <NavLink to="/fingerprints" className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}>
              <Bolt size={16} /> Fingerprints
            </NavLink>
            <NavLink to="/analytics" className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}>
              <Library size={16} /> Library
            </NavLink>
          </aside>

          <main className="space-y-6 fade-in">
            <OnboardingBanner />
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/events" element={<EventDetectionPage />} />
              <Route path="/forecasts" element={<ForecastPage />} />
              <Route path="/fingerprints" element={<FingerprintPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Routes>
          </main>

          <aside className="right-rail">
            <LiveFeedPanel />
            <div className="panel p-4 space-y-3">
              <p className="panel-title">System Pulse</p>
              <div className="flex items-center justify-between text-xs text-secondary">
                <span>Inference Queue</span>
                <span>{busy ? "Active" : "Idle"}</span>
              </div>
              <Progress value={busy ? 72 : 28} />
              <div className="flex items-center justify-between text-xs text-secondary">
                <span>Model Registry</span>
                <span>{connected ? "Synced" : "Pending"}</span>
              </div>
              <Progress value={connected ? 84 : 40} />
              <div className="glow-divider" />
              <div className="text-xs text-secondary">Latency SLA: 180ms | Drift Alerts: 2</div>
            </div>
          </aside>
        </div>
      </div>

      <nav className="bottom-nav">
        <NavLink end to="/" className={({ isActive }) => (isActive ? "active" : "")}>
          <LayoutGrid size={16} />
          Dashboard
        </NavLink>
        <NavLink to="/events" className={({ isActive }) => (isActive ? "active" : "")}>
          <Activity size={16} />
          Events
        </NavLink>
        <NavLink to="/forecasts" className={({ isActive }) => (isActive ? "active" : "")}>
          <LineChart size={16} />
          Forecasts
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => (isActive ? "active" : "")}>
          <Library size={16} />
          Library
        </NavLink>
      </nav>
    </div>
  );
}
