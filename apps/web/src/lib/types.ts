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

export interface IssueListDto {
  unsolved: IssueDto[];
  solved: IssueDto[];
}

export interface TodoDto {
  id: string;
  team_id: string;
  title: string;
  owner_id: string;
  owner_name: string;
  due_date: string;
  done_at: string | null;
  is_overdue: boolean;
  source_issue_id: string | null;
  created_at: string;
  meeting_id: string | null;
}

export interface TodoWeekCompletionDto {
  week_start: string;
  due: number;
  done: number;
  rate_percent: number;
  meets_target: boolean;
}

export interface TodoListDto {
  team_id: string;
  today: string;
  current_week_start: string;
  last_closed_week_start: string;
  overdue_count: number;
  current_week_completion: TodoWeekCompletionDto | null;
  last_closed_week_completion: TodoWeekCompletionDto | null;
  weekly_completion: Record<string, TodoWeekCompletionDto | null>;
  items: TodoDto[];
}

export type RockStatus = "on_track" | "off_track" | "complete";

export interface MilestoneDto {
  id: string;
  title: string;
  due_date: string;
  done: boolean;
  is_past_due: boolean;
}

export interface RockDto {
  id: string;
  team_id: string;
  title: string;
  owner_id: string;
  owner_name: string;
  quarter: string;
  status: RockStatus;
  progress_percent: number;
  milestones: MilestoneDto[];
}

export interface RockListDto {
  team_id: string;
  quarter: string;
  today: string;
  items: RockDto[];
}

export type MeetingSection = "scorecard" | "ids" | "conclude" | "ended";

export interface MeetingAttendeeDto {
  user_id: string;
  name: string;
  role: RoleType;
  joined_at: string;
}

export interface MeetingRatingDto {
  user_id: string;
  name: string;
  rating: number;
  updated_at: string;
}

export interface MeetingTimerDto {
  allotted_seconds: number;
  elapsed_seconds: number;
  remaining_seconds: number;
  over_time: boolean;
}

export interface MeetingSummarySnapshotDto {
  scorecard_week: string;
  measurable_status: Record<string, MeasurableStatus>;
  issues_solved: string[];
  todos_created: string[];
  attendee_ids: string[];
  rating: number | null;
}

export interface MeetingStateDto {
  id: string;
  team_id: string;
  facilitator_id: string;
  facilitator_name: string;
  section: MeetingSection;
  section_started_at: string;
  started_at: string;
  ended_at: string | null;
  scorecard_week: string;
  server_now: string;
  timer: MeetingTimerDto;
  attendees: MeetingAttendeeDto[];
  ratings: MeetingRatingDto[];
  average_rating: number | null;
  todos_created: TodoDto[];
  summary: MeetingSummarySnapshotDto | null;
}

export interface ActiveMeetingResponseDto {
  meeting: MeetingStateDto | null;
}
