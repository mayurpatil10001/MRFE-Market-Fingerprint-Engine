import { useState } from "react";
import { ArrowUpRight, Share2, Star } from "lucide-react";
import { useForecasts } from "../hooks/useForecasts";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";
import { Sparkline } from "../components/Sparkline";
import { Button } from "../components/ui/Button";

type ForecastItem = {
  forecast_id: string;
  predicted_movement: number;
  confidence: number;
  probability_distribution: Record<string, number>;
  risk_metrics: Record<string, number>;
};

export default function ForecastPage() {
  const [symbol, setSymbol] = useState("SPY");
  const forecasts = useForecasts(symbol);
  const items = (forecasts.data?.items || []) as ForecastItem[];
  const primary = items[0];

  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="panel-title">Forecast Detail</p>
            <h2 className="glow-title title-lg">{symbol.toUpperCase()} Reaction Forecast: Fed Rate Hike (0.25%)</h2>
            <p className="text-sm text-secondary">
              MRFE similarity engine + Monte Carlo horizon modeling. Updated 2 min ago.
            </p>
          </div>
          <Badge label="live" tone="info" className="live-pulse" />
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
            <p className="text-xs text-secondary">Expected</p>
            <p className="text-lg font-semibold text-glow">{primary ? `${(primary.predicted_movement * 100).toFixed(2)}%` : "-1.2%"}</p>
            <p className="text-xs text-tertiary">2-day move</p>
          </div>
          <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
            <p className="text-xs text-secondary">Confidence</p>
            <p className="text-lg font-semibold text-glow">{primary ? `${(primary.confidence * 100).toFixed(0)}%` : "75%"}</p>
            <p className="text-xs text-tertiary">Model ensemble</p>
          </div>
          <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
            <p className="text-xs text-secondary">Matches</p>
            <p className="text-lg font-semibold text-glow">47 patterns</p>
            <p className="text-xs text-tertiary">Fingerprint similarity</p>
          </div>
          <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-3">
            <p className="text-xs text-secondary">Last Update</p>
            <p className="text-lg font-semibold text-glow">2 min ago</p>
            <p className="text-xs text-tertiary">Live</p>
          </div>
        </div>
        <div className="chart-shell scanline">
          <svg viewBox="0 0 600 240" className="relative z-10 h-56 w-full">
            <defs>
              <linearGradient id="forecast-line" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.7" />
                <stop offset="100%" stopColor="#00f0ff" stopOpacity="1" />
              </linearGradient>
            </defs>
            <polygon points="0,160 80,150 160,142 240,145 320,118 400,105 480,115 560,90 560,220 0,220" className="confidence-95" />
            <polygon points="0,170 80,160 160,155 240,160 320,130 400,120 480,130 560,105 560,220 0,220" className="confidence-90" />
            <polygon points="0,182 80,172 160,168 240,170 320,145 400,135 480,142 560,125 560,220 0,220" className="confidence-50" />
            <polyline
              points="0,180 80,165 160,155 240,160 320,130 400,115 480,128 560,100"
              fill="none"
              stroke="url(#forecast-line)"
              strokeWidth="4"
              className="chart-line"
            />
          </svg>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button className="flex items-center gap-2"><ArrowUpRight size={14} />Export PDF</Button>
          <Button variant="secondary" className="flex items-center gap-2"><Share2 size={14} />Share</Button>
          <Button variant="secondary" className="flex items-center gap-2"><Star size={14} />Add to Watchlist</Button>
        </div>
      </Card>

      <Card className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="panel-title">Most Likely Patterns</p>
          <Input value={symbol} onChange={(value) => setSymbol(value.toUpperCase())} placeholder="Asset symbol" className="max-w-[140px]" />
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {items.slice(0, 4).map((item, index) => (
            <div key={item.forecast_id} className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold">Pattern {index + 1}: {item.forecast_id}</p>
                <Badge label={`${(item.confidence * 100).toFixed(0)}% likely`} tone="info" />
              </div>
              <p className="mt-2 text-xs text-secondary">
                Drops {(item.predicted_movement * 100).toFixed(2)}% first hour, recovery by session close.
              </p>
              <div className="mt-3">
                <Sparkline data={[0.2, item.predicted_movement, 0.18, item.predicted_movement * 0.6, 0.25]} />
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <div className="rounded-lg border border-[#252530] bg-[rgba(10,10,15,0.6)] p-4">
              <p className="text-sm text-secondary">No forecasts for {symbol}.</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
