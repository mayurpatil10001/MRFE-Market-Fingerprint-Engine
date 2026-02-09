import axios from "axios";

type ActivityListener = (pending: number) => void;

let pendingRequests = 0;
const activityListeners = new Set<ActivityListener>();

function notifyActivity() {
  activityListeners.forEach((listener) => listener(pendingRequests));
}

export function subscribeToActivity(listener: ActivityListener) {
  activityListeners.add(listener);
  listener(pendingRequests);
  return () => activityListeners.delete(listener);
}

export function getPendingRequests() {
  return pendingRequests;
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("mrfe_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  pendingRequests += 1;
  notifyActivity();
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    pendingRequests = Math.max(0, pendingRequests - 1);
    notifyActivity();
    return response;
  },
  async (error) => {
    pendingRequests = Math.max(0, pendingRequests - 1);
    notifyActivity();
    const status = error?.response?.status;
    const originalRequest = error?.config;
    if (status === 401) {
      localStorage.removeItem("mrfe_access_token");
      // Developer-friendly auto-login and retry once for common 401s.
      if (originalRequest && !originalRequest.__retryAuth) {
        originalRequest.__retryAuth = true;
        try {
          const tokenResp = await apiClient.post("/api/v1/auth/token", {
            user_id: "frontend_trader",
            roles: ["trader"],
          });
          const newToken = tokenResp.data?.access_token as string | undefined;
          if (newToken) {
            localStorage.setItem("mrfe_access_token", newToken);
            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return apiClient.request(originalRequest);
          }
        } catch {
          // fall through to reject
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
