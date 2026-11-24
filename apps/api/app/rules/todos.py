"""Pure To-Do completion rate, exact 90% target, and overdue rules (BR-03, BR-20)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.rules.time_utils import (
    DEFAULT_TZ,
    round_half_up_percent,
    week_start_of,
    week_start_of_date,
)


@dataclass(frozen=True)
class TodoRecord:
    id: str
    due_date: date
    done_at: datetime | None


@dataclass(frozen=True)
class TodoWeekCompletion:
    due: int
    done: int
    rate_percent: int
    meets_target: bool

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "due": self.due,
            "done": self.done,
            "rate_percent": self.rate_percent,
            "meets_target": self.meets_target,
        }


def is_todo_overdue(todo: TodoRecord, *, today: date) -> bool:
    """A To-Do is overdue iff it is not done and its due_date is strictly before today."""
    return todo.done_at is None and todo.due_date < today


def is_todo_done_on_time(todo: TodoRecord, *, tz: ZoneInfo = DEFAULT_TZ) -> bool:
    """A To-Do counts as done for its due week iff `done_at` falls on or before that week's end."""
    if todo.done_at is None:
        return False
    due_week = week_start_of_date(todo.due_date)
    done_week = week_start_of(todo.done_at, tz)
    return done_week <= due_week


def compute_todo_completion_for_week(
    todos: Sequence[TodoRecord],
    week_start: date,
    *,
    tz: ZoneInfo = DEFAULT_TZ,
) -> TodoWeekCompletion | None:
    """Compute To-Do completion metrics for a single Monday-Sunday week.

    Returns `None` when zero To-Dos are due in `week_start`.
    Compares exact integer ratio (`done * 10 >= due * 9`) against 90%, never the rounded percent.
    """
    due_in_week = [t for t in todos if week_start_of_date(t.due_date) == week_start]
    due_count = len(due_in_week)
    if due_count == 0:
        return None

    done_count = sum(1 for t in due_in_week if is_todo_done_on_time(t, tz=tz))
    rate_percent = round_half_up_percent(done_count, due_count)
    meets_target = (done_count * 10) >= (due_count * 9)

    return TodoWeekCompletion(
        due=due_count,
        done=done_count,
        rate_percent=rate_percent,
        meets_target=meets_target,
    )


def overdue_todo_ids(todos: Iterable[TodoRecord], *, today: date) -> list[str]:
    """Return overdue To-Do IDs sorted as plain strings (`t12` before `t30`)."""
    return sorted(t.id for t in todos if is_todo_overdue(t, today=today))
