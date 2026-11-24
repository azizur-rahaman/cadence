"""Common API schemas (unified error envelope)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., examples=["VALIDATION_ERROR"])
    message: str = Field(..., examples=["Request validation failed."])
    fields: dict[str, str] | None = Field(
        default=None, examples=[{"resolution_note": "Must not be empty"}]
    )
