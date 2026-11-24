"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "./api";
import type { MeetingStateDto } from "./types";

export interface MeetingWsEvent {
  type: "snapshot" | "attendee_joined" | "state_updated" | "presence_updated" | "workspace_updated" | "pong";
  meeting?: MeetingStateDto;
  online_user_ids?: string[];
  scope?: string;
  team_id?: string;
}

function buildWsUrl(meetingId: string, token: string): string {
  const base = API_BASE_URL.replace(/^http/, "ws");
  return `${base}/api/v1/meetings/${encodeURIComponent(meetingId)}/ws?token=${encodeURIComponent(token)}`;
}

export function useMeetingSocket(params: {
  meetingId: string;
  token: string | null;
  enabled?: boolean;
  onEvent: (event: MeetingWsEvent) => void;
}) {
  const { meetingId, token, enabled = true, onEvent } = params;
  const [isConnected, setIsConnected] = useState(false);
  const [onlineUserIds, setOnlineUserIds] = useState<string[]>([]);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!enabled || !token || !meetingId) {
      setIsConnected(false);
      return;
    }

    let cancelled = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;

    function connect() {
      if (cancelled || !token) return;
      const ws = new WebSocket(buildWsUrl(meetingId, token));
      socket = ws;

      ws.onopen = () => {
        if (cancelled) return;
        attempt = 0;
        setIsConnected(true);
      };

      ws.onmessage = (msg) => {
        if (cancelled) return;
        try {
          const parsed = JSON.parse(String(msg.data)) as MeetingWsEvent;
          if (parsed.online_user_ids) {
            setOnlineUserIds(parsed.online_user_ids);
          }
          onEventRef.current(parsed);
        } catch {
          // Ignore malformed frames
        }
      };

      ws.onclose = (ev) => {
        if (cancelled) return;
        setIsConnected(false);
        // Do not retry on explicit auth/not-found close codes
        if (ev.code === 4401 || ev.code === 4404) return;
        const delay = Math.min(4000, 500 * 2 ** attempt);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
      setIsConnected(false);
    };
  }, [meetingId, token, enabled]);

  return { isConnected, onlineUserIds };
}
