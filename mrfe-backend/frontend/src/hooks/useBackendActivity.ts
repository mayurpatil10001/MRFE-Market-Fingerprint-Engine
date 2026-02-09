import { useEffect, useState } from "react";
import { getPendingRequests, subscribeToActivity } from "../api/client";

export function useBackendActivity() {
  const [pending, setPending] = useState<number>(getPendingRequests());

  useEffect(() => {
    return subscribeToActivity(setPending);
  }, []);

  return {
    pending,
    busy: pending > 0,
  };
}
