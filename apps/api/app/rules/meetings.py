"""Pure Level 10 Meeting rating, timer, and summary computation rules (BR-50)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from app.rules.time_utils import DEFAULT_TZ, last_closed_week, round_half_up_1dp

MeetingSection = Literal["scorecard", "ids", "conclude", "ended"]

SECTION_ALLOTMENTS_SECONDS: dict[MeetingSection, int] = {
    "scorecard": 5 * 60,
    "ids": 60 * 60,
    "conclude": 10 * 60,
    "ended": 0,
}

NEXT_SECTION: dict[MeetingSection, MeetingSection] = {
    "scorecard": "ids",
    "ids": "conclude",
    "conclude": "ended",
    "ended": "ended",
}


@dataclass(frozen=True)
class MeetingTimerState:
    allotted_seconds: int
    elapsed_seconds: int
    remaining_seconds: int
    over_time: bool


def compute_meeting_rating(ratings: Sequence[int]) -> float | None:
    """Average submitted ratings to one decimal place (half up); `None` if no ratings."""
    if not ratings:
        return None
    return round_half_up_1dp(sum(ratings), len(ratings))


def compute_meeting_scorecard_week(
    started_at: datetime, *, tz: ZoneInfo = DEFAULT_TZ
) -> date:
    """Return the last closed week reviewed by a meeting starting at `started_at`."""
    return last_closed_week(started_at, tz)


def compute_timer_state(
    section: MeetingSection,
    section_started_at: datetime,
    now: datetime,
) -> MeetingTimerState:
    """Compute server-owned section timer state without ever auto-advancing on overrun."""
    allotted = SECTION_ALLOTMENTS_SECONDS[section]
    if section == "ended":
        return MeetingTimerState(
            allotted_seconds=0,
            elapsed_seconds=0,
            remaining_seconds=0,
            over_time=False,
        )
    elapsed = max(0, int((now - section_started_at).total_seconds()))
    remaining = allotted - elapsed
    return MeetingTimerState(
        allotted_seconds=allotted,
        elapsed_seconds=elapsed,
        remaining_seconds=remaining,
        over_time=elapsed > allotted,
    )
