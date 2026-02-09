import { ReactNode } from "react";

type Props = {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary";
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
};

export function Button({
  children,
  onClick,
  variant = "primary",
  className = "",
  disabled = false,
  type = "button",
}: Props) {
  const style = variant === "primary" ? "btn-primary" : "btn-secondary";
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`btn ${style} ${className}`}
    >
      {children}
    </button>
  );
}
