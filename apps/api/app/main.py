"""FastAPI entrypoint for Cadence (Level 10)."""

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.clock import Clock, format_utc_iso, get_clock
from app.config import get_settings
from app.dto import ApiResponse, HealthDto, ok
from app.errors import register_exception_handlers
from app.middleware import RequestIdMiddleware
from app.routers import auth, issues, scorecard, teams, todos


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Cadence (Level 10) API",
        version="0.1.0",
        description="Weekly Team Meeting Platform (EOS / Level 10) REST & WebSocket API",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    register_exception_handlers(app)

    @app.get("/api/health", response_model=ApiResponse[HealthDto], tags=["System"])
    def health(
        request: Request, clock: Clock = Depends(get_clock)
    ) -> ApiResponse[HealthDto]:
        return ok(
            HealthDto(
                status="ok",
                now=format_utc_iso(clock.now()),
                app_now=settings.app_now,
            ),
            request=request,
            clock=clock,
        )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(teams.router, prefix="/api/v1")
    app.include_router(scorecard.router, prefix="/api/v1")
    app.include_router(issues.router, prefix="/api/v1")
    app.include_router(todos.router, prefix="/api/v1")

    return app


app = create_app()
