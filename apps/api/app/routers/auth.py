"""Session authentication and seeded user switcher endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, list_accessible_teams
from app.auth.tokens import create_access_token
from app.clock import Clock, get_clock
from app.config import get_settings
from app.db import get_db
from app.dto import (
    ApiErrorResponse,
    ApiResponse,
    LoginRequestDto,
    LoginResponseDto,
    TeamDto,
    UserDto,
    UserListDto,
    UserWithTeamsDto,
    ok,
)
from app.errors import AppError
from app.models import User

router = APIRouter(tags=["Auth"])


def _build_user_with_teams(user: User, db: Session) -> UserWithTeamsDto:
    teams = list_accessible_teams(user, db)
    return UserWithTeamsDto(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,  # type: ignore[arg-type]
        teams=[TeamDto.model_validate(t) for t in teams],
    )


@router.get("/auth/users", response_model=ApiResponse[UserListDto])
def list_seeded_users(
    request: Request,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[UserListDto]:
    """List seeded personas for the header User Switcher."""
    users = db.execute(select(User).order_by(User.id.asc())).scalars().all()
    payload = UserListDto(items=[UserDto.model_validate(u) for u in users])
    return ok(payload, request=request, clock=clock)


@router.post(
    "/auth/login",
    response_model=ApiResponse[LoginResponseDto],
    responses={401: {"model": ApiErrorResponse}, 422: {"model": ApiErrorResponse}},
)
def login(
    request: Request,
    body: LoginRequestDto,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[LoginResponseDto]:
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
    payload = LoginResponseDto(access_token=token, user=_build_user_with_teams(user, db))
    return ok(payload, request=request, clock=clock)


@router.get(
    "/me",
    response_model=ApiResponse[UserWithTeamsDto],
    responses={401: {"model": ApiErrorResponse}},
)
def get_me(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[UserWithTeamsDto]:
    """Return the authenticated user's profile, role, and accessible teams."""
    return ok(_build_user_with_teams(user, db), request=request, clock=clock)
