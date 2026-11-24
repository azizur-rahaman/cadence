"""Pure Scorecard Measurable status evaluation rules (BR-10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from app.rules.time_utils import format_week_label

GoalType = Literal["at_least", "at_most", "between", "exactly"]
MeasurableStatus = Literal["on_track", "off_track", "pending"]


@dataclass(frozen=True)
class MeasurableGoal:
    goal_type: GoalType
    value: Decimal | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None


def evaluate_measurable_status(
    goal: MeasurableGoal,
    score: Decimal | None,
    *,
    week_start: date,
    current_week_start: date,
) -> MeasurableStatus:
    """Evaluate a Measurable's status for a single week against its goal.

    Rules (BR-10):
    - Missing score in a closed week (`week_start < current_week_start`) -> `off_track`
    - Missing score in the current (or future) week -> `pending`
    - Present score (even in current week) is evaluated against goal; boundaries are `on_track`.
    """
    if score is None:
        return "pending" if week_start >= current_week_start else "off_track"

    if goal.goal_type == "at_least":
        assert goal.value is not None
        return "on_track" if score >= goal.value else "off_track"

    if goal.goal_type == "at_most":
        assert goal.value is not None
        return "on_track" if score <= goal.value else "off_track"

    if goal.goal_type == "exactly":
        assert goal.value is not None
        return "on_track" if score == goal.value else "off_track"

    if goal.goal_type == "between":
        assert goal.min_value is not None and goal.max_value is not None
        return "on_track" if goal.min_value <= score <= goal.max_value else "off_track"

    raise ValueError(f"Unsupported goal_type: {goal.goal_type!r}")


def format_issue_title_from_measurable(measurable_name: str, week_start: date) -> str:
    """Format auto-generated Issue title matching seed convention (`<Name>, week of <Mon D>`)."""
    return f"{measurable_name}, week of {format_week_label(week_start)}"
