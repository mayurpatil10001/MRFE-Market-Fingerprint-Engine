import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Activity, Filter, Radar } from "lucide-react";
import apiClient from "../api/client";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { Select } from "../components/ui/Select";
import { Badge } from "../components/ui/Badge";
import { useEvents } from "../hooks/useEvents";

const severityTone = (value?: string) => {
  const key = (value || "").toUpperCase();
  if (key === "CRITICAL") return "critical";
  if (key === "HIGH") return "warning";
  if (key === "MEDIUM") return "info";
  return "positive";
};

export default function EventDetectionPage() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get("query") || "";
  const [title, setTitle] = useState(initialQuery || "CPI inflation surprise detected");
  const [description, setDescription] = useState(
    "Macro print shows hotter services inflation with broad-based upside surprise across shelter and wages."
  );
  const [source, setSource] = useState("frontend");
  const [result, setResult] = useState<string>("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const searchResults = useEvents(initialQuery ? { queryText: initialQuery } : undefined);

  const sourceOptions = useMemo(
    () => [
      { label: "frontend", value: "frontend" },
      { label: "wire", value: "wire" },
      { label: "research", value: "research" },
    ],
    []
  );

  async function classify() {
    setStatus("loading");
    try {
      const response = await apiClient.post("/api/v1/events/classify", {
        title,
        description,
        source,
      });
      setResult(JSON.stringify(response.data, null, 2));
      setStatus("idle");
    } catch (error) {
      setStatus("error");
    }
  }

  const items = (searchResults.data?.items || []) as Array<{
    event_id: string;
    title: string;
    event_type?: string;
    severity?: string;
  }>;

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_2fr]">
      <div className="space-y-4">
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="panel-title">Signal Classifier</p>
            <Badge label={status === "loading" ? "classifying" : "ready"} tone={status === "error" ? "warning" : "info"} />
          </div>
          <Input value={title} onChange={setTitle} placeholder="Headline" />
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="textarea h-32"
            placeholder="Paste event context here."
          />
          <div className="grid gap-3 md:grid-cols-2">
            <Select value={source} options={sourceOptions} onChange={setSource} />
            <Button onClick={() => void classify()}>{status === "loading" ? "Classifying..." : "Classify Event"}</Button>
          </div>
          <pre className="overflow-auto rounded-lg border border-[#252530] bg-[#0a0a0f] p-3 text-xs text-secondary">
            {result || "No result yet."}
          </pre>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="panel-title">Signal Filters</p>
            <Filter size={16} className="text-secondary" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge label="Central Bank" tone="central" />
            <Badge label="Macroeconomic" tone="macro" />
            <Badge label="Geopolitical" tone="geo" />
            <Badge label="Financial Stress" tone="stress" />
            <Badge label="Commodity" tone="commodity" />
          </div>
          <div className="rounded-lg border border-dashed border-[#252530] p-3 text-xs text-secondary">
            Tip: press "/" to focus global search and jump to similar events.
          </div>
        </Card>
      </div>

      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="panel-title">Event Feed</p>
            <p className="text-sm text-secondary">Realtime sentiment and macro shock scanner.</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge label={searchResults.isLoading ? "loading" : "live"} tone="info" className="live-pulse" />
            <Radar size={16} className="text-secondary" />
          </div>
        </div>
        {searchResults.isLoading && <p className="text-sm text-secondary">Streaming events...</p>}
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.event_id} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className={`severity-dot ${item.severity === "CRITICAL" || item.severity === "HIGH" ? "severity-high" : item.severity === "MEDIUM" ? "severity-medium" : "severity-low"}`} />
                  <div>
                    <p className={`text-sm font-semibold ${item.severity === "CRITICAL" ? "glitch" : ""}`}>{item.title}</p>
                    <p className="text-xs text-tertiary">Event ID: {item.event_id}</p>
                  </div>
                </div>
                <Badge label={(item.severity || "low").toLowerCase()} tone={severityTone(item.severity) as any} />
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-secondary">
                <Badge label={item.event_type?.replace("_", " ") || "macro"} tone="macro" />
                <span>Impact: SPY -1.2% | TLT +0.8%</span>
                <span className="text-tertiary">2 min ago</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button className="btn-sm">View Event</Button>
                <Button variant="secondary" className="btn-sm">Forecast</Button>
                <Button variant="secondary" className="btn-sm">Escalate</Button>
              </div>
            </div>
          ))}
          {items.length === 0 && !searchResults.isLoading && (
            <p className="text-sm text-secondary">No matches yet.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
