"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Circle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ApiClientError, fetchTodos, toggleTodoDone } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

export interface TodosSectionProps {
  teamId: string;
  readOnly?: boolean;
  onMutated?: () => void;
}

export function TodosSection({ teamId, readOnly = false, onMutated }: TodosSectionProps) {
  const { token, user } = useSession();
  const queryClient = useQueryClient();

  const [showCompleted, setShowCompleted] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const todosQuery = useQuery({
    queryKey: ["todos", teamId, user?.id],
    enabled: Boolean(token && teamId),
    queryFn: async () => (await fetchTodos(token!, teamId)).data,
  });

  const toggleMutation = useMutation({
    mutationFn: async (vars: { todoId: string; done: boolean }) =>
      (await toggleTodoDone(token!, vars.todoId, vars.done)).data,
    onSuccess: () => {
      setErrorMsg(null);
      void queryClient.invalidateQueries({ queryKey: ["todos", teamId] });
      onMutated?.();
    },
    onError: (err) => {
      setErrorMsg(err instanceof ApiClientError ? err.message : "Failed to update To-Do.");
    },
  });

  if (todosQuery.isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-5 w-36 rounded bg-surface-secondary" />
        <div className="mt-4 h-40 w-full rounded bg-surface-secondary" />
      </Card>
    );
  }

  if (todosQuery.isError) {
    return (
      <Card className="border-[#FECACA] bg-[#FEF2F2]">
        <p className="text-sm font-medium text-[#991B1B]">
          Unable to load To-Dos: {todosQuery.error.message}
        </p>
      </Card>
    );
  }

  const data = todosQuery.data;
  if (!data) return null;

  const openItems = data.items.filter((t) => t.done_at === null);
  const doneItems = data.items.filter((t) => t.done_at !== null);
  const closedComp = data.last_closed_week_completion;
  const currComp = data.current_week_completion;

  return (
    <Card className="overflow-hidden p-0">
      {/* Header + 90% Target KPI Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-foreground">To-Dos</h2>
            <Badge variant="neutral" className="tabular-nums">
              {openItems.length} open
            </Badge>
            {data.overdue_count > 0 ? (
              <Badge variant="danger" className="tabular-nums">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                {data.overdue_count} overdue
              </Badge>
            ) : null}
          </div>
          <p className="mt-0.5 text-xs text-[#64748B]">
            7-day commitments. Weekly target is ≥ 90% completed by Sunday 23:59 company time.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {closedComp ? (
            <Badge variant={closedComp.meets_target ? "success" : "danger"} className="tabular-nums">
              Last week ({closedComp.week_start}): {closedComp.done}/{closedComp.due} (
              {closedComp.rate_percent}%) ·{" "}
              {closedComp.meets_target ? "90% Target Met" : "Below 90%"}
            </Badge>
          ) : null}
          {currComp ? (
            <Badge variant="neutral" className="tabular-nums">
              This week: {currComp.done}/{currComp.due} ({currComp.rate_percent}%)
            </Badge>
          ) : null}
        </div>
      </div>

      {errorMsg ? (
        <div
          role="alert"
          className="border-b border-[#FECACA] bg-[#FEF2F2] px-5 py-2.5 text-xs font-medium text-[#991B1B]"
        >
          {errorMsg}
        </div>
      ) : null}

      {/* Open To-Dos */}
      <ul className="divide-y divide-border">
        {openItems.length === 0 ? (
          <li className="px-5 py-8 text-center text-sm text-[#64748B]">
            All To-Dos are completed!
          </li>
        ) : (
          openItems.map((todo) => (
            <li
              key={todo.id}
              className="flex items-center justify-between gap-3 px-5 py-3.5 hover:bg-[#FAFAFC]"
            >
              <div className="flex min-w-0 items-start gap-3">
                <button
                  type="button"
                  disabled={readOnly || toggleMutation.isPending}
                  aria-label={`Mark "${todo.title}" done`}
                  onClick={() => toggleMutation.mutate({ todoId: todo.id, done: true })}
                  className={cn(
                    "mt-0.5 shrink-0 text-[#94A3B8] transition-colors",
                    !readOnly && "hover:text-primary",
                    readOnly && "cursor-not-allowed opacity-50",
                  )}
                >
                  <Circle className="h-4 w-4" aria-hidden="true" />
                </button>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{todo.title}</span>
                    {todo.is_overdue ? (
                      <Badge variant="danger">
                        <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                        Overdue
                      </Badge>
                    ) : null}
                  </div>
                  <p className="mt-0.5 text-xs text-[#64748B]">
                    {todo.owner_name} · Due <span className="tabular-nums">{todo.due_date}</span>
                  </p>
                </div>
              </div>
            </li>
          ))
        )}
      </ul>

      {/* Collapsible Completed To-Dos */}
      <div className="border-t border-border bg-[#F8FAFC] px-5 py-3">
        <button
          type="button"
          onClick={() => setShowCompleted((prev) => !prev)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#475569] hover:text-foreground"
        >
          {showCompleted ? (
            <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          Completed To-Dos ({doneItems.length})
        </button>

        {showCompleted ? (
          <ul className="mt-3 space-y-2">
            {doneItems.map((todo) => (
              <li
                key={todo.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border bg-white px-3 py-2 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    disabled={readOnly || toggleMutation.isPending}
                    aria-label={`Undo "${todo.title}"`}
                    onClick={() => toggleMutation.mutate({ todoId: todo.id, done: false })}
                    className={cn(
                      "shrink-0 text-[#059669]",
                      !readOnly && "hover:opacity-75",
                      readOnly && "cursor-not-allowed opacity-50",
                    )}
                  >
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                  <div>
                    <span className="font-medium text-foreground line-through opacity-75">
                      {todo.title}
                    </span>
                    <span className="ml-2 text-[#64748B]">
                      {todo.owner_name} · Due {todo.due_date}
                    </span>
                  </div>
                </div>
                <Badge variant="success">Done</Badge>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </Card>
  );
}
