"""Pure timezone, week/quarter bucketing, and exact Decimal half-up rounding utilities.

Zero FastAPI or SQLAlchemy imports. All calendar calculations run in the company
IANA timezone (default `America/Chicago`) so DST transitions (such as Nov 1, 2026)
are handled accurately.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE_NAME = "America/Chicago"
DEFAULT_TZ = ZoneInfo(DEFAULT_TIMEZONE_NAME)


def get_company_tz(timezone_name: str = DEFAULT_TIMEZONE_NAME) -> ZoneInfo:
    return ZoneInfo(timezone_name)


def today_in_tz(now: datetime, tz: ZoneInfo = DEFAULT_TZ) -> date:
    """Return today's calendar date in the company timezone."""
    if now.tzinfo is None:
        raise ValueError("`now` must be timezone-aware")
    return now.astimezone(tz).date()


def week_start_of_date(d: date) -> date:
    """Return the Monday (`week_start`) of the Monday-Sunday week containing `d`."""
    return d - timedelta(days=d.weekday())


def week_start_of(ts: datetime, tz: ZoneInfo = DEFAULT_TZ) -> date:
    """Return the Monday (`week_start`) in company time for UTC timestamp `ts`."""
    return week_start_of_date(today_in_tz(ts, tz))


def last_closed_week(now: datetime, tz: ZoneInfo = DEFAULT_TZ) -> date:
    """Return the Monday of the full Monday-Sunday week immediately before the current week."""
    return week_start_of(now, tz) - timedelta(weeks=1)


def last_13_weeks(now: datetime, tz: ZoneInfo = DEFAULT_TZ) -> list[date]:
    """Return 13 chronological Monday `week_start` dates ending with the current week."""
    current_week = week_start_of(now, tz)
    return [current_week - timedelta(weeks=offset) for offset in range(12, -1, -1)]


def quarter_of(d: date) -> str:
    """Return calendar quarter string (e.g., `2026-Q4`) for date `d`."""
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def format_week_label(week_start: date) -> str:
    """Format a week_start Monday as `<Mon D>` (e.g., `Nov 2`, `Oct 26`)."""
    return f"{week_start.strftime('%b')} {week_start.day}"


def round_half_up_percent(numerator: int, denominator: int) -> int:
    """Compute whole-number percentage using exact Decimal ROUND_HALF_UP (never banker's round)."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    pct = (Decimal(numerator) * Decimal(100)) / Decimal(denominator)
    return int(pct.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round_half_up_1dp(total: int | Decimal, count: int) -> float:
    """Compute average rounded to 1 decimal place using exact Decimal ROUND_HALF_UP."""
    if count <= 0:
        raise ValueError("count must be positive")
    avg = Decimal(total) / Decimal(count)
    return float(avg.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
