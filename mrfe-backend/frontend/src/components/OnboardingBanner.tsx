import { useEffect, useState } from "react";
import { Button } from "./ui/Button";

const STORAGE_KEY = "mrfe_onboarding_dismissed";

export function OnboardingBanner() {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(localStorage.getItem(STORAGE_KEY) === "true");
  }, []);

  if (dismissed) {
    return null;
  }

  return (
    <div className="panel flex flex-wrap items-center justify-between gap-3 p-4">
      <div>
        <p className="glow-title title-md">Welcome to MRFE Control Room</p>
        <p className="text-sm text-secondary">
          Track live market reactions, route alerts, and launch forecasts with a single command.
        </p>
      </div>
      <Button
        variant="secondary"
        onClick={() => {
          localStorage.setItem(STORAGE_KEY, "true");
          setDismissed(true);
        }}
      >
        Understood
      </Button>
    </div>
  );
}
