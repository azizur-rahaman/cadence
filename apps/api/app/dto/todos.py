"""To-Dos Data Transfer Objects (DTOs)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class TodoDto(BaseModel):
    id: str
    team_id: str
    title: str
    owner_id: str
    owner_name: str
    due_date: date
    done_at: datetime | None
    is_overdue: bool
    source_issue_id: str | None
    created_at: datetime
    meeting_id: str | None


class TodoWeekCompletionDto(BaseModel):
    week_start: str
    due: int
    done: int
    rate_percent: int
    meets_target: bool


class TodoListDto(BaseModel):
    team_id: str
    today: str
    current_week_start: str
    last_closed_week_start: str
    overdue_count: int
    current_week_completion: TodoWeekCompletionDto | None
    last_closed_week_completion: TodoWeekCompletionDto | None
    weekly_completion: dict[str, TodoWeekCompletionDto | None]
    items: list[TodoDto]


class CreateTodoRequestDto(BaseModel):
    title: str = Field(..., min_length=1)
    owner_id: str = Field(..., min_length=1)
    due_date: date | None = None
    meeting_id: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title must not be empty.")
        return stripped


class ToggleTodoDoneRequestDto(BaseModel):
    done: bool
