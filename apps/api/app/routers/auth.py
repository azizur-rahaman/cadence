"""Session authentication and seeded user switcher endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, list_accessible_teams
from app.auth.tokens import create_access_token
from app.clock import Clock, get_clock
from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.models import User
from app.schemas import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    TeamOut,
    UserOut,
    UserWithTeamsOut,
)

router = APIRouter(tags=["Auth"])


def _build_user_with_teams(user: User, db: Session) -> UserWithTeamsOut:
    teams = list_accessible_teams(user, db)
    return UserWithTeamsOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,  # type: ignore[arg-type]
        teams=[TeamOut.model_validate(t) for t in teams],
    )


@router.get("/auth/users", response_model=list[UserOut])
def list_seeded_users(db: Session = Depends(get_db)) -> list[UserOut]:
    """List seeded personas for the header User Switcher."""
    users = db.execute(select(User).order_by(User.id.asc())).scalars().all()
    return [UserOut.model_validate(u) for u in users]


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> LoginResponse:
    """Sign in as a seeded user by `user_id` or case-insensitive `email`."""
    user: User | None = None
    if body.user_id is not None:
        user = db.get(User, body.user_id)
    elif body.email is not None:
        user = db.execute(
            select(User).where(func.lower(User.email) == body.email.lower())
        ).scalar_one_or_none()

    if user is None:
        raise AppError(401, "INVALID_CREDENTIALS", "Unknown user.")

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        secret=get_settings().auth_secret,
        issued_at=clock.now(),
    )
    return LoginResponse(access_token=token, user=_build_user_with_teams(user, db))


@router.get(
    "/me",
    response_model=UserWithTeamsOut,
    responses={401: {"model": ErrorResponse}},
)
def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserWithTeamsOut:
    """Return the authenticated user's profile, role, and accessible teams."""
    return _build_user_with_teams(user, db)
