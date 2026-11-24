import type {
  ActiveMeetingResponseDto,
  ApiErrorResponse,
  ApiResponse,
  HealthDto,
  IssueDto,
  IssueListDto,
  LoginResponseDto,
  MakeIssueFromMeasurableResponseDto,
  MeetingStateDto,
  MeetingSummarySnapshotDto,
  ResponseMeta,
  RockListDto,
  ScorecardResponseDto,
  TeamDto,
  TeamListDto,
  TodoDto,
  TodoListDto,
  UpsertScoreResponseDto,
  UserListDto,
  UserWithTeamsDto,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields?: Record<string, string>;
  readonly requestId?: string;

  constructor(params: {
    status: number;
    code: string;
    message: string;
    fields?: Record<string, string>;
    requestId?: string;
  }) {
    super(params.message);
    this.name = "ApiClientError";
    this.status = params.status;
    this.code = params.code;
    this.fields = params.fields;
    this.requestId = params.requestId;
  }
}

export interface ApiResult<T> {
  data: T;
  meta: ResponseMeta;
}

interface FetchOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  token?: string | null;
  body?: unknown;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
    cache: "no-store",
  });

  const requestIdHeader = res.headers.get("X-Request-Id") ?? undefined;
  let parsed: ApiResponse<T> | ApiErrorResponse | null = null;
  try {
    parsed = (await res.json()) as ApiResponse<T> | ApiErrorResponse;
  } catch {
    parsed = null;
  }

  if (!res.ok || !parsed || !parsed.success) {
    const errBody = parsed && !parsed.success ? parsed : null;
    throw new ApiClientError({
      status: res.status,
      code: errBody?.error.code ?? `HTTP_${res.status}`,
      message: errBody?.error.message ?? res.statusText ?? "Request failed",
      fields: errBody?.error.fields,
      requestId: errBody?.meta.request_id ?? requestIdHeader,
    });
  }

  return { data: parsed.data, meta: parsed.meta };
}

export function fetchHealth() {
  return apiFetch<HealthDto>("/api/health");
}

export function fetchSeededUsers() {
  return apiFetch<UserListDto>("/api/v1/auth/users");
}

export function loginAsUser(userId: string) {
  return apiFetch<LoginResponseDto>("/api/v1/auth/login", {
    method: "POST",
    body: { user_id: userId },
  });
}

export function fetchMe(token: string) {
  return apiFetch<UserWithTeamsDto>("/api/v1/me", { token });
}

export function fetchTeams(token: string) {
  return apiFetch<TeamListDto>("/api/v1/teams", { token });
}

export function fetchTeam(token: string, teamId: string) {
  return apiFetch<TeamDto>(`/api/v1/teams/${encodeURIComponent(teamId)}`, { token });
}

export function fetchEligibleOwners(token: string, teamId: string) {
  return apiFetch<UserListDto>(`/api/v1/teams/${encodeURIComponent(teamId)}/owners`, { token });
}

export function fetchScorecard(token: string, teamId: string) {
  return apiFetch<ScorecardResponseDto>(
    `/api/v1/teams/${encodeURIComponent(teamId)}/scorecard`,
    { token },
  );
}

export function upsertScore(
  token: string,
  teamId: string,
  measurableId: string,
  weekStart: string,
  value: number,
) {
  return apiFetch<UpsertScoreResponseDto>(
    `/api/v1/teams/${encodeURIComponent(teamId)}/measurables/${encodeURIComponent(measurableId)}/scores/${encodeURIComponent(weekStart)}`,
    {
      method: "PUT",
      token,
      body: { value },
    },
  );
}

export function makeIssueFromMeasurable(
  token: string,
  teamId: string,
  measurableId: string,
  weekStart: string,
) {
  return apiFetch<MakeIssueFromMeasurableResponseDto>(
    `/api/v1/teams/${encodeURIComponent(teamId)}/issues/from-measurable`,
    {
      method: "POST",
      token,
      body: { measurable_id: measurableId, week_start: weekStart },
    },
  );
}

export function fetchIssues(token: string, teamId: string) {
  return apiFetch<IssueListDto>(`/api/v1/teams/${encodeURIComponent(teamId)}/issues`, { token });
}

export function createIssue(
  token: string,
  teamId: string,
  payload: { title: string; owner_id?: string; priority?: number | null },
) {
  return apiFetch<IssueDto>(`/api/v1/teams/${encodeURIComponent(teamId)}/issues`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function updateIssuePriority(token: string, issueId: string, priority: number | null) {
  return apiFetch<IssueDto>(`/api/v1/issues/${encodeURIComponent(issueId)}`, {
    method: "PATCH",
    token,
    body: { priority },
  });
}

export function solveIssue(token: string, issueId: string, resolutionNote: string) {
  return apiFetch<IssueDto>(`/api/v1/issues/${encodeURIComponent(issueId)}/solve`, {
    method: "POST",
    token,
    body: { resolution_note: resolutionNote },
  });
}

export function createTodoFromIssue(
  token: string,
  issueId: string,
  payload: { title: string; owner_id: string; due_date?: string; meeting_id?: string },
) {
  return apiFetch<TodoDto>(`/api/v1/issues/${encodeURIComponent(issueId)}/todos`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function fetchTodos(token: string, teamId: string) {
  return apiFetch<TodoListDto>(`/api/v1/teams/${encodeURIComponent(teamId)}/todos`, { token });
}

export function toggleTodoDone(token: string, todoId: string, done: boolean) {
  return apiFetch<TodoDto>(`/api/v1/todos/${encodeURIComponent(todoId)}`, {
    method: "PATCH",
    token,
    body: { done },
  });
}

export function fetchRocks(token: string, teamId: string) {
  return apiFetch<RockListDto>(`/api/v1/teams/${encodeURIComponent(teamId)}/rocks`, { token });
}

export function fetchActiveMeeting(token: string, teamId: string) {
  return apiFetch<ActiveMeetingResponseDto>(
    `/api/v1/teams/${encodeURIComponent(teamId)}/meetings/active`,
    { token },
  );
}

export function startMeeting(token: string, teamId: string) {
  return apiFetch<MeetingStateDto>(`/api/v1/teams/${encodeURIComponent(teamId)}/meetings`, {
    method: "POST",
    token,
  });
}

export function fetchMeeting(token: string, meetingId: string) {
  return apiFetch<MeetingStateDto>(`/api/v1/meetings/${encodeURIComponent(meetingId)}`, { token });
}

export function joinMeeting(token: string, meetingId: string) {
  return apiFetch<MeetingStateDto>(`/api/v1/meetings/${encodeURIComponent(meetingId)}/join`, {
    method: "POST",
    token,
  });
}

export function advanceMeeting(token: string, meetingId: string) {
  return apiFetch<MeetingStateDto>(`/api/v1/meetings/${encodeURIComponent(meetingId)}/advance`, {
    method: "POST",
    token,
  });
}

export function endMeeting(token: string, meetingId: string) {
  return apiFetch<MeetingStateDto>(`/api/v1/meetings/${encodeURIComponent(meetingId)}/end`, {
    method: "POST",
    token,
  });
}

export function submitMeetingRating(token: string, meetingId: string, rating: number) {
  return apiFetch<MeetingStateDto>(`/api/v1/meetings/${encodeURIComponent(meetingId)}/rating`, {
    method: "PUT",
    token,
    body: { rating },
  });
}

export function fetchMeetingSummary(token: string, meetingId: string) {
  return apiFetch<MeetingSummarySnapshotDto>(
    `/api/v1/meetings/${encodeURIComponent(meetingId)}/summary`,
    { token },
  );
}
