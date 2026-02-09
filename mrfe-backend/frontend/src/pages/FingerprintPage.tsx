import { useState } from "react";
import { useFingerprints } from "../hooks/useFingerprints";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";

type FingerprintItem = {
  fingerprint_id: string;
  reaction_intensity: number;
  confidence: number;
  asset_symbol: string;
  duration_minutes: number;
  volatility_impact: number;
  volume_impact: number;
};

export default function FingerprintPage() {
  const [symbol, setSymbol] = useState("SPY");
  const fingerprints = useFingerprints(symbol);
  const items = (fingerprints.data?.items || []) as FingerprintItem[];

  return (
    <div className="space-y-4">
      <Card className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="panel-title">Fingerprint Library</p>
          <Badge label="Similarity indexed" tone="info" />
        </div>
        <Input value={symbol} onChange={(value) => setSymbol(value.toUpperCase())} placeholder="Asset symbol" />
      </Card>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item) => (
          <Card key={item.fingerprint_id} className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs text-secondary">{item.fingerprint_id}</p>
              <Badge
                label={`${(item.confidence * 100).toFixed(0)}%`}
                tone={item.confidence > 0.7 ? "positive" : "neutral"}
              />
            </div>
            <div className="grid gap-2 text-sm md:grid-cols-2">
              <p>Intensity: {(item.reaction_intensity * 100).toFixed(1)}%</p>
              <p>Duration: {item.duration_minutes} min</p>
              <p>Volatility: {(item.volatility_impact * 100).toFixed(1)}%</p>
              <p>Volume: {(item.volume_impact * 100).toFixed(1)}%</p>
            </div>
          </Card>
        ))}
        {items.length === 0 && <Card>No fingerprints for {symbol}.</Card>}
      </div>
    </div>
  );
}
