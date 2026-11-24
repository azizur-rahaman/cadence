"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Target,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { fetchRocks } from "@/lib/api";
import type { RockStatus } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

export interface RocksSectionProps {
  teamId: string;
}

function rockStatusBadge(status: RockStatus) {
  if (status === "complete") {
    return { variant: "info" as const, label: "Complete", Icon: CheckCircle2 };
  }
  if (status === "off_track") {
    return { variant: "danger" as const, label: "Off track", Icon: XCircle };
  }
  return { variant: "success" as const, label: "On track", Icon: CheckCircle2 };
}

export function RocksSection({ teamId }: RocksSectionProps) {
  const { token, user } = useSession();
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});

  const rocksQuery = useQuery({
    queryKey: ["rocks", teamId, user?.id],
    enabled: Boolean(token && teamId),
    queryFn: async () => (await fetchRocks(token!, teamId)).data,
  });

  function toggleExpand(rockId: string) {
    setExpandedIds((prev) => ({ ...prev, [rockId]: !prev[rockId] }));
  }

  if (rocksQuery.isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-5 w-40 rounded bg-surface-secondary" />
        <div className="mt-4 h-40 w-full rounded bg-surface-secondary" />
      </Card>
    );
  }

  if (rocksQuery.isError) {
    return (
      <Card className="border-[#FECACA] bg-[#FEF2F2]">
        <p className="text-sm font-medium text-[#991B1B]">
          Unable to load Rocks: {rocksQuery.error.message}
        </p>
      </Card>
    );
  }

  const data = rocksQuery.data;
  if (!data) return null;

  return (
    <Card className="overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-foreground">Quarterly Rocks</h2>
            <Badge variant="info">{data.quarter}</Badge>
          </div>
          <p className="mt-0.5 text-xs text-[#64748B]">
            Read-only 90-day priorities. Status and progress % are computed server-side from
            Milestones.
          </p>
        </div>
        <Badge variant="neutral" className="tabular-nums">
          {data.items.length} Rocks
        </Badge>
      </div>

      <ul className="divide-y divide-border">
        {data.items.length === 0 ? (
          <li className="px-5 py-8 text-center text-sm text-[#64748B]">
            No Rocks scheduled for {data.quarter}.
          </li>
        ) : (
          data.items.map((rock) => {
            const badge = rockStatusBadge(rock.status);
            const StatusIcon = badge.Icon;
            const expanded = Boolean(expandedIds[rock.id]);
            const hasMilestones = rock.milestones.length > 0;

            return (
              <li key={rock.id} className="px-5 py-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex min-w-0 flex-1 items-start gap-2.5">
                    <button
                      type="button"
                      disabled={!hasMilestones}
                      aria-expanded={expanded}
                      aria-label={`Toggle milestones for ${rock.title}`}
                      onClick={() => toggleExpand(rock.id)}
                      className={cn(
                        "mt-0.5 shrink-0 text-[#64748B]",
                        hasMilestones ? "hover:text-foreground" : "opacity-30",
                      )}
                    >
                      {expanded ? (
                        <ChevronDown className="h-4 w-4" aria-hidden="true" />
                      ) : (
                        <ChevronRight className="h-4 w-4" aria-hidden="true" />
                      )}
                    </button>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Target className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                        <span className="text-sm font-medium text-foreground">{rock.title}</span>
                      </div>
                      <p className="mt-0.5 text-xs text-[#64748B]">
                        Owner: {rock.owner_name} ·{" "}
                        {hasMilestones
                          ? `${rock.milestones.length} milestones`
                          : "No milestones"}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Progress Bar */}
                    <div className="flex w-36 items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-[#E2E8F0]">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all",
                            rock.status === "off_track"
                              ? "bg-[#DC2626]"
                              : rock.status === "complete"
                                ? "bg-primary"
                                : "bg-[#059669]",
                          )}
                          style={{ width: `${rock.progress_percent}%` }}
                        />
                      </div>
                      <span className="w-9 text-right text-xs font-semibold tabular-nums text-foreground">
                        {rock.progress_percent}%
                      </span>
                    </div>

                    <Badge variant={badge.variant}>
                      <StatusIcon className="h-3 w-3" aria-hidden="true" />
                      {badge.label}
                    </Badge>
                  </div>
                </div>

                {/* Expandable Milestones */}
                {expanded && hasMilestones ? (
                  <ul className="mt-3 ml-7 space-y-1.5 border-l-2 border-border pl-4">
                    {rock.milestones.map((ms) => (
                      <li
                        key={ms.id}
                        className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-[#F8FAFC] px-3 py-2 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          {ms.done ? (
                            <CheckCircle2
                              className="h-3.5 w-3.5 shrink-0 text-[#059669]"
                              aria-hidden="true"
                            />
                          ) : (
                            <Circle
                              className="h-3.5 w-3.5 shrink-0 text-[#94A3B8]"
                              aria-hidden="true"
                            />
                          )}
                          <span
                            className={cn(
                              "font-medium text-foreground",
                              ms.done && "line-through opacity-75",
                            )}
                          >
                            {ms.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="tabular-nums text-[#64748B]">Due {ms.due_date}</span>
                          {ms.is_past_due ? (
                            <Badge variant="danger">
                              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                              Past due
                            </Badge>
                          ) : ms.done ? (
                            <Badge variant="success">Done</Badge>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </li>
            );
          })
        )}
      </ul>
    </Card>
  );
}
