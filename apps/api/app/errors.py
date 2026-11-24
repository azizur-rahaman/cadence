"""Unified API error envelope (`ApiErrorResponse`) and FastAPI exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.clock import Clock, get_clock
from app.dto import ApiErrorResponse, ErrorDetailDto, build_meta
from app.middleware import REQUEST_ID_HEADER, get_request_id

STATUS_TO_CODE: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
}


class AppError(Exception):
    """Domain/API exception serialized to `ApiErrorResponse`."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields


def _resolve_clock(request: Request) -> Clock:
    provider = request.app.dependency_overrides.get(get_clock, get_clock)
    return provider()


def _error_json_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    fields: dict[str, str] | None = None,
) -> JSONResponse:
    clock = _resolve_clock(request)
    envelope = ApiErrorResponse(
        success=False,
        error=ErrorDetailDto(code=code, message=message, fields=fields),
        meta=build_meta(request, clock),
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(exclude_none=True),
        headers={REQUEST_ID_HEADER: get_request_id(request)},
    )


def _format_validation_fields(errors: list[Any]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for err in errors:
        loc = err.get("loc", ())
        parts = [str(part) for part in loc if part not in {"body", "query", "path"}]
        key = ".".join(parts) if parts else "body"
        fields[key] = str(err.get("msg", "Invalid value"))
    return fields


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global handlers ensuring every error returns `ApiErrorResponse`."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return _error_json_response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            fields=exc.fields,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_json_response(
            request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            fields=_format_validation_fields(list(exc.errors())),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = STATUS_TO_CODE.get(exc.status_code, f"HTTP_{exc.status_code}")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _error_json_response(
            request,
            status_code=exc.status_code,
            code=code,
            message=message,
        )
