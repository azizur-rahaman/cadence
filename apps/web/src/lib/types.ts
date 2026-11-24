export type RoleType = "admin" | "team_member" | "observer";

export interface ResponseMeta {
  request_id: string;
  timestamp: string;
}

export interface ApiResponse<T> {
  success: true;
  data: T;
  meta: ResponseMeta;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  fields?: Record<string, string>;
}

export interface ApiErrorResponse {
  success: false;
  error: ApiErrorDetail;
  meta: ResponseMeta;
}

export interface HealthDto {
  status: "ok";
  now: string;
  app_now: string;
}

export interface TeamDto {
  id: string;
  name: string;
}

export interface TeamListDto {
  items: TeamDto[];
}

export interface UserDto {
  id: string;
  name: string;
  email: string;
  role: RoleType;
}

export interface UserListDto {
  items: UserDto[];
}

export interface UserWithTeamsDto extends UserDto {
  teams: TeamDto[];
}

export interface LoginResponseDto {
  access_token: string;
  token_type: "bearer";
  user: UserWithTeamsDto;
}

export type GoalType = "at_least" | "at_most" | "between" | "exactly";
export type MeasurableStatus = "on_track" | "off_track" | "pending";

export interface IssueSourceDto {
  measurable_id: string;
  week_start: string;
}

export interface IssueDto {
  id: string;
  team_id: string;
  title: string;
  owner_id: string;
  owner_name: string;
  priority: number | null;
  created_at: string;
  solved_at: string | null;
  resolution_note: string | null;
  source: IssueSourceDto | null;
}

export interface MeasurableGoalDto {
  type: GoalType;
  value: number | null;
  min: number | null;
  max: number | null;
  label: string;
}

export interface ScoreCellDto {
  week_start: string;
  value: number | null;
  status: MeasurableStatus;
  unsolved_issue_id: string | null;
}

export interface MeasurableRowDto {
  id: string;
  team_id: string;
  name: string;
  owner_id: string;
  owner_name: string;
  unit: string;
  goal: MeasurableGoalDto;
  cells: ScoreCellDto[];
}

export interface ScorecardResponseDto {
  team_id: string;
  current_week_start: string;
  last_closed_week_start: string;
  weeks: string[];
  measurables: MeasurableRowDto[];
}

export interface UpsertScoreResponseDto {
  measurable_id: string;
  week_start: string;
  value: number;
  status: MeasurableStatus;
  unsolved_issue_id: string | null;
}

export interface MakeIssueFromMeasurableResponseDto {
  created: boolean;
  issue: IssueDto;
}
