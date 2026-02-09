import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

type EventQuery = {
  queryText?: string;
  severity?: string;
  eventType?: string;
};

export function useEvents(params?: EventQuery) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/events", {
        params: {
          page: 1,
          page_size: 20,
          query_text: params?.queryText,
          severity: params?.severity,
          event_type: params?.eventType,
        },
      });
      return response.data;
    },
    refetchInterval: 30000,
  });
}
