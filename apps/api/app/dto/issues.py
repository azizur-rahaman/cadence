"""Issues Data Transfer Objects (DTOs)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IssueSourceDto(BaseModel):
    measurable_id: str
    week_start: date


class IssueDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    team_id: str
    title: str
    owner_id: str
    owner_name: str
    priority: int | None
    created_at: datetime
    solved_at: datetime | None
    resolution_note: str | None
    source: IssueSourceDto | None


class IssueListDto(BaseModel):
    unsolved: list[IssueDto]
    solved: list[IssueDto]


class CreateIssueRequestDto(BaseModel):
    title: str = Field(..., min_length=1)
    owner_id: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title must not be empty.")
        return stripped


class UpdateIssuePriorityRequestDto(BaseModel):
    priority: int | None = Field(..., ge=1, le=5)


class SolveIssueRequestDto(BaseModel):
    resolution_note: str = Field(..., min_length=1)

    @field_validator("resolution_note")
    @classmethod
    def note_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Resolution note is required when solving an issue.")
        return stripped
