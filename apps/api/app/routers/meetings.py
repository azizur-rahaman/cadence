"""Level 10 Meeting lifecycle, join, facilitator controls, rating, and summary endpoints."""

from __future__ import annotations

import uuid
from typing import cast

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import (
    TeamAccessContext,
    assert_team_read,
    assert_team_write,
    get_current_user,
    require_team_read,
    require_team_write,
)
from app.clock import Clock, get_clock
from app.db import get_db
from app.dto import (
    ActiveMeetingResponseDto,
    ApiErrorResponse,
    ApiResponse,
    MeetingStateDto,
    MeetingSummarySnapshotDto,
    SubmitRatingRequestDto,
    ok,
)
from app.errors import AppError
from app.models import Company, Meeting, MeetingAttendee, MeetingRating, MeetingSummary, User
from app.rules import (
    NEXT_SECTION,
    MeetingSection,
    compute_meeting_scorecard_week,
    get_company_tz,
)
from app.services.meetings import build_and_store_meeting_summary, build_meeting_state_dto

router = APIRouter(tags=["Meetings"])


def _load_meeting_or_404(meeting_id: str, db: Session) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Meeting not found.")
    return meeting


@router.get(
    "/teams/{team_id}/meetings/active",
    response_model=ApiResponse[ActiveMeetingResponseDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def get_active_meeting(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[ActiveMeetingResponseDto]:
    """Return the currently active Level 10 meeting for `team_id`, or `null` if none."""
    meeting = db.execute(
        select(Meeting).where(Meeting.team_id == ctx.team.id, Meeting.ended_at.is_(None))
    ).scalar_one_or_none()
    state = build_meeting_state_dto(meeting, db, clock) if meeting is not None else None
    return ok(ActiveMeetingResponseDto(meeting=state), request=request, clock=clock)


@router.post(
    "/teams/{team_id}/meetings",
    response_model=ApiResponse[MeetingStateDto],
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
def start_meeting(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_write),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingStateDto]:
    """Start a new Level 10 meeting for `team_id` (409 if one is already active)."""
    company = db.get(Company, ctx.team.company_id)
    tz = get_company_tz(company.timezone if company is not None else None)
    now = clock.now()
    scorecard_week = compute_meeting_scorecard_week(now, tz=tz)

    meeting = Meeting(
        id=f"mt_{uuid.uuid4().hex[:12]}",
        team_id=ctx.team.id,
        facilitator_id=ctx.user.id,
        section="scorecard",
        section_started_at=now,
        started_at=now,
        ended_at=None,
        scorecard_week=scorecard_week,
    )
    db.add(meeting)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            status.HTTP_409_CONFLICT,
            "MEETING_ALREADY_ACTIVE",
            "An active meeting is already in progress for this team.",
        ) from exc

    db.execute(
        pg_insert(MeetingAttendee)
        .values(meeting_id=meeting.id, user_id=ctx.user.id, joined_at=now)
        .on_conflict_do_nothing(index_elements=["meeting_id", "user_id"])
    )
    db.commit()
    db.refresh(meeting)

    return ok(build_meeting_state_dto(meeting, db, clock), request=request, clock=clock)


@router.get(
    "/meetings/{meeting_id}",
    response_model=ApiResponse[MeetingStateDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def get_meeting(
    meeting_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingStateDto]:
    """Return full server-owned state for `meeting_id`."""
    meeting = _load_meeting_or_404(meeting_id, db)
    assert_team_read(user, meeting.team_id, db)
    return ok(build_meeting_state_dto(meeting, db, clock), request=request, clock=clock)


@router.post(
    "/meetings/{meeting_id}/join",
    response_model=ApiResponse[MeetingStateDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def join_meeting(
    meeting_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingStateDto]:
    """Record the authenticated user (including Observers) as a persistent attendee."""
    meeting = _load_meeting_or_404(meeting_id, db)
    assert_team_read(user, meeting.team_id, db)

    if meeting.ended_at is None:
        db.execute(
            pg_insert(MeetingAttendee)
            .values(meeting_id=meeting.id, user_id=user.id, joined_at=clock.now())
            .on_conflict_do_nothing(index_elements=["meeting_id", "user_id"])
        )
        db.commit()

    return ok(build_meeting_state_dto(meeting, db, clock), request=request, clock=clock)


@router.post(
    "/meetings/{meeting_id}/advance",
    response_model=ApiResponse[MeetingStateDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
def advance_meeting(
    meeting_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingStateDto]:
    """Advance the meeting to the next agenda section (facilitator-only)."""
    meeting = _load_meeting_or_404(meeting_id, db)
    assert_team_write(user, meeting.team_id, db)

    if user.id != meeting.facilitator_id:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Only the meeting facilitator can advance sections.",
        )
    if meeting.section == "ended" or meeting.ended_at is not None:
        raise AppError(status.HTTP_409_CONFLICT, "CONFLICT", "Meeting has already ended.")

    now = clock.now()
    next_sec = NEXT_SECTION[cast(MeetingSection, meeting.section)]
    meeting.section = next_sec
    meeting.section_started_at = now
    if next_sec == "ended":
        meeting.ended_at = now
        db.flush()
        build_and_store_meeting_summary(meeting, db)

    db.commit()
    db.refresh(meeting)
    return ok(build_meeting_state_dto(meeting, db, clock), request=request, clock=clock)


@router.post(
    "/meetings/{meeting_id}/end",
    response_model=ApiResponse[MeetingStateDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
def end_meeting(
    meeting_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingStateDto]:
    """End the meeting immediately and persist its immutable summary (facilitator-only)."""
    meeting = _load_meeting_or_404(meeting_id, db)
    assert_team_write(user, meeting.team_id, db)

    if user.id != meeting.facilitator_id:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Only the meeting facilitator can end the meeting.",
        )
    if meeting.section == "ended" or meeting.ended_at is not None:
        raise AppError(status.HTTP_409_CONFLICT, "CONFLICT", "Meeting has already ended.")

    now = clock.now()
    meeting.section = "ended"
    meeting.section_started_at = now
    meeting.ended_at = now
    db.flush()
    build_and_store_meeting_summary(meeting, db)
    db.commit()
    db.refresh(meeting)

    return ok(build_meeting_state_dto(meeting, db, clock), request=request, clock=clock)


@router.put(
    "/meetings/{meeting_id}/rating",
    response_model=ApiResponse[MeetingStateDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def submit_meeting_rating(
    meeting_id: str,
    body: SubmitRatingRequestDto,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingStateDto]:
    """Submit or update a 1–10 meeting rating before the meeting ends (non-Observers only)."""
    meeting = _load_meeting_or_404(meeting_id, db)
    assert_team_write(user, meeting.team_id, db)

    if meeting.section == "ended" or meeting.ended_at is not None:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Ratings are locked after the meeting ends.",
        )

    now = clock.now()
    db.execute(
        pg_insert(MeetingAttendee)
        .values(meeting_id=meeting.id, user_id=user.id, joined_at=now)
        .on_conflict_do_nothing(index_elements=["meeting_id", "user_id"])
    )
    rat_stmt = pg_insert(MeetingRating).values(
        meeting_id=meeting.id,
        user_id=user.id,
        rating=body.rating,
        updated_at=now,
    )
    db.execute(
        rat_stmt.on_conflict_do_update(
            index_elements=["meeting_id", "user_id"],
            set_={"rating": rat_stmt.excluded.rating, "updated_at": rat_stmt.excluded.updated_at},
        )
    )
    db.commit()

    return ok(build_meeting_state_dto(meeting, db, clock), request=request, clock=clock)


@router.get(
    "/meetings/{meeting_id}/summary",
    response_model=ApiResponse[MeetingSummarySnapshotDto],
    responses={
        401: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
def get_meeting_summary(
    meeting_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MeetingSummarySnapshotDto]:
    """Return the immutable post-meeting summary snapshot for an ended meeting."""
    meeting = _load_meeting_or_404(meeting_id, db)
    assert_team_read(user, meeting.team_id, db)

    if meeting.section != "ended" or meeting.ended_at is None:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Meeting summary is only available after the meeting has ended.",
        )

    summary = db.get(MeetingSummary, meeting.id)
    if summary is None:
        summary = build_and_store_meeting_summary(meeting, db)
        db.commit()

    return ok(
        MeetingSummarySnapshotDto.model_validate(summary.snapshot),
        request=request,
        clock=clock,
    )
