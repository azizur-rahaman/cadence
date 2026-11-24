"use client";

import { CheckCircle2 } from "lucide-react";
import type { MeetingSection } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AgendaBarProps {
  section: MeetingSection;
}

const STEPS: Array<{ id: Exclude<MeetingSection, "ended">; label: string; duration: string }> = [
  { id: "scorecard", label: "Scorecard", duration: "5m" },
  { id: "ids", label: "IDS", duration: "60m" },
  { id: "conclude", label: "Conclude", duration: "10m" },
];

const ORDER: Record<MeetingSection, number> = {
  scorecard: 0,
  ids: 1,
  conclude: 2,
  ended: 3,
};

export function AgendaBar({ section }: AgendaBarProps) {
  const currentIdx = ORDER[section];

  return (
    <ol aria-label="Meeting agenda" className="flex flex-wrap items-center gap-2">
      {STEPS.map((step, idx) => {
        const isDone = currentIdx > idx;
        const isActive = currentIdx === idx;
        return (
          <li
            key={step.id}
            data-active={isActive ? "true" : "false"}
            className={cn(
              "inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-colors",
              isActive && "border-primary bg-primary text-white shadow-sm",
              isDone && "border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46]",
              !isActive && !isDone && "border-border bg-white text-[#64748B]",
            )}
          >
            {isDone ? (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <span className="tabular-nums">{idx + 1}.</span>
            )}
            <span>{step.label}</span>
            <span className={cn("text-[11px] tabular-nums", isActive ? "opacity-90" : "opacity-70")}>
              ({step.duration})
            </span>
          </li>
        );
      })}
    </ol>
  );
}
