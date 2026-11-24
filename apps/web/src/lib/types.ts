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
