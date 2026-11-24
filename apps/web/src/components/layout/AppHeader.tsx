"use client";

import Link from "next/link";
import { UserCircle, Users, Video } from "lucide-react";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { RoleType } from "@/lib/types";
import { formatRoleLabel } from "@/lib/utils";
import { useSession } from "@/providers/AppProviders";

function roleBadgeVariant(role: RoleType): BadgeVariant {
  if (role === "admin") return "info";
  if (role === "observer") return "warning";
  return "neutral";
}

export function AppHeader() {
  const {
    user,
    seededUsers,
    teams,
    activeTeamId,
    isLoadingSession,
    isSwitchingUser,
    switchUser,
    setActiveTeamId,
  } = useSession();

  const isObserver = user?.role === "observer";

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-border bg-surface">
      <div className="mx-auto flex h-full max-w-[1440px] items-center justify-between gap-4 px-4 sm:px-8">
        {/* Left: Brand + Team Switcher */}
        <div className="flex min-w-0 items-center gap-4">
          <Link
            href="/"
            className="flex shrink-0 items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:rounded-md"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-sm font-semibold text-white">
              L10
            </span>
            <div className="hidden sm:block">
              <span className="text-sm font-semibold tracking-tight text-foreground">Cadence</span>
              <span className="ml-1.5 text-xs text-[#64748B]">Level 10</span>
            </div>
          </Link>

          <div className="h-5 w-px bg-border" aria-hidden="true" />

          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 shrink-0 text-[#64748B]" aria-hidden="true" />
            <label htmlFor="team-switcher" className="sr-only">
              Select Team
            </label>
            <select
              id="team-switcher"
              aria-label="Team Switcher"
              disabled={isLoadingSession || teams.length === 0}
              value={teams.some((t) => t.id === activeTeamId) ? (activeTeamId ?? "") : ""}
              onChange={(e) => setActiveTeamId(e.target.value)}
              className="h-9 rounded-md border border-border bg-surface px-3 text-sm font-medium text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
            >
              {!teams.some((t) => t.id === activeTeamId) && activeTeamId ? (
                <option value="" disabled>
                  Unauthorized team ({activeTeamId})
                </option>
              ) : null}
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Right: Live Meeting CTA + Seeded User Switcher */}
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            disabled={isLoadingSession || isObserver || !activeTeamId}
            title={
              isObserver
                ? "Observers cannot start a Level 10 Meeting (join when active)"
                : "Live Level 10 Meeting launches in Phase 4"
            }
            className="hidden md:inline-flex"
          >
            <Video className="h-4 w-4" aria-hidden="true" />
            Start Level 10
          </Button>

          <div className="flex items-center gap-2">
            <UserCircle className="h-4 w-4 shrink-0 text-[#64748B]" aria-hidden="true" />
            <label htmlFor="user-switcher" className="sr-only">
              Switch Seeded User
            </label>
            <select
              id="user-switcher"
              aria-label="User Switcher"
              disabled={isLoadingSession || isSwitchingUser || seededUsers.length === 0}
              value={user?.id ?? ""}
              onChange={(e) => void switchUser(e.target.value)}
              className="h-9 max-w-[200px] rounded-md border border-border bg-surface px-2.5 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
            >
              {seededUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.id})
                </option>
              ))}
            </select>
            {user ? (
              <Badge variant={roleBadgeVariant(user.role)} className="hidden sm:inline-flex">
                {formatRoleLabel(user.role)}
              </Badge>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
