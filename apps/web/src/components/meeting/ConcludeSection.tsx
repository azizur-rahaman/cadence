"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Eye, ListChecks, Star } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ApiClientError, submitMeetingRating } from "@/lib/api";
import type { MeetingStateDto } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

interface ConcludeSectionProps {
  meeting: MeetingStateDto;
  readOnly?: boolean;
}

const RATING_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export function ConcludeSection({ meeting, readOnly = false }: ConcludeSectionProps) {
  const { token, user } = useSession();
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const myRating = meeting.ratings.find((r) => r.user_id === user?.id)?.rating ?? null;

  const rateMutation = useMutation({
    mutationFn: async (rating: number) =>
      (await submitMeetingRating(token!, meeting.id, rating)).data,
    onSuccess: (updated) => {
      setErrorMsg(null);
      queryClient.setQueryData(["meeting", meeting.id], updated);
    },
    onError: (err) => {
      setErrorMsg(err instanceof ApiClientError ? err.message : "Failed to submit rating.");
    },
  });

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Recap New To-Dos */}
      <Card>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ListChecks className="h-4 w-4 text-primary" aria-hidden="true" />
            <h2 className="text-base font-semibold text-foreground">New To-Dos Recap</h2>
          </div>
          <Badge variant="neutral" className="tabular-nums">
            {meeting.todos_created.length} created
          </Badge>
        </div>
        <p className="mt-1 text-xs text-[#64748B]">
          Review every commitment created during this meeting before rating and closing.
        </p>

        <ul className="mt-4 space-y-2">
          {meeting.todos_created.length === 0 ? (
            <li className="rounded-md border border-dashed border-border px-4 py-6 text-center text-xs text-[#64748B]">
              No new To-Dos were created during this meeting.
            </li>
          ) : (
            meeting.todos_created.map((td) => (
              <li
                key={td.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border bg-[#F8FAFC] px-3 py-2.5 text-xs"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                  <span className="font-medium text-foreground">{td.title}</span>
                </div>
                <span className="shrink-0 text-[#64748B] tabular-nums">
                  {td.owner_name} · Due {td.due_date}
                </span>
              </li>
            ))
          )}
        </ul>
      </Card>

      {/* Rate the Meeting (1–10) */}
      <Card>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Star className="h-4 w-4 text-[#D97706]" aria-hidden="true" />
            <h2 className="text-base font-semibold text-foreground">Rate This Meeting (1–10)</h2>
          </div>
          <Badge variant="info" className="tabular-nums">
            Average: {meeting.average_rating !== null ? meeting.average_rating.toFixed(1) : "—"}
          </Badge>
        </div>

        {readOnly ? (
          <div className="mt-4 flex items-center gap-2 rounded-md border border-[#FDE68A] bg-warning-bg px-3.5 py-2.5 text-xs text-[#92400E]">
            <Eye className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Observers cannot submit a meeting rating.</span>
          </div>
        ) : (
          <div className="mt-4">
            <p className="text-xs text-[#64748B]">
              Select a score from 1 to 10. You can update your rating until the facilitator ends
              the meeting.
            </p>
            <div className="mt-3 grid grid-cols-5 gap-2 sm:grid-cols-10">
              {RATING_VALUES.map((val) => {
                const selected = myRating === val;
                return (
                  <button
                    key={val}
                    type="button"
                    disabled={rateMutation.isPending}
                    aria-pressed={selected}
                    aria-label={`Rate meeting ${val} out of 10`}
                    onClick={() => rateMutation.mutate(val)}
                    className={cn(
                      "h-10 rounded-md border text-sm font-semibold tabular-nums transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      selected
                        ? "border-primary bg-primary text-white shadow-sm"
                        : "border-border-strong bg-white text-foreground hover:border-primary hover:text-primary",
                    )}
                  >
                    {val}
                  </button>
                );
              })}
            </div>
            {errorMsg ? (
              <p role="alert" className="mt-2 text-xs font-medium text-[#DC2626]">
                {errorMsg}
              </p>
            ) : null}
          </div>
        )}

        {/* Submitted Ratings List */}
        <div className="mt-5 border-t border-border pt-4">
          <h3 className="text-xs font-semibold text-[#475569]">
            Submitted Ratings ({meeting.ratings.length})
          </h3>
          <ul className="mt-2 flex flex-wrap gap-2">
            {meeting.ratings.length === 0 ? (
              <li className="text-xs text-[#64748B]">No ratings submitted yet.</li>
            ) : (
              meeting.ratings.map((r) => (
                <li
                  key={r.user_id}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-[#F8FAFC] px-3 py-1 text-xs font-medium text-foreground"
                >
                  <span>{r.name}</span>
                  <span className="font-bold text-primary tabular-nums">{r.rating}/10</span>
                </li>
              ))
            )}
          </ul>
        </div>
      </Card>
    </div>
  );
}
