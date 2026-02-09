import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

export function useForecasts(assetSymbol: string) {
  return useQuery({
    queryKey: ["forecasts", assetSymbol],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/forecasts", {
        params: { asset_symbol: assetSymbol, page: 1, page_size: 20 },
      });
      return response.data;
    },
  });
}
