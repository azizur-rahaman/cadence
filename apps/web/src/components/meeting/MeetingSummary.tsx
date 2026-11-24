"use client";

import Link from "next/link";
import { ArrowLeft, CheckCircle2, Clock, Star, Users, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { MeetingStateDto } from "@/lib/types";

interface MeetingSummaryProps {
  meeting: MeetingStateDto;
}

export function MeetingSummary({ meeting }: MeetingSummaryProps) {
  const summary = meeting.summary;
  if (!summary) return null;

  const measurableEntries = Object.entries(summary.measurable_status);
  const attendeeNameMap = new Map(meeting.attendees.map((a) => [a.user_id, a.name]));

  return (
    <div className="space-y-6" data-testid="meeting-summary">
      {/* Top Banner */}
      <Card className="flex flex-wrap items-center justify-between gap-4 border-[#A7F3D0] bg-[#ECFDF5]/60">
        <div>
          <Badge variant="success">Immutable Meeting Summary</Badge>
          <h2 className="mt-1.5 text-lg font-semibold text-foreground">
            Level 10 Meeting Complete
          </h2>
          <p className="mt-0.5 text-xs text-[#475569]">
            Reviewed Scorecard week <strong className="tabular-nums">{summary.scorecard_week}</strong>{" "}
            · Facilitated by {meeting.facilitator_name}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded-lg border border-border bg-white px-4 py-2">
            <Star className="h-5 w-5 text-[#D97706]" aria-hidden="true" />
            <div>
              <div className="text-[11px] text-[#64748B]">Avg Rating</div>
              <div className="text-lg font-bold tabular-nums text-foreground">
                {summary.rating !== null ? `${summary.rating.toFixed(1)} / 10` : "No ratings"}
              </div>
            </div>
          </div>
          <Link href="/">
            <Button variant="secondary" size="sm">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Back to Team Page
            </Button>
          </Link>
        </div>
      </Card>

      {/* Summary Details Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Scorecard Snapshot */}
        <Card>
          <h3 className="text-sm font-semibold text-foreground">
            Scorecard Status ({summary.scorecard_week})
          </h3>
          <ul className="mt-3 space-y-2">
            {measurableEntries.map(([mid, st]) => (
              <li
                key={mid}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-xs"
              >
                <span className="font-mono font-medium text-foreground">{mid}</span>
                {st === "on_track" ? (
                  <Badge variant="success">
                    <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
                    On track
                  </Badge>
                ) : st === "off_track" ? (
                  <Badge variant="danger">
                    <XCircle className="h-3 w-3" aria-hidden="true" />
                    Off track
                  </Badge>
                ) : (
                  <Badge variant="neutral">
                    <Clock className="h-3 w-3" aria-hidden="true" />
                    Pending
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        </Card>

        {/* Outcomes & Attendees */}
        <div className="space-y-6">
          <Card>
            <h3 className="text-sm font-semibold text-foreground">Outcomes</h3>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="rounded-md border border-border bg-[#F8FAFC] p-3">
                <div className="text-xs text-[#64748B]">Issues Solved</div>
                <div className="mt-1 text-xl font-bold tabular-nums text-foreground">
                  {summary.issues_solved.length}
                </div>
                {summary.issues_solved.length > 0 ? (
                  <p className="mt-1 font-mono text-[11px] text-[#475569]">
                    {summary.issues_solved.join(", ")}
                  </p>
                ) : null}
              </div>
              <div className="rounded-md border border-border bg-[#F8FAFC] p-3">
                <div className="text-xs text-[#64748B]">To-Dos Created</div>
                <div className="mt-1 text-xl font-bold tabular-nums text-foreground">
                  {summary.todos_created.length}
                </div>
                {summary.todos_created.length > 0 ? (
                  <p className="mt-1 font-mono text-[11px] text-[#475569]">
                    {summary.todos_created.join(", ")}
                  </p>
                ) : null}
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-primary" aria-hidden="true" />
              <h3 className="text-sm font-semibold text-foreground">
                Attendees ({summary.attendee_ids.length})
              </h3>
            </div>
            <ul className="mt-3 flex flex-wrap gap-2">
              {summary.attendee_ids.map((uid) => (
                <li key={uid}>
                  <Badge variant="neutral">{attendeeNameMap.get(uid) ?? uid}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
