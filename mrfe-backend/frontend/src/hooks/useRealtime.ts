import { useEffect, useState } from "react";

export function useRealtime(topic: string) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/${topic}`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => setMessages((prev) => [...prev.slice(-20), event.data]);
    return () => ws.close();
  }, [topic]);

  return { connected, messages };
}
