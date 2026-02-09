import { Card } from "./ui/Card";

type Props = {
  label: string;
  value: string;
  trend?: "up" | "down" | "flat";
  trendLabel?: string;
};

export function MetricCard({ label, value, trend = "flat", trendLabel }: Props) {
  const trendClass =
    trend === "up" ? "metric-trend-up" : trend === "down" ? "metric-trend-down" : "metric-trend-flat";
  const trendSymbol = trend === "up" ? "?" : trend === "down" ? "?" : "?";
  const displayLabel = trendLabel || (trend === "up" ? "Bullish" : trend === "down" ? "Bearish" : "Stable");

  return (
    <Card className="metric-card fade-in">
      <p className="panel-title">{label}</p>
      <p className="metric-value">{value}</p>
      <p className={`text-xs ${trendClass}`}>{trendSymbol} {displayLabel}</p>
    </Card>
  );
}
