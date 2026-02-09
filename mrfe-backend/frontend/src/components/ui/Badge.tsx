type Tone =
  | "positive"
  | "neutral"
  | "warning"
  | "info"
  | "critical"
  | "macro"
  | "central"
  | "geo"
  | "stress"
  | "commodity";

type Props = {
  label: string;
  tone?: Tone;
  className?: string;
};

export function Badge({ label, tone = "neutral", className = "" }: Props) {
  const styles: Record<Tone, string> = {
    positive: "badge-positive",
    warning: "badge-warning",
    info: "badge-info",
    neutral: "badge-neutral",
    critical: "badge-critical",
    macro: "badge-macro",
    central: "badge-central",
    geo: "badge-geo",
    stress: "badge-stress",
    commodity: "badge-commodity",
  };

  return (
    <span className={`badge ${styles[tone]} ${className}`}>
      {label}
    </span>
  );
}
