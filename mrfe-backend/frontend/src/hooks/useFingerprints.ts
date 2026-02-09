import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

export function useFingerprints(assetSymbol: string) {
  return useQuery({
    queryKey: ["fingerprints", assetSymbol],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/fingerprints", {
        params: { asset_symbol: assetSymbol, page: 1, page_size: 20 },
      });
      return response.data;
    },
  });
}
