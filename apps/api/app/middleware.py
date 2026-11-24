"""Request correlation middleware attaching `X-Request-Id` to every request and response."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-Id"


def generate_request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def get_request_id(request: Request) -> str:
    req_id = getattr(request.state, "request_id", None)
    if isinstance(req_id, str) and req_id:
        return req_id
    req_id = generate_request_id()
    request.state.request_id = req_id
    return req_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Propagates or generates a correlation `X-Request-Id` header on every HTTP response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "").strip()
        request_id = incoming[:64] if incoming else generate_request_id()
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
