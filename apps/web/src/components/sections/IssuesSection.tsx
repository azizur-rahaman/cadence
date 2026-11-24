"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Link2,
  ListPlus,
  Plus,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  ApiClientError,
  createIssue,
  createTodoFromIssue,
  fetchEligibleOwners,
  fetchIssues,
  solveIssue,
  updateIssuePriority,
} from "@/lib/api";
import type { IssueDto } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

export interface IssuesSectionProps {
  teamId: string;
  meetingId?: string;
  readOnly?: boolean;
  onMutated?: () => void;
}

export function IssuesSection({
  teamId,
  meetingId,
  readOnly = false,
  onMutated,
}: IssuesSectionProps) {
  const { token, user } = useSession();
  const queryClient = useQueryClient();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newPriority, setNewPriority] = useState<string>("");

  const [solvingId, setSolvingId] = useState<string | null>(null);
  const [resolutionNote, setResolutionNote] = useState("");

  const [todoIssueId, setTodoIssueId] = useState<string | null>(null);
  const [todoTitle, setTodoTitle] = useState("");
  const [todoOwnerId, setTodoOwnerId] = useState("");
  const [todoDueDate, setTodoDueDate] = useState("");

  const [showSolved, setShowSolved] = useState(false);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error";
    text: string;
  } | null>(null);

  const issuesQuery = useQuery({
    queryKey: ["issues", teamId, user?.id],
    enabled: Boolean(token && teamId),
    queryFn: async () => (await fetchIssues(token!, teamId)).data,
  });

  const ownersQuery = useQuery({
    queryKey: ["team-owners", teamId, user?.id],
    enabled: Boolean(token && teamId),
    queryFn: async () => (await fetchEligibleOwners(token!, teamId)).data.items,
  });

  const createIssueMutation = useMutation({
    mutationFn: async () =>
      (
        await createIssue(token!, teamId, {
          title: newTitle.trim(),
          priority: newPriority ? Number(newPriority) : null,
        })
      ).data,
    onSuccess: (created) => {
      setNewTitle("");
      setNewPriority("");
      setShowAddForm(false);
      setFeedback({ tone: "success", text: `Added Issue: "${created.title}"` });
      void queryClient.invalidateQueries({ queryKey: ["issues", teamId] });
      onMutated?.();
    },
    onError: (err) => {
      setFeedback({
        tone: "error",
        text: err instanceof ApiClientError ? err.message : "Failed to create Issue.",
      });
    },
  });

  const priorityMutation = useMutation({
    mutationFn: async (vars: { issueId: string; priority: number | null }) =>
      (await updateIssuePriority(token!, vars.issueId, vars.priority)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["issues", teamId] });
      onMutated?.();
    },
    onError: (err) => {
      setFeedback({
        tone: "error",
        text: err instanceof ApiClientError ? err.message : "Failed to update priority.",
      });
    },
  });

  const solveMutation = useMutation({
    mutationFn: async (vars: { issueId: string; note: string }) =>
      (await solveIssue(token!, vars.issueId, vars.note)).data,
    onSuccess: (solved) => {
      setSolvingId(null);
      setResolutionNote("");
      setFeedback({ tone: "success", text: `Solved Issue: "${solved.title}"` });
      void queryClient.invalidateQueries({ queryKey: ["issues", teamId] });
      void queryClient.invalidateQueries({ queryKey: ["scorecard", teamId] });
      onMutated?.();
    },
    onError: (err) => {
      setFeedback({
        tone: "error",
        text: err instanceof ApiClientError ? err.message : "Failed to solve Issue.",
      });
    },
  });

  const createTodoMutation = useMutation({
    mutationFn: async (vars: {
      issueId: string;
      title: string;
      ownerId: string;
      dueDate?: string;
    }) =>
      (
        await createTodoFromIssue(token!, vars.issueId, {
          title: vars.title,
          owner_id: vars.ownerId,
          due_date: vars.dueDate || undefined,
          meeting_id: meetingId,
        })
      ).data,
    onSuccess: (created) => {
      setTodoIssueId(null);
      setTodoTitle("");
      setTodoDueDate("");
      setFeedback({
        tone: "success",
        text: `Added To-Do "${created.title}" for ${created.owner_name} (due ${created.due_date}).`,
      });
      void queryClient.invalidateQueries({ queryKey: ["todos", teamId] });
      onMutated?.();
    },
    onError: (err) => {
      setFeedback({
        tone: "error",
        text: err instanceof ApiClientError ? err.message : "Failed to add To-Do.",
      });
    },
  });

  function openTodoForm(issue: IssueDto) {
    setSolvingId(null);
    setTodoIssueId(issue.id);
    setTodoTitle("");
    setTodoDueDate("");
    const owners = ownersQuery.data ?? [];
    const defaultOwner =
      owners.find((o) => o.id === issue.owner_id)?.id ?? owners[0]?.id ?? "";
    setTodoOwnerId(defaultOwner);
  }

  function openSolveForm(issueId: string) {
    setTodoIssueId(null);
    setSolvingId(issueId);
    setResolutionNote("");
  }

  if (issuesQuery.isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-5 w-36 rounded bg-surface-secondary" />
        <div className="mt-4 h-40 w-full rounded bg-surface-secondary" />
      </Card>
    );
  }

  if (issuesQuery.isError) {
    return (
      <Card className="border-[#FECACA] bg-[#FEF2F2]">
        <p className="text-sm font-medium text-[#991B1B]">
          Unable to load Issues: {issuesQuery.error.message}
        </p>
      </Card>
    );
  }

  const data = issuesQuery.data;
  if (!data) return null;

  const owners = ownersQuery.data ?? [];

  return (
    <Card className="overflow-hidden p-0">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-foreground">Issues (IDS)</h2>
            <Badge variant="neutral" className="tabular-nums">
              {data.unsolved.length} open
            </Badge>
          </div>
          <p className="mt-0.5 text-xs text-[#64748B]">
            Ordered server-side by priority (5 → 1, unranked last) then oldest first.
          </p>
        </div>
        {!readOnly ? (
          <Button
            size="sm"
            variant={showAddForm ? "secondary" : "primary"}
            onClick={() => setShowAddForm((prev) => !prev)}
          >
            <Plus className="h-3.5 w-3.5" aria-hidden="true" />
            {showAddForm ? "Cancel" : "Add Issue"}
          </Button>
        ) : null}
      </div>

      {/* Feedback Banner */}
      {feedback ? (
        <div
          role="status"
          className={cn(
            "flex items-center justify-between border-b px-5 py-2.5 text-xs font-medium",
            feedback.tone === "success" && "border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46]",
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

      {/* Add Issue Form */}
      {showAddForm && !readOnly ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!newTitle.trim()) return;
            createIssueMutation.mutate();
          }}
          className="flex flex-wrap items-end gap-3 border-b border-border bg-[#F8FAFC] px-5 py-4"
        >
          <div className="min-w-[240px] flex-1">
            <label className="block text-xs font-medium text-[#475569]" htmlFor="new-issue-title">
              Issue title
            </label>
            <input
              id="new-issue-title"
              type="text"
              required
              placeholder="e.g., Enterprise onboarding taking 3 weeks"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="mt-1 w-full rounded-md border border-border-strong bg-white px-3 py-1.5 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="w-36">
            <label
              className="block text-xs font-medium text-[#475569]"
              htmlFor="new-issue-priority"
            >
              Priority
            </label>
            <select
              id="new-issue-priority"
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value)}
              className="mt-1 w-full rounded-md border border-border-strong bg-white px-2.5 py-1.5 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">Unranked</option>
              <option value="5">P5 (Highest)</option>
              <option value="4">P4</option>
              <option value="3">P3</option>
              <option value="2">P2</option>
              <option value="1">P1 (Lowest)</option>
            </select>
          </div>
          <Button type="submit" size="sm" disabled={createIssueMutation.isPending}>
            {createIssueMutation.isPending ? "Adding..." : "Save Issue"}
          </Button>
        </form>
      ) : null}

      {/* Unsolved Issues List */}
      <ul className="divide-y divide-border">
        {data.unsolved.length === 0 ? (
          <li className="px-5 py-8 text-center text-sm text-[#64748B]">
            No unsolved Issues for this team.
          </li>
        ) : (
          data.unsolved.map((issue) => (
            <li key={issue.id} className="px-5 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 text-[#D97706]" aria-hidden="true" />
                    <span className="text-sm font-medium text-foreground">{issue.title}</span>
                    {issue.source ? (
                      <Badge variant="info" className="text-[11px]">
                        <Link2 className="h-3 w-3" aria-hidden="true" />
                        Scorecard · {issue.source.week_start}
                      </Badge>
                    ) : null}
                  </div>
                  <p className="mt-1 text-xs text-[#64748B]">Owner: {issue.owner_name}</p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {/* Priority Selector */}
                  {readOnly ? (
                    <Badge variant={issue.priority ? "warning" : "neutral"}>
                      {issue.priority ? `P${issue.priority}` : "Unranked"}
                    </Badge>
                  ) : (
                    <select
                      aria-label={`Priority for ${issue.title}`}
                      value={issue.priority ?? ""}
                      disabled={priorityMutation.isPending}
                      onChange={(e) =>
                        priorityMutation.mutate({
                          issueId: issue.id,
                          priority: e.target.value ? Number(e.target.value) : null,
                        })
                      }
                      className="rounded-md border border-border-strong bg-white px-2 py-1 text-xs font-medium text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      <option value="">Unranked</option>
                      <option value="5">P5</option>
                      <option value="4">P4</option>
                      <option value="3">P3</option>
                      <option value="2">P2</option>
                      <option value="1">P1</option>
                    </select>
                  )}

                  {!readOnly ? (
                    <>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => openTodoForm(issue)}
                      >
                        <ListPlus className="h-3.5 w-3.5" aria-hidden="true" />
                        Add To-Do
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => openSolveForm(issue.id)}
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                        Solve
                      </Button>
                    </>
                  ) : null}
                </div>
              </div>

              {/* Inline Add To-Do Form */}
              {todoIssueId === issue.id && !readOnly ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!todoTitle.trim() || !todoOwnerId) return;
                    createTodoMutation.mutate({
                      issueId: issue.id,
                      title: todoTitle.trim(),
                      ownerId: todoOwnerId,
                      dueDate: todoDueDate || undefined,
                    });
                  }}
                  className="mt-3 flex flex-wrap items-end gap-3 rounded-lg border border-border bg-[#F8FAFC] p-3"
                >
                  <div className="min-w-[200px] flex-1">
                    <label className="block text-xs font-medium text-[#475569]">
                      To-Do action item
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Specific 7-day action..."
                      value={todoTitle}
                      onChange={(e) => setTodoTitle(e.target.value)}
                      className="mt-1 w-full rounded-md border border-border-strong bg-white px-2.5 py-1.5 text-xs text-foreground"
                    />
                  </div>
                  <div className="w-44">
                    <label className="block text-xs font-medium text-[#475569]">Owner</label>
                    <select
                      value={todoOwnerId}
                      onChange={(e) => setTodoOwnerId(e.target.value)}
                      className="mt-1 w-full rounded-md border border-border-strong bg-white px-2.5 py-1.5 text-xs text-foreground"
                    >
                      {owners.map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="w-36">
                    <label className="block text-xs font-medium text-[#475569]">
                      Due (default +7d)
                    </label>
                    <input
                      type="date"
                      value={todoDueDate}
                      onChange={(e) => setTodoDueDate(e.target.value)}
                      className="mt-1 w-full rounded-md border border-border-strong bg-white px-2 py-1.5 text-xs text-foreground"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" size="sm" disabled={createTodoMutation.isPending}>
                      {createTodoMutation.isPending ? "Saving..." : "Create To-Do"}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setTodoIssueId(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              ) : null}

              {/* Inline Solve Issue Form */}
              {solvingId === issue.id && !readOnly ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!resolutionNote.trim()) return;
                    solveMutation.mutate({ issueId: issue.id, note: resolutionNote.trim() });
                  }}
                  className="mt-3 flex flex-wrap items-end gap-3 rounded-lg border border-[#A7F3D0] bg-[#ECFDF5]/60 p-3"
                >
                  <div className="min-w-[240px] flex-1">
                    <label className="block text-xs font-medium text-[#065F46]">
                      Resolution note (required)
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Summarize how this Issue was resolved..."
                      value={resolutionNote}
                      onChange={(e) => setResolutionNote(e.target.value)}
                      className="mt-1 w-full rounded-md border border-border-strong bg-white px-2.5 py-1.5 text-xs text-foreground"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" size="sm" disabled={solveMutation.isPending}>
                      {solveMutation.isPending ? "Solving..." : "Confirm Solved"}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setSolvingId(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              ) : null}
            </li>
          ))
        )}
      </ul>

      {/* Collapsible Solved Issues */}
      <div className="border-t border-border bg-[#F8FAFC] px-5 py-3">
        <button
          type="button"
          onClick={() => setShowSolved((prev) => !prev)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#475569] hover:text-foreground"
        >
          {showSolved ? (
            <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          Solved Issues ({data.solved.length})
        </button>

        {showSolved ? (
          <ul className="mt-3 space-y-2">
            {data.solved.length === 0 ? (
              <li className="text-xs text-[#64748B]">No solved Issues yet.</li>
            ) : (
              data.solved.map((issue) => (
                <li
                  key={issue.id}
                  className="rounded-md border border-border bg-white px-3 py-2.5 text-xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-foreground line-through opacity-80">
                      {issue.title}
                    </span>
                    <Badge variant="success">Solved</Badge>
                  </div>
                  {issue.resolution_note ? (
                    <p className="mt-1 text-[#475569]">Resolution: {issue.resolution_note}</p>
                  ) : null}
                </li>
              ))
            )}
          </ul>
        ) : null}
      </div>
    </Card>
  );
}
