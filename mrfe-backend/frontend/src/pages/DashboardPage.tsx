import { Activity, Bell, Radar, Sparkles } from "lucide-react";
import { useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Progress } from "../components/ui/Progress";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Sparkline } from "../components/Sparkline";
import { useEvents } from "../hooks/useEvents";
import { useRealtime } from "../hooks/useRealtime";
import { useForecasts } from "../hooks/useForecasts";
import { useNews } from "../hooks/useNews";
import { useTaskStatus } from "../hooks/useTaskStatus";
import { useHealth } from "../hooks/useHealth";
import apiClient from "../api/client";

export default function DashboardPage() {
  const events = useEvents();
  const news = useNews();
  const forecasts = useForecasts("SPY");
  const realtime = useRealtime("market");
  const health = useHealth();

  const [newsProvider, setNewsProvider] = useState<"newsapi" | "alphavantage" | "combined">("combined");
  const [newsRefreshing, setNewsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<string | null>(null);

  const [taskId, setTaskId] = useState<string | null>(null);
  const [opsLoading, setOpsLoading] = useState(false);
  const taskStatus = useTaskStatus(taskId);

  const [intelProvider, setIntelProvider] = useState<"openrouter" | "anthropic" | "heuristic">("openrouter");
  const [intelSymbol, setIntelSymbol] = useState("SPY");
  const [intelContext, setIntelContext] = useState(
    "Earnings week with rates expectations anchored; positioning light and vol sellers active."
  );
  const [intelResult, setIntelResult] = useState("Run an intelligence brief to see structured scenarios.");
  const [intelLoading, setIntelLoading] = useState(false);

  const items = (events.data?.items || []) as Array<{ event_id: string; title: string; severity: string }>;
  const newsItems = (news.data?.items || []) as Array<{
    article_id: string;
    title: string;
    source: string;
    published_at: string;
  }>;
  const forecastItems = (forecasts.data?.items || []) as Array<{
    forecast_id: string;
    predicted_movement: number;
    confidence: number;
  }>;
  const severityCount = items.reduce(
    (acc, item) => {
      acc[item.severity] = (acc[item.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  async function refreshNews() {
    setNewsRefreshing(true);
    try {
      await apiClient.post(
        "/api/v1/news/refresh",
        {},
        { params: { provider: newsProvider, mode: "everything" } }
      );
      setLastRefresh(new Date().toLocaleTimeString());
      await news.refetch();
    } catch (error) {
      setLastRefresh("refresh failed");
    } finally {
      setNewsRefreshing(false);
    }
  }

  async function runEventPipeline() {
    setOpsLoading(true);
    try {
      const response = await apiClient.post("/api/v1/tasks/detect-events", { items: items.length || 24 });
      setTaskId(response.data.task_id);
    } catch (error) {
      setTaskId(null);
    } finally {
      setOpsLoading(false);
    }
  }

  async function runIntel() {
    setIntelLoading(true);
    try {
      const response = await apiClient.post("/api/v1/intel/brief", {
        symbol: intelSymbol.toUpperCase(),
        market_context: intelContext,
        horizon_hours: 24,
        risk_profile: "balanced",
        provider: intelProvider,
      });
      setIntelResult(JSON.stringify(response.data, null, 2));
    } catch (error) {
      setIntelResult("Unable to fetch intelligence. Check provider/API configuration.");
    } finally {
      setIntelLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-4">
        <MetricCard label="Events Today" value={String(items.length)} trend="up" trendLabel="Live" />
        <MetricCard label="Forecast Hit Rate" value="72%" trend="up" trendLabel="Confidence" />
        <MetricCard label="Open Alerts" value="6" trend="down" trendLabel="Resolved" />
        <MetricCard label="LLM Cost (24h)" value="$12.43" trend="flat" trendLabel="Stable" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[2.2fr_1fr]">
        <Card className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="panel-title">Forecast Command</p>
              <h2 className="glow-title title-lg">SPY Reaction Forecast: Fed Rate Hike (0.25%)</h2>
              <p className="text-sm text-secondary">
                Neural similarity engine with Monte Carlo overlays and volatility regime tagging.
              </p>
            </div>
            <Badge label={health.data?.status === "ready" ? "live" : "syncing"} tone="info" className="live-pulse" />
          </div>
          <div className="chart-shell scanline">
            <svg viewBox="0 0 600 220" className="relative z-10 h-48 w-full">
              <defs>
                <linearGradient id="mrfe-line" x1="0" x2="1" y1="0" y2="0">
                  <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.6" />
                  <stop offset="100%" stopColor="#00f0ff" stopOpacity="1" />
                </linearGradient>
              </defs>
              <polygon points="0,140 80,130 160,110 240,120 320,90 400,80 480,95 560,70 560,210 0,210" className="confidence-95" />
              <polygon points="0,150 80,142 160,128 240,138 320,110 400,96 480,110 560,88 560,210 0,210" className="confidence-90" />
              <polygon points="0,162 80,155 160,145 240,150 320,125 400,116 480,128 560,110 560,210 0,210" className="confidence-50" />
              <polyline
                points="0,160 80,150 160,130 240,140 320,110 400,95 480,110 560,85"
                fill="none"
                stroke="url(#mrfe-line)"
                strokeWidth="4"
                className="chart-line"
              />
            </svg>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <p className="text-xs text-secondary">Expected Move</p>
              <p className="text-lg font-semibold text-glow">-1.2%</p>
            </div>
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <p className="text-xs text-secondary">Confidence</p>
              <p className="text-lg font-semibold text-glow">75%</p>
            </div>
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <p className="text-xs text-secondary">Matches</p>
              <p className="text-lg font-semibold text-glow">47 patterns</p>
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="panel-title">Signal Balance</p>
              <Radar className="text-secondary" size={18} />
            </div>
            <div className="space-y-3 text-xs text-secondary">
              {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((key) => (
                <div key={key} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span>{key}</span>
                    <span>{severityCount[key] || 0}</span>
                  </div>
                  <Progress value={Math.min(100, ((severityCount[key] || 0) / Math.max(1, items.length)) * 100)} />
                </div>
              ))}
            </div>
            <div>
              <p className="text-xs text-secondary">Realtime messages</p>
              <div className="mt-2 space-y-1 text-xs">
                {realtime.messages.slice(-4).map((msg, index) => (
                  <div key={`${msg}-${index}`} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] px-2 py-1 text-tertiary">
                    {msg}
                  </div>
                ))}
                {realtime.messages.length === 0 && <p className="text-xs text-tertiary">No stream traffic yet.</p>}
              </div>
            </div>
          </Card>

          <Card className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="panel-title">Event Radar</p>
              <Activity size={16} className="text-secondary" />
            </div>
            {items.slice(0, 4).map((item) => (
              <div key={item.event_id} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
                <p className="text-sm font-semibold">{item.title}</p>
                <div className="mt-2 flex items-center gap-2 text-xs text-secondary">
                  <Badge
                    label={item.severity.toLowerCase()}
                    tone={item.severity === "CRITICAL" ? "critical" : item.severity === "HIGH" ? "warning" : "info"}
                  />
                  <span>ID {item.event_id}</span>
                </div>
              </div>
            ))}
            {items.length === 0 && !events.isLoading && <p className="text-xs text-tertiary">No events available.</p>}
          </Card>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Card className="space-y-3">
          <h3 className="panel-title">Forecast Pulse</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {forecastItems.slice(0, 4).map((forecast) => (
              <div key={forecast.forecast_id} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
                <p className="text-xs text-secondary">{forecast.forecast_id}</p>
                <p className="mt-1 text-sm font-semibold">
                  Move: {(forecast.predicted_movement * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-secondary">
                  Confidence: {(forecast.confidence * 100).toFixed(1)}%
                </p>
                <Sparkline data={[0.1, forecast.predicted_movement, 0.2, forecast.predicted_movement * 0.6, 0.3]} />
              </div>
            ))}
            {forecastItems.length === 0 && (
              <p className="text-sm text-secondary">No forecasts loaded for SPY.</p>
            )}
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="panel-title">Market News</p>
              <p className="text-xs text-secondary">NewsAPI + AlphaVantage ingest.</p>
            </div>
            <Bell className="text-secondary" size={18} />
          </div>
          {news.isLoading && <p className="text-sm text-secondary">Loading news...</p>}
          {newsItems.slice(0, 6).map((item) => (
            <div key={item.article_id} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] px-3 py-2">
              <p className="text-sm font-semibold">{item.title}</p>
              <p className="text-xs text-tertiary">{item.source}</p>
            </div>
          ))}
          {newsItems.length === 0 && !news.isLoading && (
            <p className="text-sm text-secondary">No news yet. Use Refresh News below.</p>
          )}
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_1fr]">
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="panel-title">Ops & Telemetry</p>
            <Badge
              label={health.data?.status === "ready" ? "API ready" : health.isLoading ? "checking" : "API issue"}
              tone={health.data?.status === "ready" ? "positive" : health.isLoading ? "info" : "warning"}
            />
          </div>
          <div className="grid gap-2 md:grid-cols-[1fr_1fr]">
            <Select
              value={newsProvider}
              options={[
                { label: "Combined providers", value: "combined" },
                { label: "NewsAPI only", value: "newsapi" },
                { label: "AlphaVantage only", value: "alphavantage" },
              ]}
              onChange={(value) => setNewsProvider(value as "newsapi" | "alphavantage" | "combined")}
            />
            <Button onClick={() => void refreshNews()} disabled={newsRefreshing}>
              {newsRefreshing ? "Refreshing feeds..." : "Refresh News"}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-secondary">
            <Badge
              label={taskStatus.data ? `Task ${taskStatus.data.state}` : "No active tasks"}
              tone={taskStatus.data?.state === "PROGRESS" ? "info" : "neutral"}
            />
            {lastRefresh && <Badge label={`Last refresh ${lastRefresh}`} tone="neutral" />}
            {taskId && <span className="status-chip">Task ID: {taskId}</span>}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => void runEventPipeline()} disabled={opsLoading}>
              {opsLoading ? "Enqueueing..." : "Run Event Pipeline"}
            </Button>
            <Button variant="secondary" onClick={() => setTaskId(null)} disabled={!taskId}>
              Clear Task
            </Button>
          </div>
          {taskStatus.data && (
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3 text-xs text-secondary">
              <p>Status: {taskStatus.data.state}</p>
              {typeof taskStatus.data.result?.progress === "number" && (
                <Progress value={taskStatus.data.result.progress} />
              )}
              <p>{taskStatus.data.result?.message || "Awaiting worker updates."}</p>
            </div>
          )}
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="panel-title">AI Intel Preview</p>
            <Sparkles size={16} className="text-secondary" />
          </div>
          <div className="grid gap-2 md:grid-cols-[1fr_1fr]">
            <Input value={intelSymbol} onChange={(value) => setIntelSymbol(value.toUpperCase())} placeholder="Symbol" />
            <Button onClick={() => void runIntel()} disabled={intelLoading}>
              {intelLoading ? "Generating..." : "Generate Brief"}
            </Button>
          </div>
          <Select
            value={intelProvider}
            options={[
              { label: "OpenRouter", value: "openrouter" },
              { label: "Anthropic", value: "anthropic" },
              { label: "Heuristic fallback", value: "heuristic" },
            ]}
            onChange={(value) => setIntelProvider(value as "openrouter" | "anthropic" | "heuristic")}
            className="w-full"
          />
          <textarea
            value={intelContext}
            onChange={(event) => setIntelContext(event.target.value)}
            className="textarea h-28"
          />
          <pre className="max-h-52 overflow-auto rounded-lg border border-[#252530] bg-[#0a0a0f] p-3 text-xs text-secondary">
            {intelResult}
          </pre>
        </Card>
      </div>
    </div>
  );
}
