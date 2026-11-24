"""Pure quarterly Rock status and Milestone progress rules (BR-30, BR-31)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.rules.time_utils import round_half_up_percent

RockStatus = Literal["on_track", "off_track", "complete"]


@dataclass(frozen=True)
class MilestoneRecord:
    id: str
    due_date: date
    done: bool


@dataclass(frozen=True)
class RockRecord:
    id: str
    quarter: str
    seeded_status: RockStatus
    milestones: Sequence[MilestoneRecord]


@dataclass(frozen=True)
class RockEvaluation:
    status: RockStatus
    progress_percent: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "status": self.status,
            "progress_percent": self.progress_percent,
        }


def is_milestone_past_due(milestone: MilestoneRecord, *, today: date) -> bool:
    """A Milestone is past due iff it is unfinished and due strictly before today."""
    return (not milestone.done) and (milestone.due_date < today)


def evaluate_rock(rock: RockRecord, *, today: date) -> RockEvaluation:
    """Compute a Rock's status and whole-percent Milestone progress (half up).

    Rules (BR-30, BR-31):
    - Status is `complete` if seeded `complete`.
    - Else `off_track` if seeded `off_track` OR any unfinished Milestone is past due.
    - Else `on_track`.
    - Progress: completed Milestones / total Milestones (whole percent, half up).
      No Milestones -> `100` if `complete`, else `0`.
    """
    if rock.seeded_status == "complete":
        status: RockStatus = "complete"
    elif rock.seeded_status == "off_track" or any(
        is_milestone_past_due(ms, today=today) for ms in rock.milestones
    ):
        status = "off_track"
    else:
        status = "on_track"

    total = len(rock.milestones)
    if total == 0:
        progress = 100 if status == "complete" else 0
    else:
        completed = sum(1 for ms in rock.milestones if ms.done)
        progress = round_half_up_percent(completed, total)

    return RockEvaluation(status=status, progress_percent=progress)
