"""Read-only current-quarter Rocks and Milestones endpoint."""

from __future__ import annotations

from collections import defaultdict
from typing import cast

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import TeamAccessContext, require_team_read
from app.clock import Clock, get_clock
from app.db import get_db
from app.dto import ApiErrorResponse, ApiResponse, MilestoneDto, RockDto, RockListDto, ok
from app.models import Company, Milestone, Rock, User
from app.rules import (
    MilestoneRecord,
    RockRecord,
    RockStatus,
    evaluate_rock,
    get_company_tz,
    is_milestone_past_due,
    quarter_of,
    today_in_tz,
)

router = APIRouter(prefix="/teams/{team_id}", tags=["Rocks"])


@router.get(
    "/rocks",
    response_model=ApiResponse[RockListDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def list_team_rocks(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[RockListDto]:
    """Return current-quarter Rocks with server-computed status, progress %, and Milestones."""
    company = db.get(Company, ctx.team.company_id)
    tz = get_company_tz(company.timezone if company is not None else None)
    today = today_in_tz(clock.now(), tz)
    current_quarter = quarter_of(today)

    rocks = (
        db.execute(
            select(Rock)
            .where(Rock.team_id == ctx.team.id, Rock.quarter == current_quarter)
            .order_by(Rock.id)
        )
        .scalars()
        .all()
    )
    rock_ids = [r.id for r in rocks]
    owner_ids = {r.owner_id for r in rocks}
    owners = (
        {
            u.id: u.name
            for u in db.execute(select(User).where(User.id.in_(owner_ids))).scalars().all()
        }
        if owner_ids
        else {}
    )

    milestones_by_rock: dict[str, list[Milestone]] = defaultdict(list)
    if rock_ids:
        ms_rows = (
            db.execute(
                select(Milestone)
                .where(Milestone.rock_id.in_(rock_ids))
                .order_by(Milestone.due_date.asc(), Milestone.id.asc())
            )
            .scalars()
            .all()
        )
        for ms in ms_rows:
            milestones_by_rock[ms.rock_id].append(ms)

    items: list[RockDto] = []
    for r in rocks:
        ms_models = milestones_by_rock.get(r.id, [])
        ms_records = [
            MilestoneRecord(id=ms.id, due_date=ms.due_date, done=ms.done) for ms in ms_models
        ]
        ev = evaluate_rock(
            RockRecord(
                id=r.id,
                quarter=r.quarter,
                seeded_status=cast(RockStatus, r.seeded_status),
                milestones=ms_records,
            ),
            today=today,
        )
        ms_dtos = [
            MilestoneDto(
                id=ms.id,
                title=ms.title,
                due_date=ms.due_date,
                done=ms.done,
                is_past_due=is_milestone_past_due(
                    MilestoneRecord(id=ms.id, due_date=ms.due_date, done=ms.done),
                    today=today,
                ),
            )
            for ms in ms_models
        ]
        items.append(
            RockDto(
                id=r.id,
                team_id=r.team_id,
                title=r.title,
                owner_id=r.owner_id,
                owner_name=owners.get(r.owner_id, r.owner_id),
                quarter=r.quarter,
                status=ev.status,
                progress_percent=ev.progress_percent,
                milestones=ms_dtos,
            )
        )

    payload = RockListDto(
        team_id=ctx.team.id,
        quarter=current_quarter,
        today=today.isoformat(),
        items=items,
    )
    return ok(payload, request=request, clock=clock)
