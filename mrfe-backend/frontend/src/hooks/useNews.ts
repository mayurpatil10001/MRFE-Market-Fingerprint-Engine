import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

export function useNews(queryText?: string) {
  return useQuery({
    queryKey: ["news", queryText],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/news", {
        params: { page: 1, page_size: 20, query_text: queryText || undefined },
      });
      return response.data;
    },
    refetchInterval: 60000,
  });
}
