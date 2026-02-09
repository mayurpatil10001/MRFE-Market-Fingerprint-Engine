import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { hasError: boolean; message: string };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("frontend_error_boundary", error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="panel m-6 p-6">
          <h2 className="text-lg font-semibold">Something went wrong</h2>
          <p className="mt-2 text-sm text-secondary">{this.state.message || "Unknown UI error"}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
