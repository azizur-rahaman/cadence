"""Team listing, team access verification, and eligible owner endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.deps import (
    TeamAccessContext,
    get_current_user,
    get_eligible_team_owners,
    list_accessible_teams,
    require_team_read,
)
from app.clock import Clock, get_clock
from app.db import get_db
from app.dto import (
    ApiErrorResponse,
    ApiResponse,
    TeamDto,
    TeamListDto,
    UserDto,
    UserListDto,
    ok,
)
from app.models import User

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get(
    "",
    response_model=ApiResponse[TeamListDto],
    responses={401: {"model": ApiErrorResponse}},
)
def list_teams(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[TeamListDto]:
    """List teams accessible to the authenticated user (all teams for Admin)."""
    teams = list_accessible_teams(user, db)
    payload = TeamListDto(items=[TeamDto.model_validate(t) for t in teams])
    return ok(payload, request=request, clock=clock)


@router.get(
    "/{team_id}",
    response_model=ApiResponse[TeamDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def get_team(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[TeamDto]:
    """Return team metadata if the authenticated user has read access (404 otherwise)."""
    return ok(TeamDto.model_validate(ctx.team), request=request, clock=clock)


@router.get(
    "/{team_id}/owners",
    response_model=ApiResponse[UserListDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def list_eligible_owners(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[UserListDto]:
    """List users eligible to own items in this team: (company Admins) U (team's Team Members)."""
    owners = get_eligible_team_owners(ctx.team.id, ctx.team.company_id, db)
    payload = UserListDto(items=[UserDto.model_validate(u) for u in owners])
    return ok(payload, request=request, clock=clock)
