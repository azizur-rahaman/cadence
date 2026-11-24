"use client";

import { useState, type ComponentType } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ChartNoAxesCombined,
  Clock,
  Eye,
  ListChecks,
  Target,
} from "lucide-react";
import { AccessErrorView } from "@/components/layout/AccessErrorView";
import { IssuesSection } from "@/components/sections/IssuesSection";
import { RocksSection } from "@/components/sections/RocksSection";
import { ScorecardSection } from "@/components/sections/ScorecardSection";
import { TodosSection } from "@/components/sections/TodosSection";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ApiClientError, fetchHealth, fetchTeam } from "@/lib/api";
import { cn, formatRoleLabel } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

type SectionTab = "scorecard" | "issues" | "todos" | "rocks";

const SECTION_TABS: Array<{
  id: SectionTab;
  label: string;
  icon: ComponentType<{ className?: string }>;
}> = [
  { id: "scorecard", label: "Scorecard", icon: ChartNoAxesCombined },
  { id: "issues", label: "Issues", icon: AlertCircle },
  { id: "todos", label: "To-Dos", icon: ListChecks },
  { id: "rocks", label: "Rocks", icon: Target },
];

export default function TeamPage() {
  const {
    token,
    user,
    teams,
    activeTeamId,
    isLoadingSession,
    sessionError,
    setActiveTeamId,
  } = useSession();

  const [activeTab, setActiveTab] = useState<SectionTab>("scorecard");

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await fetchHealth()).data,
  });

  const teamQuery = useQuery({
    queryKey: ["team", activeTeamId, user?.id],
    enabled: Boolean(token && activeTeamId),
    retry: false,
    queryFn: async () => (await fetchTeam(token!, activeTeamId!)).data,
  });

  if (isLoadingSession) {
    return (
      <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-8">
        <Card className="animate-pulse">
          <div className="h-6 w-48 rounded bg-surface-secondary" />
          <div className="mt-3 h-4 w-80 rounded bg-surface-secondary" />
        </Card>
      </main>
    );
  }

  if (sessionError) {
    return (
      <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-8">
        <AccessErrorView status={500} message={sessionError} />
      </main>
    );
  }

  if (teamQuery.isError) {
    const err = teamQuery.error;
    const isApiErr = err instanceof ApiClientError;
    return (
      <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-8">
        <AccessErrorView
          status={isApiErr ? err.status : 500}
          code={isApiErr ? err.code : undefined}
          message={err.message}
          requestId={isApiErr ? err.requestId : undefined}
          onReset={teams[0] ? () => setActiveTeamId(teams[0].id) : undefined}
          resetLabel={teams[0] ? `Switch to ${teams[0].name}` : undefined}
        />
      </main>
    );
  }

  const isObserver = user?.role === "observer";

  return (
    <main className="mx-auto max-w-[1440px] px-4 py-8 sm:px-8">
      {/* Team Context Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-xs font-medium text-[#64748B]">Measure. Commit. Resolve.</p>
          <h1 className="mt-0.5 text-2xl font-semibold tracking-tight text-foreground">
            {teamQuery.data?.name ?? "Team Workspace"}
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-[#64748B]">
          {healthQuery.data ? (
            <Badge variant="neutral" className="tabular-nums">
              <Clock className="h-3.5 w-3.5" aria-hidden="true" />
              Server clock: {healthQuery.data.now}
            </Badge>
          ) : null}
          {user ? (
            <Badge variant="info">
              Signed in as {user.name} ({formatRoleLabel(user.role)})
            </Badge>
          ) : null}
        </div>
      </div>

      {/* Observer Read-Only Banner */}
      {isObserver ? (
        <div
          role="status"
          className="mt-5 flex items-center gap-2.5 rounded-lg border border-[#FDE68A] bg-warning-bg px-4 py-3 text-sm text-[#92400E]"
        >
          <Eye className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>
            <strong>Read-only Observer mode:</strong> You can view this team&apos;s data and join
            live meetings, but editing scores, managing Issues/To-Dos, facilitating, and rating are
            disabled (and enforced server-side).
          </span>
        </div>
      ) : null}

      {/* Team Page Section Tabs (Strictly the 4 In-Scope Sections) */}
      <nav aria-label="Team workspace sections" className="mt-6 border-b border-border">
        <div className="flex gap-6 overflow-x-auto">
          {SECTION_TABS.map((tab) => {
            const Icon = tab.icon;
            const active = tab.id === activeTab;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "inline-flex shrink-0 items-center gap-2 border-b-2 pb-3 pt-1 text-sm font-medium transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                  active
                    ? "border-primary text-primary"
                    : "border-transparent text-[#475569] hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Active Section Workspace */}
      <section className="mt-6">
        {activeTab === "scorecard" && activeTeamId ? (
          <ScorecardSection teamId={activeTeamId} readOnly={isObserver} />
        ) : activeTab === "issues" && activeTeamId ? (
          <IssuesSection teamId={activeTeamId} readOnly={isObserver} />
        ) : activeTab === "todos" && activeTeamId ? (
          <TodosSection teamId={activeTeamId} readOnly={isObserver} />
        ) : activeTab === "rocks" && activeTeamId ? (
          <RocksSection teamId={activeTeamId} />
        ) : null}
      </section>
    </main>
  );
}
