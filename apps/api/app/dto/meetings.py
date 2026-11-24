"""Level 10 Meeting lifecycle, timer, rating, and summary DTOs."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.dto.auth import RoleType
from app.dto.scorecard import MeasurableStatusDto
from app.dto.todos import TodoDto

MeetingSectionDto = Literal["scorecard", "ids", "conclude", "ended"]


class MeetingAttendeeDto(BaseModel):
    user_id: str
    name: str
    role: RoleType
    joined_at: datetime


class MeetingRatingDto(BaseModel):
    user_id: str
    name: str
    rating: int
    updated_at: datetime


class MeetingTimerDto(BaseModel):
    allotted_seconds: int
    elapsed_seconds: int
    remaining_seconds: int
    over_time: bool


class MeetingSummarySnapshotDto(BaseModel):
    scorecard_week: str
    measurable_status: dict[str, MeasurableStatusDto]
    issues_solved: list[str]
    todos_created: list[str]
    attendee_ids: list[str]
    rating: float | None


class MeetingStateDto(BaseModel):
    id: str
    team_id: str
    facilitator_id: str
    facilitator_name: str
    section: MeetingSectionDto
    section_started_at: datetime
    started_at: datetime
    ended_at: datetime | None
    scorecard_week: date
    server_now: datetime
    timer: MeetingTimerDto
    attendees: list[MeetingAttendeeDto]
    ratings: list[MeetingRatingDto]
    average_rating: float | None
    todos_created: list[TodoDto]
    summary: MeetingSummarySnapshotDto | None


class ActiveMeetingResponseDto(BaseModel):
    meeting: MeetingStateDto | None


class SubmitRatingRequestDto(BaseModel):
    rating: int = Field(..., ge=1, le=10)
