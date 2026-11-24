"""Domain service helpers for Level 10 Meeting state assembly and immutable summaries."""

from __future__ import annotations

from typing import cast

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.clock import Clock
from app.dto import (
    MeetingAttendeeDto,
    MeetingRatingDto,
    MeetingSectionDto,
    MeetingStateDto,
    MeetingSummarySnapshotDto,
    MeetingTimerDto,
    RoleType,
    TodoDto,
)
from app.models import (
    Company,
    Issue,
    Measurable,
    Meeting,
    MeetingAttendee,
    MeetingRating,
    MeetingSummary,
    Score,
    Team,
    Todo,
    User,
)
from app.rules import (
    GoalType,
    MeasurableGoal,
    MeetingSection,
    TodoRecord,
    compute_meeting_rating,
    compute_timer_state,
    evaluate_measurable_status,
    get_company_tz,
    is_todo_overdue,
    today_in_tz,
    week_start_of,
)


def build_and_store_meeting_summary(meeting: Meeting, db: Session) -> MeetingSummary:
    """Compute and persist the immutable `MeetingSummary` snapshot when a meeting ends."""
    assert meeting.ended_at is not None

    team = db.get(Team, meeting.team_id)
    company = db.get(Company, team.company_id) if team is not None else None
    tz = get_company_tz(company.timezone if company is not None else None)

    measurables = (
        db.execute(
            select(Measurable)
            .where(Measurable.team_id == meeting.team_id)
            .order_by(Measurable.id)
        )
        .scalars()
        .all()
    )
    measurable_ids = [m.id for m in measurables]

    score_map = {}
    if measurable_ids:
        score_rows = (
            db.execute(
                select(Score).where(
                    Score.measurable_id.in_(measurable_ids),
                    Score.week_start == meeting.scorecard_week,
                )
            )
            .scalars()
            .all()
        )
        score_map = {s.measurable_id: s.value for s in score_rows}

    meeting_week = week_start_of(meeting.started_at, tz)
    measurable_status = {
        m.id: evaluate_measurable_status(
            MeasurableGoal(
                goal_type=cast(GoalType, m.goal_type),
                value=m.goal_value,
                min_value=m.goal_min,
                max_value=m.goal_max,
            ),
            score_map.get(m.id),
            week_start=meeting.scorecard_week,
            current_week_start=meeting_week,
        )
        for m in measurables
    }

    solved_ids = sorted(
        db.execute(
            select(Issue.id).where(
                Issue.team_id == meeting.team_id,
                Issue.solved_at.is_not(None),
                Issue.solved_at >= meeting.started_at,
                Issue.solved_at <= meeting.ended_at,
            )
        )
        .scalars()
        .all()
    )

    todo_ids = sorted(
        db.execute(
            select(Todo.id).where(
                Todo.team_id == meeting.team_id,
                or_(
                    Todo.meeting_id == meeting.id,
                    (Todo.created_at >= meeting.started_at)
                    & (Todo.created_at <= meeting.ended_at),
                ),
            )
        )
        .scalars()
        .all()
    )

    attendee_ids = sorted(
        db.execute(
            select(MeetingAttendee.user_id).where(MeetingAttendee.meeting_id == meeting.id)
        )
        .scalars()
        .all()
    )

    ratings = (
        db.execute(
            select(MeetingRating.rating).where(MeetingRating.meeting_id == meeting.id)
        )
        .scalars()
        .all()
    )
    rating_avg = compute_meeting_rating(ratings)

    snapshot = {
        "scorecard_week": meeting.scorecard_week.isoformat(),
        "measurable_status": measurable_status,
        "issues_solved": solved_ids,
        "todos_created": todo_ids,
        "attendee_ids": attendee_ids,
        "rating": rating_avg,
    }

    stmt = pg_insert(MeetingSummary).values(
        meeting_id=meeting.id,
        snapshot=snapshot,
        created_at=meeting.ended_at,
    )
    db.execute(stmt.on_conflict_do_nothing(index_elements=["meeting_id"]))
    summary = db.get(MeetingSummary, meeting.id)
    assert summary is not None
    return summary


def build_meeting_state_dto(
    meeting: Meeting, db: Session, clock: Clock
) -> MeetingStateDto:
    """Assemble the complete real-time `MeetingStateDto` for REST & WebSocket snapshots."""
    now = clock.now()
    timer_state = compute_timer_state(
        cast(MeetingSection, meeting.section),
        meeting.section_started_at,
        now,
    )

    attendee_rows = (
        db.execute(
            select(MeetingAttendee)
            .where(MeetingAttendee.meeting_id == meeting.id)
            .order_by(MeetingAttendee.joined_at.asc(), MeetingAttendee.user_id.asc())
        )
        .scalars()
        .all()
    )
    rating_rows = (
        db.execute(
            select(MeetingRating)
            .where(MeetingRating.meeting_id == meeting.id)
            .order_by(MeetingRating.user_id.asc())
        )
        .scalars()
        .all()
    )

    todo_filter = (
        or_(
            Todo.meeting_id == meeting.id,
            (Todo.created_at >= meeting.started_at)
            & (Todo.created_at <= meeting.ended_at),
        )
        if meeting.ended_at is not None
        else or_(
            Todo.meeting_id == meeting.id,
            Todo.created_at >= meeting.started_at,
        )
    )
    todo_rows = (
        db.execute(
            select(Todo)
            .where(Todo.team_id == meeting.team_id, todo_filter)
            .order_by(Todo.created_at.asc(), Todo.id.asc())
        )
        .scalars()
        .all()
    )

    user_ids = (
        {meeting.facilitator_id}
        | {a.user_id for a in attendee_rows}
        | {r.user_id for r in rating_rows}
        | {t.owner_id for t in todo_rows}
    )
    users = {
        u.id: u
        for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()
    }

    team = db.get(Team, meeting.team_id)
    company = db.get(Company, team.company_id) if team is not None else None
    tz = get_company_tz(company.timezone if company is not None else None)
    today = today_in_tz(now, tz)

    attendees = [
        MeetingAttendeeDto(
            user_id=a.user_id,
            name=users[a.user_id].name if a.user_id in users else a.user_id,
            role=cast(RoleType, users[a.user_id].role) if a.user_id in users else "team_member",
            joined_at=a.joined_at,
        )
        for a in attendee_rows
    ]
    ratings = [
        MeetingRatingDto(
            user_id=r.user_id,
            name=users[r.user_id].name if r.user_id in users else r.user_id,
            rating=r.rating,
            updated_at=r.updated_at,
        )
        for r in rating_rows
    ]
    todos_created = [
        TodoDto(
            id=t.id,
            team_id=t.team_id,
            title=t.title,
            owner_id=t.owner_id,
            owner_name=users[t.owner_id].name if t.owner_id in users else t.owner_id,
            due_date=t.due_date,
            done_at=t.done_at,
            is_overdue=is_todo_overdue(
                TodoRecord(id=t.id, due_date=t.due_date, done_at=t.done_at),
                today=today,
            ),
            source_issue_id=t.source_issue_id,
            created_at=t.created_at,
            meeting_id=t.meeting_id,
        )
        for t in todo_rows
    ]

    summary_dto: MeetingSummarySnapshotDto | None = None
    if meeting.section == "ended":
        summary_row = db.get(MeetingSummary, meeting.id)
        if summary_row is not None:
            summary_dto = MeetingSummarySnapshotDto.model_validate(summary_row.snapshot)

    facilitator = users.get(meeting.facilitator_id)
    return MeetingStateDto(
        id=meeting.id,
        team_id=meeting.team_id,
        facilitator_id=meeting.facilitator_id,
        facilitator_name=facilitator.name if facilitator is not None else meeting.facilitator_id,
        section=cast(MeetingSectionDto, meeting.section),
        section_started_at=meeting.section_started_at,
        started_at=meeting.started_at,
        ended_at=meeting.ended_at,
        scorecard_week=meeting.scorecard_week,
        server_now=now,
        timer=MeetingTimerDto(
            allotted_seconds=timer_state.allotted_seconds,
            elapsed_seconds=timer_state.elapsed_seconds,
            remaining_seconds=timer_state.remaining_seconds,
            over_time=timer_state.over_time,
        ),
        attendees=attendees,
        ratings=ratings,
        average_rating=compute_meeting_rating([r.rating for r in rating_rows]),
        todos_created=todos_created,
        summary=summary_dto,
    )
