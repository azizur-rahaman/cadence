"""API Data Transfer Objects (DTOs) and standard response envelopes."""

from app.dto.auth import (
    HealthDto,
    LoginRequestDto,
    LoginResponseDto,
    RoleType,
    TeamDto,
    TeamListDto,
    UserDto,
    UserListDto,
    UserWithTeamsDto,
)
from app.dto.envelope import (
    ApiErrorResponse,
    ApiResponse,
    ErrorDetailDto,
    ResponseMetaDto,
    build_meta,
    ok,
)

__all__ = [
    "ApiErrorResponse",
    "ApiResponse",
    "ErrorDetailDto",
    "HealthDto",
    "LoginRequestDto",
    "LoginResponseDto",
    "ResponseMetaDto",
    "RoleType",
    "TeamDto",
    "TeamListDto",
    "UserDto",
    "UserListDto",
    "UserWithTeamsDto",
    "build_meta",
    "ok",
]
