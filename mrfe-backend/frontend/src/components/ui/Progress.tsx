type Props = {
  value: number;
  className?: string;
};

export function Progress({ value, className = "" }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={`progress-track h-2 w-full ${className}`}>
      <div className="progress-bar" style={{ width: `${clamped}%` }} />
    </div>
  );
}
