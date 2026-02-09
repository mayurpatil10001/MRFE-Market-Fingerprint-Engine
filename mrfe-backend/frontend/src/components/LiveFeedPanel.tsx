import { Activity } from "lucide-react";
import { useEvents } from "../hooks/useEvents";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

const categoryTone = (value?: string) => {
  const key = (value || "").toUpperCase();
  if (key.includes("CENTRAL")) return "central";
  if (key.includes("MACRO")) return "macro";
  if (key.includes("GEO")) return "geo";
  if (key.includes("STRESS")) return "stress";
  if (key.includes("COMMOD")) return "commodity";
  return "macro";
};

const severityTone = (value?: string) => {
  const key = (value || "").toUpperCase();
  if (key === "CRITICAL") return "critical";
  if (key === "HIGH") return "warning";
  if (key === "MEDIUM") return "info";
  return "positive";
};

const severityDot = (value?: string) => {
  const key = (value || "").toUpperCase();
  if (key === "CRITICAL" || key === "HIGH") return "severity-high";
  if (key === "MEDIUM") return "severity-medium";
  return "severity-low";
};

export function LiveFeedPanel() {
  const events = useEvents();
  const items = (events.data?.items || []) as Array<{ event_id: string; title: string; severity?: string; event_type?: string }>;

  return (
    <div className="panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-secondary" />
          <p className="panel-title">Live Feed</p>
        </div>
        <Badge label={events.isLoading ? "syncing" : "live"} tone="info" className="live-pulse" />
      </div>
      <div className="space-y-3">
        {events.isLoading && <p className="text-xs text-secondary">Streaming event pipeline...</p>}
        {items.slice(0, 5).map((item) => (
          <div key={item.event_id} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start gap-2">
                <span className={`severity-dot ${severityDot(item.severity)}`} />
                <div>
                  <p className={`text-sm font-semibold ${item.severity === "CRITICAL" ? "glitch" : ""}`}>{item.title}</p>
                  <p className="text-xs text-tertiary">Event ID: {item.event_id}</p>
                </div>
              </div>
              <Badge label={(item.severity || "low").toLowerCase()} tone={severityTone(item.severity) as any} />
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              <Badge label={item.event_type?.toLowerCase().replace("_", " ") || "macro"} tone={categoryTone(item.event_type) as any} />
              <span className="text-tertiary">2 min ago</span>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <Button variant="secondary" className="btn-sm">View</Button>
              <Button className="btn-sm">Forecast</Button>
            </div>
          </div>
        ))}
        {items.length === 0 && !events.isLoading && (
          <p className="text-xs text-secondary">No live events detected yet.</p>
        )}
      </div>
    </div>
  );
}
