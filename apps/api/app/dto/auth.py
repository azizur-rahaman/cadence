"""Authentication, user profile, team, and system health DTOs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RoleType = Literal["admin", "team_member", "observer"]


class HealthDto(BaseModel):
    status: Literal["ok"] = "ok"
    now: str
    app_now: str


class TeamDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class TeamListDto(BaseModel):
    items: list[TeamDto]


class UserDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: RoleType


class UserListDto(BaseModel):
    items: list[UserDto]


class UserWithTeamsDto(UserDto):
    teams: list[TeamDto]


class LoginRequestDto(BaseModel):
    user_id: str | None = Field(default=None, description="Seeded user ID (e.g., u1, u2)")
    email: str | None = Field(default=None, description="Seeded user email (case-insensitive)")

    @model_validator(mode="after")
    def require_identifier(self) -> LoginRequestDto:
        uid = (self.user_id or "").strip()
        mail = (self.email or "").strip()
        if not uid and not mail:
            raise ValueError("Provide either 'user_id' or 'email'.")
        self.user_id = uid or None
        self.email = mail or None
        return self


class LoginResponseDto(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserWithTeamsDto
