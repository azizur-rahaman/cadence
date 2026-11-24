"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, Clock, Link2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import {
  ApiClientError,
  fetchScorecard,
  makeIssueFromMeasurable,
  upsertScore,
} from "@/lib/api";
import type { IssueDto, MeasurableStatus, ScoreCellDto } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

export interface ScorecardSectionProps {
  teamId: string;
  highlightWeek?: string;
  readOnly?: boolean;
  onIssueCreated?: (issue: IssueDto, created: boolean) => void;
  onMutated?: () => void;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatShortWeek(weekIso: string): string {
  const parts = weekIso.split("-");
  if (parts.length !== 3) return weekIso;
  const monthIdx = Number(parts[1]) - 1;
  const day = Number(parts[2]);
  return `${MONTHS[monthIdx] ?? parts[1]} ${day}`;
}

function formatScoreValue(val: number | null): string {
  if (val === null) return "—";
  return Number.isInteger(val) ? String(val) : String(val);
}

function statusMeta(status: MeasurableStatus) {
  if (status === "on_track") {
    return {
      cellClass: "bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]",
      label: "On track",
      Icon: CheckCircle2,
    };
  }
  if (status === "off_track") {
    return {
      cellClass: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]",
      label: "Off track",
      Icon: XCircle,
    };
  }
  return {
    cellClass: "bg-[#F8FAFC] text-[#475569] border-[#E2E8F0]",
    label: "Pending",
    Icon: Clock,
  };
}

export function ScorecardSection({
  teamId,
  highlightWeek,
  readOnly = false,
  onIssueCreated,
  onMutated,
}: ScorecardSectionProps) {
  const { token, user } = useSession();
  const queryClient = useQueryClient();

  const [editingCell, setEditingCell] = useState<{
    measurableId: string;
    weekStart: string;
    draft: string;
  } | null>(null);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "info" | "error";
    text: string;
  } | null>(null);

  const scorecardQuery = useQuery({
    queryKey: ["scorecard", teamId, user?.id],
    enabled: Boolean(token && teamId),
    queryFn: async () => (await fetchScorecard(token!, teamId)).data,
  });

  const upsertMutation = useMutation({
    mutationFn: async (vars: { measurableId: string; weekStart: string; value: number }) =>
      (await upsertScore(token!, teamId, vars.measurableId, vars.weekStart, vars.value)).data,
    onSuccess: (updated) => {
      setEditingCell(null);
      setFeedback({
        tone: "success",
        text: `Saved score ${updated.value} for week of ${formatShortWeek(updated.week_start)} (${statusMeta(updated.status).label}).`,
      });
      void queryClient.invalidateQueries({ queryKey: ["scorecard", teamId] });
      onMutated?.();
    },
    onError: (err) => {
      setFeedback({
        tone: "error",
        text: err instanceof ApiClientError ? err.message : "Failed to save score.",
      });
    },
  });

  const makeIssueMutation = useMutation({
    mutationFn: async (vars: { measurableId: string; weekStart: string }) =>
      (await makeIssueFromMeasurable(token!, teamId, vars.measurableId, vars.weekStart)).data,
    onSuccess: (res) => {
      setFeedback({
        tone: res.created ? "success" : "info",
        text: res.created
          ? `Created Issue: "${res.issue.title}"`
          : `Already linked to unsolved Issue: "${res.issue.title}"`,
      });
      void queryClient.invalidateQueries({ queryKey: ["scorecard", teamId] });
      void queryClient.invalidateQueries({ queryKey: ["issues", teamId] });
      onIssueCreated?.(res.issue, res.created);
      onMutated?.();
    },
    onError: (err) => {
      setFeedback({
        tone: "error",
        text: err instanceof ApiClientError ? err.message : "Failed to create Issue.",
      });
    },
  });

  function startEdit(measurableId: string, cell: ScoreCellDto) {
    if (readOnly) return;
    setFeedback(null);
    setEditingCell({
      measurableId,
      weekStart: cell.week_start,
      draft: cell.value !== null ? String(cell.value) : "",
    });
  }

  function commitEdit() {
    if (!editingCell) return;
    const trimmed = editingCell.draft.trim();
    if (trimmed === "") {
      setEditingCell(null);
      return;
    }
    const num = Number(trimmed);
    if (!Number.isFinite(num)) {
      setFeedback({ tone: "error", text: "Please enter a valid number." });
      return;
    }
    upsertMutation.mutate({
      measurableId: editingCell.measurableId,
      weekStart: editingCell.weekStart,
      value: num,
    });
  }

  if (scorecardQuery.isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-5 w-40 rounded bg-surface-secondary" />
        <div className="mt-4 h-48 w-full rounded bg-surface-secondary" />
      </Card>
    );
  }

  if (scorecardQuery.isError) {
    return (
      <Card className="border-[#FECACA] bg-[#FEF2F2]">
        <p className="text-sm font-medium text-[#991B1B]">
          Unable to load Scorecard: {scorecardQuery.error.message}
        </p>
      </Card>
    );
  }

  const scorecard = scorecardQuery.data;
  if (!scorecard) return null;

  const effectiveHighlight = highlightWeek ?? scorecard.last_closed_week_start;

  return (
    <Card className="overflow-hidden p-0">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-foreground">13-Week Scorecard</h2>
          <p className="mt-0.5 text-xs text-[#64748B]">
            {readOnly
              ? "Read-only view. Statuses are computed server-side."
              : "Click any cell to enter or update a score. Turn off-track cells into Issues in one click."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="success">
            <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
            On track
          </Badge>
          <Badge variant="danger">
            <XCircle className="h-3 w-3" aria-hidden="true" />
            Off track
          </Badge>
          <Badge variant="neutral">
            <Clock className="h-3 w-3" aria-hidden="true" />
            Pending
          </Badge>
        </div>
      </div>

      {/* Inline Feedback Banner */}
      {feedback ? (
        <div
          role="status"
          className={cn(
            "flex items-center justify-between border-b px-5 py-2.5 text-xs font-medium",
            feedback.tone === "success" && "border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46]",
            feedback.tone === "info" && "border-[#BFDBFE] bg-[#EFF6FF] text-[#1D4ED8]",
            feedback.tone === "error" && "border-[#FECACA] bg-[#FEF2F2] text-[#991B1B]",
          )}
        >
          <span>{feedback.text}</span>
          <button
            type="button"
            onClick={() => setFeedback(null)}
            className="ml-4 underline opacity-80 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      ) : null}

      {/* Scrollable 13-Week Grid */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-border bg-[#F8FAFC] text-[#475569]">
              <th className="sticky left-0 z-10 min-w-[200px] border-r border-border bg-[#F8FAFC] px-4 py-3 font-semibold">
                Measurable
              </th>
              <th className="min-w-[110px] border-r border-border px-3 py-3 font-semibold">
                Owner
              </th>
              <th className="min-w-[96px] border-r border-border px-3 py-3 font-semibold">
                Goal
              </th>
              {scorecard.weeks.map((week) => {
                const isHighlighted = week === effectiveHighlight;
                const isCurrent = week === scorecard.current_week_start;
                return (
                  <th
                    key={week}
                    className={cn(
                      "min-w-[92px] border-r border-border px-2.5 py-2.5 text-center font-semibold tabular-nums last:border-r-0",
                      isHighlighted && "bg-[#EEF2FF] text-primary",
                    )}
                  >
                    <div>{formatShortWeek(week)}</div>
                    {highlightWeek && week === highlightWeek ? (
                      <span className="mt-0.5 inline-block rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                        Review
                      </span>
                    ) : isCurrent ? (
                      <span className="mt-0.5 inline-block rounded bg-[#E2E8F0] px-1.5 py-0.5 text-[10px] font-medium text-[#475569]">
                        Current
                      </span>
                    ) : null}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {scorecard.measurables.map((row) => (
              <tr key={row.id} className="group hover:bg-[#FAFAFC]">
                <td className="sticky left-0 z-10 border-r border-border bg-white px-4 py-3 group-hover:bg-[#FAFAFC]">
                  <div className="font-medium text-foreground">{row.name}</div>
                  <div className="mt-0.5 text-[11px] text-[#64748B]">{row.unit}</div>
                </td>
                <td className="border-r border-border px-3 py-3 text-[#475569]">
                  {row.owner_name}
                </td>
                <td className="border-r border-border px-3 py-3 font-medium tabular-nums text-foreground">
                  {row.goal.label}
                </td>
                {row.cells.map((cell) => {
                  const meta = statusMeta(cell.status);
                  const Icon = meta.Icon;
                  const isEditing =
                    editingCell?.measurableId === row.id &&
                    editingCell?.weekStart === cell.week_start;
                  const isHighlighted = cell.week_start === effectiveHighlight;
                  const isMakingIssue =
                    makeIssueMutation.isPending &&
                    makeIssueMutation.variables?.measurableId === row.id &&
                    makeIssueMutation.variables?.weekStart === cell.week_start;

                  return (
                    <td
                      key={cell.week_start}
                      className={cn(
                        "border-r border-border p-1.5 text-center align-top last:border-r-0",
                        isHighlighted && "bg-[#EEF2FF]/40",
                      )}
                    >
                      <div
                        className={cn(
                          "flex min-h-[54px] flex-col items-center justify-center rounded-md border px-1.5 py-1 transition-colors",
                          meta.cellClass,
                          !readOnly && !isEditing && "cursor-pointer hover:brightness-95",
                        )}
                        onClick={() => {
                          if (!isEditing) startEdit(row.id, cell);
                        }}
                      >
                        {isEditing ? (
                          <input
                            type="number"
                            step="any"
                            autoFocus
                            aria-label={`Score for ${row.name}, week of ${cell.week_start}`}
                            value={editingCell.draft}
                            onChange={(e) =>
                              setEditingCell({ ...editingCell, draft: e.target.value })
                            }
                            onClick={(e) => e.stopPropagation()}
                            onBlur={commitEdit}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                e.preventDefault();
                                commitEdit();
                              } else if (e.key === "Escape") {
                                setEditingCell(null);
                              }
                            }}
                            className="w-16 rounded border border-primary bg-white px-1.5 py-0.5 text-center text-xs font-semibold tabular-nums text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                          />
                        ) : (
                          <>
                            <div className="flex items-center gap-1 text-xs font-semibold tabular-nums">
                              <Icon className="h-3 w-3 shrink-0" aria-hidden="true" />
                              <span>{formatScoreValue(cell.value)}</span>
                            </div>
                            <span className="sr-only">{meta.label}</span>
                          </>
                        )}

                        {/* Off-track Make it an Issue / Linked badge */}
                        {cell.status === "off_track" && !isEditing ? (
                          cell.unsolved_issue_id ? (
                            <span
                              title={`Linked to unsolved Issue ${cell.unsolved_issue_id}`}
                              className="mt-1 inline-flex items-center gap-0.5 rounded bg-white/80 px-1.5 py-0.5 text-[10px] font-medium text-[#991B1B]"
                            >
                              <Link2 className="h-2.5 w-2.5" aria-hidden="true" />
                              Issue
                            </span>
                          ) : !readOnly ? (
                            <button
                              type="button"
                              disabled={isMakingIssue}
                              onClick={(e) => {
                                e.stopPropagation();
                                makeIssueMutation.mutate({
                                  measurableId: row.id,
                                  weekStart: cell.week_start,
                                });
                              }}
                              className="mt-1 inline-flex items-center gap-0.5 rounded bg-white px-1.5 py-0.5 text-[10px] font-semibold text-[#991B1B] shadow-sm ring-1 ring-[#FCA5A5] transition-colors hover:bg-[#991B1B] hover:text-white disabled:opacity-50"
                            >
                              <AlertCircle className="h-2.5 w-2.5" aria-hidden="true" />
                              {isMakingIssue ? "..." : "Make Issue"}
                            </button>
                          ) : null
                        ) : null}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
