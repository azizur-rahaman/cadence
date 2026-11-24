"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Clock } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import type { MeetingSection, MeetingTimerDto } from "@/lib/types";
import { cn } from "@/lib/utils";

interface MeetingTimerProps {
  section: MeetingSection;
  timer: MeetingTimerDto;
  serverNow: string;
}

function formatClock(totalSeconds: number): string {
  const abs = Math.abs(Math.trunc(totalSeconds));
  const mins = Math.floor(abs / 60);
  const secs = abs % 60;
  const formatted = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  return totalSeconds < 0 ? `+${formatted}` : formatted;
}

export function MeetingTimer({ section, timer, serverNow }: MeetingTimerProps) {
  const [localOffsetSec, setLocalOffsetSec] = useState(0);

  // Snap to authoritative server snapshot whenever timer or serverNow updates
  useEffect(() => {
    setLocalOffsetSec(0);
    if (section === "ended") return;
    const id = setInterval(() => {
      setLocalOffsetSec((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(id);
  }, [section, timer.remaining_seconds, serverNow]);

  if (section === "ended") {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-border bg-[#F8FAFC] px-4 py-2">
        <Clock className="h-4 w-4 text-[#64748B]" aria-hidden="true" />
        <span className="text-sm font-semibold text-[#475569]">Meeting Ended</span>
      </div>
    );
  }

  const remaining = timer.remaining_seconds - localOffsetSec;
  const isOverTime = timer.over_time || remaining < 0;

  return (
    <div
      data-testid="meeting-timer"
      className={cn(
        "flex items-center gap-3 rounded-lg border px-4 py-2 transition-colors",
        isOverTime
          ? "border-[#FCA5A5] bg-[#FEF2F2] text-[#991B1B]"
          : "border-border bg-white text-foreground",
      )}
    >
      {isOverTime ? (
        <AlertTriangle className="h-5 w-5 shrink-0 text-[#DC2626]" aria-hidden="true" />
      ) : (
        <Clock className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
      )}
      <span className="font-mono text-2xl font-bold tracking-tight tabular-nums">
        {formatClock(remaining)}
      </span>
      {isOverTime ? <Badge variant="danger">Over time</Badge> : null}
    </div>
  );
}
