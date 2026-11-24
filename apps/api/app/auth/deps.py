"""Centralized server-side authentication, RBAC, and team-boundary dependencies.

All routes MUST use these dependencies/helpers rather than ad-hoc role checks.
Invariants:
- Missing or invalid token -> 401 UNAUTHORIZED
- Non-member team access (including guessed IDs) -> 404 TEAM_NOT_FOUND
- Observer write / facilitate / rate -> 403 FORBIDDEN
- Admin has read/write/ownership access across ALL company teams even without
  explicit membership rows.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.tokens import InvalidTokenError, verify_access_token
from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.models import Membership, Team, User

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TeamAccessContext:
    """Resolved authenticated user and authorized team for a route."""

    user: User
    team: Team


def authenticate_token(token: str | None, db: Session) -> User:
    """Verify a raw Bearer/WebSocket token and load the corresponding User."""
    if not token:
        raise AppError(401, "UNAUTHORIZED", "Authentication token is required.")

    try:
        payload = verify_access_token(token, secret=get_settings().auth_secret)
    except InvalidTokenError as exc:
        raise AppError(401, "UNAUTHORIZED", "Invalid or expired authentication token.") from exc

    user = db.get(User, payload.user_id)
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "Authenticated user no longer exists.")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency returning the authenticated User from the Bearer token."""
    raw_token = (
        credentials.credentials
        if credentials and credentials.scheme.lower() == "bearer"
        else None
    )
    return authenticate_token(raw_token, db)


def assert_team_read(user: User, team_id: str, db: Session) -> Team:
    """Verify the user can read `team_id`; raises 404 on missing or unauthorized team."""
    team = db.execute(
        select(Team).where(Team.id == team_id, Team.company_id == user.company_id)
    ).scalar_one_or_none()
    if team is None:
        raise AppError(404, "TEAM_NOT_FOUND", "Team not found.")

    if user.role == "admin":
        return team

    membership = db.execute(
        select(Membership).where(Membership.user_id == user.id, Membership.team_id == team_id)
    ).scalar_one_or_none()
    if membership is None:
        # Return 404 (never 403) so guessed team IDs do not leak team existence
        raise AppError(404, "TEAM_NOT_FOUND", "Team not found.")

    return team


def assert_team_write(user: User, team_id: str, db: Session) -> Team:
    """Verify the user can mutate data in `team_id`; non-members -> 404, Observers -> 403."""
    team = assert_team_read(user, team_id, db)
    if user.role == "observer":
        raise AppError(403, "FORBIDDEN", "Observers have read-only access.")
    return team


def require_team_read(
    team_id: str = Path(..., description="Target team ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamAccessContext:
    """FastAPI dependency enforcing team read access on `/teams/{team_id}/...` routes."""
    team = assert_team_read(user, team_id, db)
    return TeamAccessContext(user=user, team=team)


def require_team_write(
    team_id: str = Path(..., description="Target team ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamAccessContext:
    """FastAPI dependency enforcing team write access on `/teams/{team_id}/...` routes."""
    team = assert_team_write(user, team_id, db)
    return TeamAccessContext(user=user, team=team)


def list_accessible_teams(user: User, db: Session) -> list[Team]:
    """Return every team the user can access (all company teams for Admin)."""
    if user.role == "admin":
        stmt = select(Team).where(Team.company_id == user.company_id).order_by(Team.name.asc())
        return list(db.execute(stmt).scalars().all())

    stmt = (
        select(Team)
        .join(Membership, Membership.team_id == Team.id)
        .where(Membership.user_id == user.id, Team.company_id == user.company_id)
        .order_by(Team.name.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_eligible_team_owners(team_id: str, company_id: str, db: Session) -> list[User]:
    """Return eligible item owners for a team: (all company Admins) U (team's Team Members)."""
    member_subq = select(Membership.user_id).where(Membership.team_id == team_id)
    stmt = (
        select(User)
        .where(
            User.company_id == company_id,
            or_(
                User.role == "admin",
                (User.role == "team_member") & User.id.in_(member_subq),
            ),
        )
        .order_by(User.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def assert_eligible_team_owner(
    owner_id: str, team_id: str, company_id: str, db: Session
) -> User:
    """Validate that `owner_id` is an Admin or Team Member of `team_id`; else raise 422."""
    eligible = get_eligible_team_owners(team_id, company_id, db)
    for candidate in eligible:
        if candidate.id == owner_id:
            return candidate
    raise AppError(
        422,
        "VALIDATION_ERROR",
        "Owner must be a company Admin or a Team Member belonging to this team.",
        fields={"owner_id": "Selected user cannot own items on this team"},
    )
