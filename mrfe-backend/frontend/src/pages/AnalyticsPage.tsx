import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Progress } from "../components/ui/Progress";
import { Sparkline } from "../components/Sparkline";

const palette = [
  { name: "Primary Background", value: "#0a0a0f" },
  { name: "Secondary Background", value: "#12121a" },
  { name: "Elevated Background", value: "#1a1a26" },
  { name: "Border / Divider", value: "#252530" },
  { name: "Electric Cyan", value: "#00f0ff" },
  { name: "Neon Purple", value: "#b400ff" },
  { name: "Hot Pink", value: "#ff0080" },
  { name: "Lime Green", value: "#00ff41" },
  { name: "Electric Orange", value: "#ff6b00" },
  { name: "Electric Yellow", value: "#ffd000" },
  { name: "Primary Text", value: "#e0e6ed" },
  { name: "Secondary Text", value: "#8b92b8" },
  { name: "Tertiary Text", value: "#4b5173" },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div>
          <p className="panel-title">Component Library</p>
          <h2 className="glow-title title-lg">MRFE Neon UI Kit</h2>
          <p className="text-sm text-secondary">Reusable components for the cyberpunk trading terminal.</p>
        </div>
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <div className="space-y-3">
            <p className="panel-title">Buttons</p>
            <div className="flex flex-wrap gap-2">
              <Button>Primary Action</Button>
              <Button variant="secondary">Secondary Action</Button>
              <Button variant="secondary" className="btn-sm">Compact</Button>
            </div>
            <p className="panel-title">Inputs</p>
            <div className="grid gap-2 md:grid-cols-2">
              <Input value="SPY" onChange={() => undefined} placeholder="Symbol" />
              <Select
                value="live"
                options={[
                  { label: "Live", value: "live" },
                  { label: "Simulation", value: "sim" },
                  { label: "Backtest", value: "back" },
                ]}
                onChange={() => undefined}
              />
            </div>
            <textarea className="textarea h-24" placeholder="Multiline input" />
            <p className="panel-title">Badges</p>
            <div className="flex flex-wrap gap-2">
              <Badge label="Central Bank" tone="central" />
              <Badge label="Macroeconomic" tone="macro" />
              <Badge label="Geopolitical" tone="geo" />
              <Badge label="Financial Stress" tone="stress" />
              <Badge label="Commodity" tone="commodity" />
              <Badge label="High" tone="critical" />
              <Badge label="Medium" tone="warning" />
              <Badge label="Low" tone="positive" />
            </div>
          </div>
          <div className="space-y-3">
            <p className="panel-title">Cards</p>
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-4">
              <p className="text-sm font-semibold">Glowing Card</p>
              <p className="text-xs text-secondary">Gradient surfaces with neon edges.</p>
            </div>
            <div className="rounded-lg border border-[#252530] bg-[#1a1a26] p-4">
              <p className="text-sm font-semibold">Elevated Card</p>
              <p className="text-xs text-secondary">Used for modals or hover surfaces.</p>
            </div>
            <p className="panel-title">Charts</p>
            <div className="chart-shell">
              <Sparkline data={[0.2, 0.1, 0.15, 0.05, 0.12, 0.08, 0.18]} />
              <div className="mt-2 flex items-center justify-between text-xs text-secondary">
                <span>Forecast Line</span>
                <span>Confidence Bands</span>
              </div>
            </div>
            <p className="panel-title">Progress</p>
            <Progress value={68} />
            <p className="panel-title">Loading</p>
            <div className="flex items-center gap-3">
              <div className="skeleton h-6 w-32 rounded-md" />
              <div className="spinner" />
            </div>
          </div>
        </div>
      </Card>

      <Card className="space-y-4">
        <div>
          <p className="panel-title">Color Palette Export</p>
          <p className="text-sm text-secondary">Core MRFE cyberpunk palette with neon accents.</p>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {palette.map((color) => (
            <div key={color.name} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <div className="mb-2 h-10 rounded-md" style={{ backgroundColor: color.value }} />
              <p className="text-sm font-semibold">{color.name}</p>
              <p className="text-xs text-secondary">{color.value}</p>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card className="space-y-4">
          <div>
            <p className="panel-title">Typography</p>
            <p className="text-sm text-secondary">Futuristic headers with readable body copy.</p>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-secondary">H1 36px / 700</p>
              <h1 className="glow-title title-xl">MRFE Forecast Command Deck</h1>
            </div>
            <div>
              <p className="text-xs text-secondary">H2 28px / 700</p>
              <h2 className="glow-title title-lg">Market Reaction Intelligence</h2>
            </div>
            <div>
              <p className="text-xs text-secondary">H3 20px / 600</p>
              <h3 className="glow-title title-md">Signal Amplification Panel</h3>
            </div>
            <div>
              <p className="text-xs text-secondary">Body 14-16px</p>
              <p className="text-sm text-secondary">
                Optimized for long trading sessions. High contrast, reduced eye strain, and clear visual hierarchy.
              </p>
            </div>
            <div>
              <p className="text-xs text-secondary">Monospace Metrics</p>
              <p className="font-mono text-lg text-glow">72.3%  +2.1%</p>
            </div>
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <p className="panel-title">Motion Guidelines</p>
            <p className="text-sm text-secondary">Subtle, purposeful animations only.</p>
          </div>
          <ul className="space-y-2 text-sm text-secondary">
            <li>Pulse glow on live data surfaces (`.live-pulse`).</li>
            <li>Scanline sweep on charts during refresh (`.scanline`).</li>
            <li>Hover scale + glow on all interactive components.</li>
            <li>Staggered fade-in for cards (100ms increments).</li>
            <li>Respect `prefers-reduced-motion` to disable animation.</li>
          </ul>
          <div>
            <p className="panel-title">Interaction States</p>
            <ul className="space-y-2 text-sm text-secondary">
              <li>Hover: scale 1.02 + glow increase.</li>
              <li>Active: scale 0.98 + strong glow.</li>
              <li>Focus: cyan outline with glow.</li>
              <li>Critical alerts: magenta glow + brief shake.</li>
            </ul>
          </div>
        </Card>
      </div>

      <Card className="space-y-4">
        <div>
          <p className="panel-title">Mobile Preview (375px)</p>
          <p className="text-sm text-secondary">Stacked layout with glowing bottom nav.</p>
        </div>
        <div className="mobile-preview">
          <div className="mobile-header">
            <div>
              <p className="text-xs text-secondary">MRFE</p>
              <p className="text-sm font-semibold text-glow">Live Dashboard</p>
            </div>
            <span className="mobile-pill">LIVE</span>
          </div>
          <div className="space-y-2">
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <p className="text-xs text-secondary">Expected Move</p>
              <p className="text-lg font-semibold text-glow">-1.2%</p>
            </div>
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <p className="text-xs text-secondary">Alerts</p>
              <p className="text-lg font-semibold text-glow">6 Active</p>
            </div>
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
              <p className="text-xs text-secondary">Live Feed</p>
              <p className="text-sm">CPI surprise detected</p>
              <p className="text-xs text-tertiary">SPY -1.2% | TLT +0.8%</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
