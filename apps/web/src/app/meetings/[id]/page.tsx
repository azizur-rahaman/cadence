"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  Square,
  Users,
  Wifi,
  WifiOff,
} from "lucide-react";
import { AccessErrorView } from "@/components/layout/AccessErrorView";
import { AgendaBar } from "@/components/meeting/AgendaBar";
import { ConcludeSection } from "@/components/meeting/ConcludeSection";
import { MeetingSummary } from "@/components/meeting/MeetingSummary";
import { MeetingTimer } from "@/components/meeting/MeetingTimer";
import { IssuesSection } from "@/components/sections/IssuesSection";
import { ScorecardSection } from "@/components/sections/ScorecardSection";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  ApiClientError,
  advanceMeeting,
  endMeeting,
  fetchMeeting,
  joinMeeting,
} from "@/lib/api";
import { useMeetingSocket, type MeetingWsEvent } from "@/lib/ws";
import { cn } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

export default function LiveMeetingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: meetingId } = use(params);
  const { token, user, isLoadingSession } = useSession();
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);

  const handleWsEvent = useCallback(
    (event: MeetingWsEvent) => {
      if (event.meeting) {
        queryClient.setQueryData(["meeting", meetingId], event.meeting);
      }
      if (event.type === "workspace_updated" && event.team_id) {
        void queryClient.invalidateQueries({ queryKey: ["scorecard", event.team_id] });
        void queryClient.invalidateQueries({ queryKey: ["issues", event.team_id] });
        void queryClient.invalidateQueries({ queryKey: ["todos", event.team_id] });
        void queryClient.invalidateQueries({ queryKey: ["meeting", meetingId] });
      }
    },
    [meetingId, queryClient],
  );

  const { isConnected, onlineUserIds } = useMeetingSocket({
    meetingId,
    token,
    enabled: Boolean(token && meetingId),
    onEvent: handleWsEvent,
  });

  const meetingQuery = useQuery({
    queryKey: ["meeting", meetingId],
    enabled: Boolean(token && meetingId),
    retry: false,
    // 2s polling fallback whenever WebSocket is disconnected
    refetchInterval: isConnected ? false : 2000,
    queryFn: async () => (await fetchMeeting(token!, meetingId)).data,
  });

  // Ensure persistent attendance is recorded on initial load (even if WS takes a moment)
  useEffect(() => {
    if (!token || !meetingId || !meetingQuery.data || meetingQuery.data.section === "ended") return;
    const alreadyAttending = meetingQuery.data.attendees.some((a) => a.user_id === user?.id);
    if (!alreadyAttending) {
      void joinMeeting(token, meetingId).then((res) => {
        queryClient.setQueryData(["meeting", meetingId], res.data);
      });
    }
  }, [token, meetingId, meetingQuery.data, user?.id, queryClient]);

  const advanceMutation = useMutation({
    mutationFn: async () => (await advanceMeeting(token!, meetingId)).data,
    onSuccess: (updated) => {
      setActionError(null);
      queryClient.setQueryData(["meeting", meetingId], updated);
      void queryClient.invalidateQueries({ queryKey: ["active-meeting", updated.team_id] });
    },
    onError: (err) => {
      setActionError(err instanceof ApiClientError ? err.message : "Failed to advance section.");
    },
  });

  const endMutation = useMutation({
    mutationFn: async () => (await endMeeting(token!, meetingId)).data,
    onSuccess: (updated) => {
      setActionError(null);
      queryClient.setQueryData(["meeting", meetingId], updated);
      void queryClient.invalidateQueries({ queryKey: ["active-meeting", updated.team_id] });
    },
    onError: (err) => {
      setActionError(err instanceof ApiClientError ? err.message : "Failed to end meeting.");
    },
  });

  if (isLoadingSession || meetingQuery.isLoading) {
    return (
      <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-8">
        <Card className="animate-pulse">
          <div className="h-6 w-64 rounded bg-surface-secondary" />
          <div className="mt-4 h-48 w-full rounded bg-surface-secondary" />
        </Card>
      </main>
    );
  }

  if (meetingQuery.isError) {
    const err = meetingQuery.error;
    const isApiErr = err instanceof ApiClientError;
    return (
      <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-8">
        <AccessErrorView
          status={isApiErr ? err.status : 500}
          code={isApiErr ? err.code : undefined}
          message={err.message}
          requestId={isApiErr ? err.requestId : undefined}
        />
      </main>
    );
  }

  const meeting = meetingQuery.data;
  if (!meeting) return null;

  const isObserver = user?.role === "observer";
  const isFacilitator = user?.id === meeting.facilitator_id && !isObserver;
  const nextLabel =
    meeting.section === "scorecard"
      ? "Next: IDS"
      : meeting.section === "ids"
        ? "Next: Conclude"
        : "End Meeting";

  return (
    <main className="mx-auto max-w-[1440px] px-4 py-6 sm:px-8">
      {/* Top Meeting Control Bar */}
      <Card className="p-4 sm:p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#64748B] hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
              Team Page
            </Link>
            <div className="h-4 w-px bg-border" aria-hidden="true" />
            <AgendaBar section={meeting.section} />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <MeetingTimer
              section={meeting.section}
              timer={meeting.timer}
              serverNow={meeting.server_now}
            />

            {isFacilitator && meeting.section !== "ended" ? (
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  disabled={advanceMutation.isPending || endMutation.isPending}
                  onClick={() => advanceMutation.mutate()}
                >
                  {nextLabel}
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Button>
                {meeting.section !== "conclude" ? (
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={advanceMutation.isPending || endMutation.isPending}
                    onClick={() => endMutation.mutate()}
                  >
                    <Square className="h-3 w-3" aria-hidden="true" />
                    End
                  </Button>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>

        {/* Attendees & Live Sync Row */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 font-semibold text-[#475569]">
              <Users className="h-3.5 w-3.5" aria-hidden="true" />
              Attendees ({meeting.attendees.length}):
            </span>
            {meeting.attendees.map((att) => {
              const online = onlineUserIds.includes(att.user_id);
              return (
                <span
                  key={att.user_id}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-[#F8FAFC] px-2.5 py-0.5 text-xs font-medium text-foreground"
                >
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      online ? "bg-[#10B981]" : "bg-[#CBD5E1]",
                    )}
                    aria-hidden="true"
                  />
                  {att.name}
                  {att.user_id === meeting.facilitator_id ? (
                    <span className="text-[10px] font-semibold text-primary">Facilitator</span>
                  ) : null}
                </span>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            {isConnected ? (
              <Badge variant="success">
                <Wifi className="h-3 w-3" aria-hidden="true" />
                Live sync
              </Badge>
            ) : (
              <Badge variant="warning">
                <WifiOff className="h-3 w-3" aria-hidden="true" />
                Polling fallback
              </Badge>
            )}
          </div>
        </div>

        {actionError ? (
          <p role="alert" className="mt-2 text-xs font-medium text-[#DC2626]">
            {actionError}
          </p>
        ) : null}
      </Card>

      {/* Observer Banner */}
      {isObserver && meeting.section !== "ended" ? (
        <div
          role="status"
          className="mt-4 flex items-center gap-2 rounded-lg border border-[#FDE68A] bg-warning-bg px-4 py-2.5 text-xs text-[#92400E]"
        >
          <Eye className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>
            <strong>Observer mode:</strong> You are attending live in read-only mode.
          </span>
        </div>
      ) : null}

      {/* Active Meeting Section Workspace — Reuses ScorecardSection & IssuesSection Identically */}
      <section className="mt-6">
        {meeting.section === "scorecard" ? (
          <ScorecardSection
            teamId={meeting.team_id}
            highlightWeek={meeting.scorecard_week}
            readOnly={isObserver}
          />
        ) : meeting.section === "ids" ? (
          <IssuesSection
            teamId={meeting.team_id}
            meetingId={meeting.id}
            readOnly={isObserver}
            onMutated={() => {
              void queryClient.invalidateQueries({ queryKey: ["meeting", meeting.id] });
            }}
          />
        ) : meeting.section === "conclude" ? (
          <ConcludeSection meeting={meeting} readOnly={isObserver} />
        ) : (
          <MeetingSummary meeting={meeting} />
        )}
      </section>
    </main>
  );
}
