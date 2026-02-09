import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

export function useTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: ["task-status", taskId],
    enabled: Boolean(taskId),
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/tasks/${taskId}`);
      return response.data as { task_id: string; state: string; result?: { progress?: number; message?: string } };
    },
    refetchInterval: taskId ? 1500 : false,
  });
}
