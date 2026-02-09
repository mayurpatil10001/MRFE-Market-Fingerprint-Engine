import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/health/ready");
      return response.data as { status: string };
    },
    refetchInterval: 15000,
  });
}
