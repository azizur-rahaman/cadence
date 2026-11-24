"""Quarterly Rocks & Milestones Data Transfer Objects (DTOs)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

RockStatusDto = Literal["on_track", "off_track", "complete"]


class MilestoneDto(BaseModel):
    id: str
    title: str
    due_date: date
    done: bool
    is_past_due: bool


class RockDto(BaseModel):
    id: str
    team_id: str
    title: str
    owner_id: str
    owner_name: str
    quarter: str
    status: RockStatusDto
    progress_percent: int
    milestones: list[MilestoneDto]


class RockListDto(BaseModel):
    team_id: str
    quarter: str
    today: str
    items: list[RockDto]
