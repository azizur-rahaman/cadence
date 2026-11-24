"""Team listing, team access verification, and eligible owner endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import (
    TeamAccessContext,
    get_current_user,
    get_eligible_team_owners,
    list_accessible_teams,
    require_team_read,
)
from app.db import get_db
from app.models import User
from app.schemas import ErrorResponse, TeamOut, UserOut

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get(
    "",
    response_model=list[TeamOut],
    responses={401: {"model": ErrorResponse}},
)
def list_teams(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TeamOut]:
    """List teams accessible to the authenticated user (all teams for Admin)."""
    teams = list_accessible_teams(user, db)
    return [TeamOut.model_validate(t) for t in teams]


@router.get(
    "/{team_id}",
    response_model=TeamOut,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_team(
    ctx: TeamAccessContext = Depends(require_team_read),
) -> TeamOut:
    """Return team metadata if the authenticated user has read access (404 otherwise)."""
    return TeamOut.model_validate(ctx.team)


@router.get(
    "/{team_id}/owners",
    response_model=list[UserOut],
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def list_eligible_owners(
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    """List users eligible to own items in this team: (company Admins) U (team's Team Members)."""
    owners = get_eligible_team_owners(ctx.team.id, ctx.team.company_id, db)
    return [UserOut.model_validate(u) for u in owners]
