"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { fetchMe, fetchSeededUsers, loginAsUser } from "@/lib/api";
import type { TeamDto, UserDto, UserWithTeamsDto } from "@/lib/types";

const TOKEN_STORAGE_KEY = "cadence_access_token";
const TEAM_STORAGE_KEY = "cadence_active_team_id";
const DEFAULT_USER_ID = "u2";

interface SessionContextValue {
  token: string | null;
  user: UserWithTeamsDto | null;
  seededUsers: UserDto[];
  teams: TeamDto[];
  activeTeamId: string | null;
  isLoadingSession: boolean;
  isSwitchingUser: boolean;
  sessionError: string | null;
  switchUser: (userId: string) => Promise<void>;
  setActiveTeamId: (teamId: string) => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

function SessionProviderInner({
  children,
  queryClient,
}: {
  children: ReactNode;
  queryClient: QueryClient;
}) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserWithTeamsDto | null>(null);
  const [activeTeamId, setActiveTeamIdState] = useState<string | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isSwitchingUser, setIsSwitchingUser] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  const seededUsersQuery = useQuery({
    queryKey: ["seeded-users"],
    queryFn: async () => (await fetchSeededUsers()).data.items,
  });

  const selectTeamForUser = useCallback((u: UserWithTeamsDto, preferredTeamId?: string | null) => {
    const urlTeam =
      typeof window !== "undefined"
        ? new URLSearchParams(window.location.search).get("team")
        : null;
    if (urlTeam) {
      setActiveTeamIdState(urlTeam);
      return;
    }

    const storedTeam =
      preferredTeamId ??
      (typeof window !== "undefined" ? sessionStorage.getItem(TEAM_STORAGE_KEY) : null);

    if (storedTeam && u.teams.some((t) => t.id === storedTeam)) {
      setActiveTeamIdState(storedTeam);
      return;
    }

    const fallback = u.teams[0]?.id ?? null;
    setActiveTeamIdState(fallback);
    if (fallback && typeof window !== "undefined") {
      sessionStorage.setItem(TEAM_STORAGE_KEY, fallback);
    }
  }, []);

  const performLogin = useCallback(
    async (userId: string) => {
      const { data } = await loginAsUser(userId);
      setToken(data.access_token);
      setUser(data.user);
      if (typeof window !== "undefined") {
        sessionStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
      }
      selectTeamForUser(data.user);
      await queryClient.invalidateQueries({
        predicate: (q) => q.queryKey[0] !== "seeded-users",
      });
    },
    [queryClient, selectTeamForUser],
  );

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      setIsLoadingSession(true);
      setSessionError(null);
      try {
        const storedToken =
          typeof window !== "undefined" ? sessionStorage.getItem(TOKEN_STORAGE_KEY) : null;
        if (storedToken) {
          try {
            const { data: me } = await fetchMe(storedToken);
            if (!cancelled) {
              setToken(storedToken);
              setUser(me);
              selectTeamForUser(me);
            }
            return;
          } catch {
            if (typeof window !== "undefined") {
              sessionStorage.removeItem(TOKEN_STORAGE_KEY);
            }
          }
        }
        await performLogin(DEFAULT_USER_ID);
      } catch (err) {
        if (!cancelled) {
          setSessionError(err instanceof Error ? err.message : "Failed to initialize session.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSession(false);
        }
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [performLogin, selectTeamForUser]);

  const switchUser = useCallback(
    async (userId: string) => {
      setIsSwitchingUser(true);
      setSessionError(null);
      try {
        await performLogin(userId);
      } catch (err) {
        setSessionError(err instanceof Error ? err.message : "Failed to switch user.");
      } finally {
        setIsSwitchingUser(false);
      }
    },
    [performLogin],
  );

  const setActiveTeamId = useCallback((teamId: string) => {
    setActiveTeamIdState(teamId);
    if (typeof window !== "undefined") {
      sessionStorage.setItem(TEAM_STORAGE_KEY, teamId);
      const url = new URL(window.location.href);
      if (url.searchParams.has("team")) {
        url.searchParams.set("team", teamId);
        window.history.replaceState({}, "", url.toString());
      }
    }
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      token,
      user,
      seededUsers: seededUsersQuery.data ?? [],
      teams: user?.teams ?? [],
      activeTeamId,
      isLoadingSession,
      isSwitchingUser,
      sessionError,
      switchUser,
      setActiveTeamId,
    }),
    [
      token,
      user,
      seededUsersQuery.data,
      activeTeamId,
      isLoadingSession,
      isSwitchingUser,
      sessionError,
      switchUser,
      setActiveTeamId,
    ],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 10_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <SessionProviderInner queryClient={queryClient}>{children}</SessionProviderInner>
    </QueryClientProvider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession must be used inside <AppProviders>");
  }
  return ctx;
}
