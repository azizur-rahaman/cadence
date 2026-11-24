"""Pure-Python rules report generator matching the starter README.md JSON contract.

Zero FastAPI or SQLAlchemy imports are permitted inside this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from app.rules.issues import IssueRecord, ordered_unsolved_issue_ids
from app.rules.meetings import compute_meeting_rating, compute_meeting_scorecard_week
from app.rules.rocks import RockRecord, evaluate_rock
from app.rules.scorecard import MeasurableGoal, evaluate_measurable_status
from app.rules.time_utils import DEFAULT_TZ, last_13_weeks, today_in_tz, week_start_of
from app.rules.todos import TodoRecord, compute_todo_completion_for_week, overdue_todo_ids


@dataclass(frozen=True)
class ReportMeasurableInput:
    id: str
    team_id: str
    goal: MeasurableGoal


@dataclass(frozen=True)
class ReportTodoInput:
    id: str
    team_id: str
    due_date: date
    done_at: datetime | None
    created_at: datetime
    meeting_id: str | None = None


@dataclass(frozen=True)
class ReportIssueInput:
    id: str
    team_id: str
    priority: int | None
    created_at: datetime
    solved_at: datetime | None


@dataclass(frozen=True)
class ReportRockInput:
    id: str
    team_id: str
    rock: RockRecord


@dataclass(frozen=True)
class ReportMeetingInput:
    id: str
    team_id: str
    started_at: datetime
    ended_at: datetime | None
    attendee_ids: Sequence[str]
    ratings: Sequence[int]


@dataclass(frozen=True)
class ReportInput:
    team_ids: Sequence[str]
    measurables: Sequence[ReportMeasurableInput]
    scores: Mapping[tuple[str, date], Decimal]
    todos: Sequence[ReportTodoInput]
    rocks: Sequence[ReportRockInput]
    issues: Sequence[ReportIssueInput]
    meetings: Sequence[ReportMeetingInput]


def _format_utc_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def build_rules_report(
    data: ReportInput,
    *,
    now: datetime,
    tz: ZoneInfo = DEFAULT_TZ,
) -> dict[str, Any]:
    """Compute the full unwrapped `rules_report.json` payload for `now` in `tz`."""
    today = today_in_tz(now, tz)
    weeks = last_13_weeks(now, tz)
    current_week = weeks[-1]

    teams_payload: dict[str, Any] = {}

    for team_id in sorted(data.team_ids):
        team_measurables = sorted(
            (m for m in data.measurables if m.team_id == team_id),
            key=lambda m: m.id,
        )
        team_todos_raw = [t for t in data.todos if t.team_id == team_id]
        team_todos = [
            TodoRecord(id=t.id, due_date=t.due_date, done_at=t.done_at) for t in team_todos_raw
        ]
        team_rocks = sorted(
            (r for r in data.rocks if r.team_id == team_id),
            key=lambda r: r.id,
        )
        team_issues_raw = [i for i in data.issues if i.team_id == team_id]
        team_issues = [
            IssueRecord(
                id=i.id,
                priority=i.priority,
                created_at=i.created_at,
                solved_at=i.solved_at,
            )
            for i in team_issues_raw
        ]
        team_ended_meetings = sorted(
            (m for m in data.meetings if m.team_id == team_id and m.ended_at is not None),
            key=lambda m: m.id,
        )

        measurable_status: dict[str, dict[str, str]] = {}
        for m in team_measurables:
            measurable_status[m.id] = {
                w.isoformat(): evaluate_measurable_status(
                    m.goal,
                    data.scores.get((m.id, w)),
                    week_start=w,
                    current_week_start=current_week,
                )
                for w in weeks
            }

        todo_completion: dict[str, dict[str, Any] | None] = {}
        for w in weeks:
            comp = compute_todo_completion_for_week(team_todos, w, tz=tz)
            todo_completion[w.isoformat()] = comp.to_dict() if comp is not None else None

        overdue = overdue_todo_ids(team_todos, today=today)

        rocks_payload = {
            r.id: evaluate_rock(r.rock, today=today).to_dict() for r in team_rocks
        }

        issue_order = ordered_unsolved_issue_ids(team_issues)

        meetings_payload: dict[str, Any] = {}
        for mt in team_ended_meetings:
            assert mt.ended_at is not None
            sc_week = compute_meeting_scorecard_week(mt.started_at, tz=tz)
            meeting_week = week_start_of(mt.started_at, tz)
            mt_measurable_status = {
                m.id: evaluate_measurable_status(
                    m.goal,
                    data.scores.get((m.id, sc_week)),
                    week_start=sc_week,
                    current_week_start=meeting_week,
                )
                for m in team_measurables
            }
            issues_solved = sorted(
                iss.id
                for iss in team_issues_raw
                if iss.solved_at is not None and mt.started_at <= iss.solved_at <= mt.ended_at
            )
            todos_created = sorted(
                td.id
                for td in team_todos_raw
                if td.meeting_id == mt.id or (mt.started_at <= td.created_at <= mt.ended_at)
            )
            meetings_payload[mt.id] = {
                "scorecard_week": sc_week.isoformat(),
                "measurable_status": mt_measurable_status,
                "issues_solved": issues_solved,
                "todos_created": todos_created,
                "attendee_ids": sorted(mt.attendee_ids),
                "rating": compute_meeting_rating(mt.ratings),
            }

        teams_payload[team_id] = {
            "measurable_status": measurable_status,
            "todo_completion": todo_completion,
            "overdue_todos": overdue,
            "rocks": rocks_payload,
            "issue_order": issue_order,
            "meetings": meetings_payload,
        }

    return {
        "now": _format_utc_iso(now),
        "teams": teams_payload,
    }
