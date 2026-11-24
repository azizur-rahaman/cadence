"""CLI entrypoint (`python -m app.cli.report`) printing the unwrapped rules report JSON.

Uses `FrozenClock(APP_NOW)` so timestamps never drift and calls the pure-Python
`app.rules.report.build_rules_report` function over the live PostgreSQL dataset.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import FrozenClock
from app.config import get_settings
from app.db import SessionLocal
from app.models import (
    Company,
    Issue,
    Measurable,
    Meeting,
    MeetingAttendee,
    MeetingRating,
    Milestone,
    Rock,
    Score,
    Team,
    Todo,
)
from app.rules import (
    GoalType,
    MeasurableGoal,
    MilestoneRecord,
    ReportInput,
    ReportIssueInput,
    ReportMeasurableInput,
    ReportMeetingInput,
    ReportRockInput,
    ReportTodoInput,
    RockRecord,
    RockStatus,
    build_rules_report,
    get_company_tz,
)


def generate_rules_report_from_db(db: Session, *, now: datetime) -> dict[str, Any]:
    """Load all entities from PostgreSQL and compute the rules report for `now`."""
    company = db.execute(select(Company).limit(1)).scalar_one_or_none()
    tz = get_company_tz(company.timezone if company is not None else None)

    team_ids = [row[0] for row in db.execute(select(Team.id)).all()]

    measurables = [
        ReportMeasurableInput(
            id=m.id,
            team_id=m.team_id,
            goal=MeasurableGoal(
                goal_type=cast(GoalType, m.goal_type),
                value=m.goal_value,
                min_value=m.goal_min,
                max_value=m.goal_max,
            ),
        )
        for m in db.execute(select(Measurable)).scalars().all()
    ]

    scores: dict[tuple[str, date], Decimal] = {
        (s.measurable_id, s.week_start): s.value
        for s in db.execute(select(Score)).scalars().all()
    }

    milestones_by_rock: dict[str, list[MilestoneRecord]] = defaultdict(list)
    for ms in db.execute(select(Milestone)).scalars().all():
        milestones_by_rock[ms.rock_id].append(
            MilestoneRecord(id=ms.id, due_date=ms.due_date, done=ms.done)
        )

    rocks = [
        ReportRockInput(
            id=r.id,
            team_id=r.team_id,
            rock=RockRecord(
                id=r.id,
                quarter=r.quarter,
                seeded_status=cast(RockStatus, r.seeded_status),
                milestones=milestones_by_rock.get(r.id, []),
            ),
        )
        for r in db.execute(select(Rock)).scalars().all()
    ]

    todos = [
        ReportTodoInput(
            id=t.id,
            team_id=t.team_id,
            due_date=t.due_date,
            done_at=t.done_at,
            created_at=t.created_at,
            meeting_id=t.meeting_id,
        )
        for t in db.execute(select(Todo)).scalars().all()
    ]

    issues = [
        ReportIssueInput(
            id=i.id,
            team_id=i.team_id,
            priority=i.priority,
            created_at=i.created_at,
            solved_at=i.solved_at,
        )
        for i in db.execute(select(Issue)).scalars().all()
    ]

    attendees_by_meeting: dict[str, list[str]] = defaultdict(list)
    for att in db.execute(select(MeetingAttendee)).scalars().all():
        attendees_by_meeting[att.meeting_id].append(att.user_id)

    ratings_by_meeting: dict[str, list[int]] = defaultdict(list)
    for rat in db.execute(select(MeetingRating)).scalars().all():
        ratings_by_meeting[rat.meeting_id].append(rat.rating)

    meetings = [
        ReportMeetingInput(
            id=mt.id,
            team_id=mt.team_id,
            started_at=mt.started_at,
            ended_at=mt.ended_at,
            attendee_ids=attendees_by_meeting.get(mt.id, []),
            ratings=ratings_by_meeting.get(mt.id, []),
        )
        for mt in db.execute(select(Meeting)).scalars().all()
    ]

    report_input = ReportInput(
        team_ids=team_ids,
        measurables=measurables,
        scores=scores,
        todos=todos,
        rocks=rocks,
        issues=issues,
        meetings=meetings,
    )
    return build_rules_report(report_input, now=now, tz=tz)


def main() -> None:
    settings = get_settings()
    clock = FrozenClock(settings.app_now)
    with SessionLocal() as db:
        report = generate_rules_report_from_db(db, now=clock.now())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
