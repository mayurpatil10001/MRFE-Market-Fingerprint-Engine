type Option = { label: string; value: string };

type Props = {
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  className?: string;
};

export function Select({ value, options, onChange, className = "" }: Props) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={`select ${className}`}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
