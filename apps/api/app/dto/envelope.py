"""Standard generic API response & error envelope DTOs."""

from __future__ import annotations

from typing import Literal

from fastapi import Request
from pydantic import BaseModel, Field

from app.clock import Clock, format_utc_iso
from app.middleware import get_request_id


class ResponseMetaDto(BaseModel):
    request_id: str = Field(..., examples=["req_a1b2c3d4e5f6"])
    timestamp: str = Field(..., examples=["2026-11-11T15:00:00Z"])


class ApiResponse[T](BaseModel):
    """Standard success envelope wrapping every 2xx REST DTO payload."""

    success: Literal[True] = True
    data: T
    meta: ResponseMetaDto


class ErrorDetailDto(BaseModel):
    code: str = Field(..., examples=["VALIDATION_ERROR"])
    message: str = Field(..., examples=["Request validation failed."])
    fields: dict[str, str] | None = Field(
        default=None, examples=[{"resolution_note": "Must not be empty"}]
    )


class ApiErrorResponse(BaseModel):
    """Standard error envelope returned for every 4xx/5xx REST response."""

    success: Literal[False] = False
    error: ErrorDetailDto
    meta: ResponseMetaDto


def build_meta(request: Request, clock: Clock) -> ResponseMetaDto:
    return ResponseMetaDto(
        request_id=get_request_id(request),
        timestamp=format_utc_iso(clock.now()),
    )


def ok[T](data: T, *, request: Request, clock: Clock) -> ApiResponse[T]:
    """Wrap any typed DTO in the standard `ApiResponse[T]` envelope."""
    return ApiResponse(success=True, data=data, meta=build_meta(request, clock))
