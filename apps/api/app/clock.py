"""Deterministic Clock service driven by APP_NOW.

This is the single module allowed to compute 'now' in the application.
Live API processes use LiveClock (APP_NOW + monotonic elapsed seconds) so
meeting timers advance smoothly while starting deterministically. The rules
report CLI and automated tests use FrozenClock (zero elapsed offset).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.config import get_settings


def parse_utc_iso(value: str) -> datetime:
    """Parse an ISO 8601 UTC timestamp string into a timezone-aware UTC datetime."""
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include a timezone offset: {value!r}")
    return parsed.astimezone(UTC)


def format_utc_iso(dt: datetime) -> str:
    """Format a timezone-aware datetime as canonical ISO 8601 UTC (trailing Z)."""
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")
    utc_dt = dt.astimezone(UTC).replace(microsecond=0)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _coerce_utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        return parse_utc_iso(value)
    return value.astimezone(UTC)


class Clock(Protocol):
    """Protocol for deterministic application clocks."""

    @property
    def app_now(self) -> datetime: ...

    def now(self) -> datetime: ...


class FrozenClock:
    """Deterministic clock pinned to APP_NOW with zero wall-clock drift.

    Supports manual advancement in tests via `advance(seconds=...)`.
    """

    def __init__(self, app_now: datetime | str) -> None:
        self._app_now = _coerce_utc(app_now)
        self._offset = timedelta(0)

    @property
    def app_now(self) -> datetime:
        return self._app_now

    def now(self) -> datetime:
        return self._app_now + self._offset

    def advance(self, seconds: float) -> datetime:
        self._offset += timedelta(seconds=seconds)
        return self.now()

    def set_now(self, new_now: datetime | str) -> datetime:
        target = _coerce_utc(new_now)
        self._offset = target - self._app_now
        return self.now()


class LiveClock:
    """Ticking deterministic clock: APP_NOW + monotonic elapsed time since creation."""

    def __init__(
        self,
        app_now: datetime | str,
        monotonic_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self._app_now = _coerce_utc(app_now)
        self._monotonic = monotonic_fn
        self._started_at = self._monotonic()

    @property
    def app_now(self) -> datetime:
        return self._app_now

    def now(self) -> datetime:
        elapsed = max(0.0, self._monotonic() - self._started_at)
        return self._app_now + timedelta(seconds=elapsed)


_default_clock: Clock | None = None


def create_clock_from_settings() -> Clock:
    settings = get_settings()
    if settings.clock_mode == "frozen":
        return FrozenClock(settings.app_now)
    return LiveClock(settings.app_now)


def get_clock() -> Clock:
    """FastAPI dependency returning the process-wide deterministic clock."""
    global _default_clock
    if _default_clock is None:
        _default_clock = create_clock_from_settings()
    return _default_clock


def reset_default_clock(clock: Clock | None = None) -> None:
    """Reset the process-wide default clock (used by tests)."""
    global _default_clock
    _default_clock = clock
