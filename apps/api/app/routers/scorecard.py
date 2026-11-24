"""Scorecard 13-week grid, inline score upsert, and atomic Make it an Issue endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.auth.deps import TeamAccessContext, require_team_read, require_team_write
from app.clock import Clock, get_clock
from app.db import get_db
from app.dto import (
    ApiErrorResponse,
    ApiResponse,
    IssueDto,
    IssueSourceDto,
    MakeIssueFromMeasurableRequestDto,
    MakeIssueFromMeasurableResponseDto,
    MeasurableGoalDto,
    MeasurableRowDto,
    ScorecardResponseDto,
    ScoreCellDto,
    UpsertScoreRequestDto,
    UpsertScoreResponseDto,
    ok,
)
from app.errors import AppError
from app.models import Company, Issue, Measurable, Score, User
from app.realtime.hub import notify_team_workspace_change
from app.rules import (
    GoalType,
    MeasurableGoal,
    evaluate_measurable_status,
    format_issue_title_from_measurable,
    get_company_tz,
    last_13_weeks,
    last_closed_week,
    week_start_of,
)

router = APIRouter(prefix="/teams/{team_id}", tags=["Scorecard"])


def _fmt_decimal(d: Decimal) -> str:
    text_val = format(d.normalize(), "f")
    if "." in text_val:
        text_val = text_val.rstrip("0").rstrip(".")
    return text_val


def _format_goal_label(m: Measurable) -> str:
    if m.goal_type == "at_least" and m.goal_value is not None:
        return f"≥ {_fmt_decimal(m.goal_value)}"
    if m.goal_type == "at_most" and m.goal_value is not None:
        return f"≤ {_fmt_decimal(m.goal_value)}"
    if m.goal_type == "exactly" and m.goal_value is not None:
        return f"= {_fmt_decimal(m.goal_value)}"
    if m.goal_type == "between" and m.goal_min is not None and m.goal_max is not None:
        return f"{_fmt_decimal(m.goal_min)} – {_fmt_decimal(m.goal_max)}"
    return ""


def _to_rule_goal(m: Measurable) -> MeasurableGoal:
    return MeasurableGoal(
        goal_type=cast(GoalType, m.goal_type),
        value=m.goal_value,
        min_value=m.goal_min,
        max_value=m.goal_max,
    )


def _ensure_monday(week_start: date) -> None:
    if week_start.weekday() != 0:
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message="week_start must be a Monday.",
            fields={"week_start": "Must be a Monday (YYYY-MM-DD)"},
        )


def _get_team_tz(db: Session, company_id: str):
    company = db.get(Company, company_id)
    return get_company_tz(company.timezone if company is not None else None)


def _build_issue_dto(issue: Issue, owner_name: str) -> IssueDto:
    source = (
        IssueSourceDto(
            measurable_id=issue.source_measurable_id,
            week_start=issue.source_week_start,
        )
        if issue.source_measurable_id is not None and issue.source_week_start is not None
        else None
    )
    return IssueDto(
        id=issue.id,
        team_id=issue.team_id,
        title=issue.title,
        owner_id=issue.owner_id,
        owner_name=owner_name,
        priority=issue.priority,
        created_at=issue.created_at,
        solved_at=issue.solved_at,
        resolution_note=issue.resolution_note,
        source=source,
    )


@router.get(
    "/scorecard",
    response_model=ApiResponse[ScorecardResponseDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def get_scorecard(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[ScorecardResponseDto]:
    """Return the 13-week rolling Scorecard for `team_id` with server-computed statuses."""
    tz = _get_team_tz(db, ctx.team.company_id)
    now = clock.now()
    weeks = last_13_weeks(now, tz)
    current_week = weeks[-1]
    closed_week = last_closed_week(now, tz)

    measurables = (
        db.execute(
            select(Measurable)
            .where(Measurable.team_id == ctx.team.id)
            .order_by(Measurable.id)
        )
        .scalars()
        .all()
    )
    measurable_ids = [m.id for m in measurables]

    owner_ids = {m.owner_id for m in measurables}
    owners = (
        {
            u.id: u.name
            for u in db.execute(select(User).where(User.id.in_(owner_ids))).scalars().all()
        }
        if owner_ids
        else {}
    )

    score_map: dict[tuple[str, date], Decimal] = {}
    unsolved_issue_map: dict[tuple[str, date], str] = {}
    if measurable_ids:
        score_rows = (
            db.execute(
                select(Score).where(
                    Score.measurable_id.in_(measurable_ids),
                    Score.week_start >= weeks[0],
                    Score.week_start <= weeks[-1],
                )
            )
            .scalars()
            .all()
        )
        for s in score_rows:
            score_map[(s.measurable_id, s.week_start)] = s.value

        linked_issues = (
            db.execute(
                select(Issue.id, Issue.source_measurable_id, Issue.source_week_start).where(
                    Issue.team_id == ctx.team.id,
                    Issue.solved_at.is_(None),
                    Issue.source_measurable_id.in_(measurable_ids),
                )
            )
            .all()
        )
        for iss_id, src_mid, src_ws in linked_issues:
            if src_mid is not None and src_ws is not None:
                unsolved_issue_map[(src_mid, src_ws)] = iss_id

    rows: list[MeasurableRowDto] = []
    for m in measurables:
        rule_goal = _to_rule_goal(m)
        cells: list[ScoreCellDto] = []
        for w in weeks:
            raw_val = score_map.get((m.id, w))
            cell_status = evaluate_measurable_status(
                rule_goal,
                raw_val,
                week_start=w,
                current_week_start=current_week,
            )
            cells.append(
                ScoreCellDto(
                    week_start=w.isoformat(),
                    value=float(raw_val) if raw_val is not None else None,
                    status=cell_status,
                    unsolved_issue_id=unsolved_issue_map.get((m.id, w)),
                )
            )

        rows.append(
            MeasurableRowDto(
                id=m.id,
                team_id=m.team_id,
                name=m.name,
                owner_id=m.owner_id,
                owner_name=owners.get(m.owner_id, m.owner_id),
                unit=m.unit,
                goal=MeasurableGoalDto(
                    type=cast(GoalType, m.goal_type),
                    value=float(m.goal_value) if m.goal_value is not None else None,
                    min=float(m.goal_min) if m.goal_min is not None else None,
                    max=float(m.goal_max) if m.goal_max is not None else None,
                    label=_format_goal_label(m),
                ),
                cells=cells,
            )
        )

    payload = ScorecardResponseDto(
        team_id=ctx.team.id,
        current_week_start=current_week.isoformat(),
        last_closed_week_start=closed_week.isoformat(),
        weeks=[w.isoformat() for w in weeks],
        measurables=rows,
    )
    return ok(payload, request=request, clock=clock)


@router.put(
    "/measurables/{measurable_id}/scores/{week_start}",
    response_model=ApiResponse[UpsertScoreResponseDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def upsert_score(
    measurable_id: str,
    week_start: date,
    body: UpsertScoreRequestDto,
    request: Request,
    background_tasks: BackgroundTasks,
    ctx: TeamAccessContext = Depends(require_team_write),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[UpsertScoreResponseDto]:
    """Create or update a weekly score cell and return its server-computed status."""
    _ensure_monday(week_start)

    measurable = db.execute(
        select(Measurable).where(
            Measurable.id == measurable_id,
            Measurable.team_id == ctx.team.id,
        )
    ).scalar_one_or_none()
    if measurable is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Measurable not found.",
        )

    stmt = pg_insert(Score).values(
        measurable_id=measurable.id,
        week_start=week_start,
        value=body.value,
    )
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["measurable_id", "week_start"],
            set_={"value": stmt.excluded.value},
        )
    )
    db.commit()

    tz = _get_team_tz(db, ctx.team.company_id)
    current_week = week_start_of(clock.now(), tz)
    cell_status = evaluate_measurable_status(
        _to_rule_goal(measurable),
        body.value,
        week_start=week_start,
        current_week_start=current_week,
    )

    unsolved_issue_id = db.execute(
        select(Issue.id).where(
            Issue.source_measurable_id == measurable.id,
            Issue.source_week_start == week_start,
            Issue.solved_at.is_(None),
        )
    ).scalar_one_or_none()

    payload = UpsertScoreResponseDto(
        measurable_id=measurable.id,
        week_start=week_start.isoformat(),
        value=float(body.value),
        status=cell_status,
        unsolved_issue_id=unsolved_issue_id,
    )
    notify_team_workspace_change(background_tasks, ctx.team.id, "scorecard", db)
    return ok(payload, request=request, clock=clock)


@router.post(
    "/issues/from-measurable",
    response_model=ApiResponse[MakeIssueFromMeasurableResponseDto],
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"model": ApiResponse[MakeIssueFromMeasurableResponseDto]},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def make_issue_from_measurable(
    body: MakeIssueFromMeasurableRequestDto,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    ctx: TeamAccessContext = Depends(require_team_write),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[MakeIssueFromMeasurableResponseDto]:
    """Atomically create (201) or return existing unsolved (200) Issue for an off-track cell."""
    _ensure_monday(body.week_start)

    measurable = db.execute(
        select(Measurable).where(
            Measurable.id == body.measurable_id,
            Measurable.team_id == ctx.team.id,
        )
    ).scalar_one_or_none()
    if measurable is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Measurable not found.",
        )

    tz = _get_team_tz(db, ctx.team.company_id)
    now = clock.now()
    current_week = week_start_of(now, tz)

    score_row = db.execute(
        select(Score).where(
            Score.measurable_id == measurable.id,
            Score.week_start == body.week_start,
        )
    ).scalar_one_or_none()
    cell_status = evaluate_measurable_status(
        _to_rule_goal(measurable),
        score_row.value if score_row is not None else None,
        week_start=body.week_start,
        current_week_start=current_week,
    )
    if cell_status != "off_track":
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message="Only off-track scorecard cells can be turned into an Issue.",
            fields={"week_start": f"Cell status is '{cell_status}', not 'off_track'."},
        )

    title = format_issue_title_from_measurable(measurable.name, body.week_start)
    new_issue_id = f"iss_{uuid.uuid4().hex[:12]}"

    insert_stmt = (
        pg_insert(Issue)
        .values(
            id=new_issue_id,
            team_id=ctx.team.id,
            title=title,
            owner_id=measurable.owner_id,
            priority=None,
            created_at=now,
            solved_at=None,
            resolution_note=None,
            source_measurable_id=measurable.id,
            source_week_start=body.week_start,
        )
        .on_conflict_do_nothing(
            index_elements=["source_measurable_id", "source_week_start"],
            index_where=text("solved_at IS NULL AND source_measurable_id IS NOT NULL"),
        )
        .returning(Issue.id)
    )
    inserted_id = db.execute(insert_stmt).scalar_one_or_none()
    db.commit()

    if inserted_id is not None:
        created = True
        response.status_code = status.HTTP_201_CREATED
        issue = db.get(Issue, inserted_id)
    else:
        created = False
        response.status_code = status.HTTP_200_OK
        issue = db.execute(
            select(Issue).where(
                Issue.source_measurable_id == measurable.id,
                Issue.source_week_start == body.week_start,
                Issue.solved_at.is_(None),
            )
        ).scalar_one()

    assert issue is not None
    owner = db.get(User, issue.owner_id)
    owner_name = owner.name if owner is not None else issue.owner_id

    payload = MakeIssueFromMeasurableResponseDto(
        created=created,
        issue=_build_issue_dto(issue, owner_name),
    )
    notify_team_workspace_change(background_tasks, ctx.team.id, "issues", db)
    return ok(payload, request=request, clock=clock)
