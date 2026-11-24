"""Issues Data Transfer Objects (DTOs)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
