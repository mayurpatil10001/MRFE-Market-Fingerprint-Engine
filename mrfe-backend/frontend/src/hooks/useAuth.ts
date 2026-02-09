import { useCallback, useState } from "react";
import apiClient from "../api/client";

export function useAuth() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("mrfe_access_token"));

  const login = useCallback(
    async (userId: string, roles: string[] = ["trader"]) => {
      const response = await apiClient.post("/api/v1/auth/token", {
        user_id: userId,
        roles,
      });
      const accessToken = response.data.access_token as string;
      localStorage.setItem("mrfe_access_token", accessToken);
      setToken(accessToken);
      return accessToken;
    },
    []
  );

  const ensureLogin = useCallback(async () => {
    if (token) return token;
    return login("frontend_trader", ["trader"]);
  }, [login, token]);

  const logout = useCallback(() => {
    localStorage.removeItem("mrfe_access_token");
    setToken(null);
  }, []);

  return { token, login, ensureLogin, logout };
}
