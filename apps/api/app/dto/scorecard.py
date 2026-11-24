"""Scorecard Data Transfer Objects (DTOs)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.dto.issues import IssueDto

GoalTypeDto = Literal["at_least", "at_most", "between", "exactly"]
MeasurableStatusDto = Literal["on_track", "off_track", "pending"]


class MeasurableGoalDto(BaseModel):
    type: GoalTypeDto
    value: float | None = None
    min: float | None = None
    max: float | None = None
    label: str


class ScoreCellDto(BaseModel):
    week_start: str
    value: float | None
    status: MeasurableStatusDto
    unsolved_issue_id: str | None = None


class MeasurableRowDto(BaseModel):
    id: str
    team_id: str
    name: str
    owner_id: str
    owner_name: str
    unit: str
    goal: MeasurableGoalDto
    cells: list[ScoreCellDto]


class ScorecardResponseDto(BaseModel):
    team_id: str
    current_week_start: str
    last_closed_week_start: str
    weeks: list[str]
    measurables: list[MeasurableRowDto]


class UpsertScoreRequestDto(BaseModel):
    value: Decimal = Field(..., description="Numeric score value for the measurable and week.")

    @field_validator("value")
    @classmethod
    def must_be_finite(cls, v: Decimal) -> Decimal:
        if not v.is_finite():
            raise ValueError("Score value must be a finite number.")
        return v


class UpsertScoreResponseDto(BaseModel):
    measurable_id: str
    week_start: str
    value: float
    status: MeasurableStatusDto
    unsolved_issue_id: str | None = None


class MakeIssueFromMeasurableRequestDto(BaseModel):
    measurable_id: str = Field(..., min_length=1)
    week_start: date


class MakeIssueFromMeasurableResponseDto(BaseModel):
    created: bool
    issue: IssueDto
