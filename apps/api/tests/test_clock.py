"""Tests for deterministic Clock service, health endpoint, and wall-clock lint invariant."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clock import FrozenClock, LiveClock, format_utc_iso, get_clock, parse_utc_iso
from app.main import create_app


def test_parse_and_format_utc_iso() -> None:
    dt = parse_utc_iso("2026-11-11T15:00:00Z")
    assert dt == datetime(2026, 11, 11, 15, 0, 0, tzinfo=UTC)
    assert format_utc_iso(dt) == "2026-11-11T15:00:00Z"


def test_parse_utc_iso_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone"):
        parse_utc_iso("2026-11-11T15:00:00")


def test_frozen_clock_stays_fixed_and_advances_manually() -> None:
    clock = FrozenClock("2026-11-11T15:00:00Z")
    assert format_utc_iso(clock.now()) == "2026-11-11T15:00:00Z"
    assert clock.now() == clock.app_now

    clock.advance(seconds=305)
    assert format_utc_iso(clock.now()) == "2026-11-11T15:05:05Z"

    clock.set_now("2026-11-16T15:00:00Z")
    assert format_utc_iso(clock.now()) == "2026-11-16T15:00:00Z"


def test_live_clock_adds_monotonic_elapsed_seconds() -> None:
    fake_ticks = iter([100.0, 100.0, 142.5])
    clock = LiveClock("2026-11-11T15:00:00Z", monotonic_fn=lambda: next(fake_ticks))
    assert clock.now() == datetime(2026, 11, 11, 15, 0, 0, tzinfo=UTC)
    assert clock.now() == datetime(2026, 11, 11, 15, 0, 42, 500000, tzinfo=UTC)


def test_health_endpoint_uses_injected_clock() -> None:
    app = create_app()
    frozen = FrozenClock("2026-11-11T15:00:00Z")
    app.dependency_overrides[get_clock] = lambda: frozen

    client = TestClient(app)
    res = client.get("/api/health", headers={"X-Request-Id": "req_health_01"})
    assert res.status_code == 200
    assert res.headers["X-Request-Id"] == "req_health_01"
    assert res.json() == {
        "success": True,
        "data": {
            "status": "ok",
            "now": "2026-11-11T15:00:00Z",
            "app_now": "2026-11-11T15:00:00Z",
        },
        "meta": {
            "request_id": "req_health_01",
            "timestamp": "2026-11-11T15:00:00Z",
        },
    }

    frozen.advance(seconds=60)
    res2 = client.get("/api/health")
    body2 = res2.json()
    assert body2["success"] is True
    assert body2["data"]["now"] == "2026-11-11T15:01:00Z"
    assert body2["meta"]["timestamp"] == "2026-11-11T15:01:00Z"
    assert body2["meta"]["request_id"] == res2.headers["X-Request-Id"]


def test_no_wall_clock_calls_outside_clock_module() -> None:
    """Enforce AGENTS.md invariant: zero datetime.now/utcnow or date.today calls."""
    app_dir = Path(__file__).resolve().parent.parent / "app"
    forbidden = {("datetime", "now"), ("datetime", "utcnow"), ("date", "today")}
    violations: list[str] = []

    for py_file in sorted(app_dir.rglob("*.py")):
        if py_file.name == "clock.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    pair = (node.func.value.id, node.func.attr)
                    if pair in forbidden:
                        rel = py_file.relative_to(app_dir)
                        violations.append(f"{rel}:{node.lineno} calls {pair[0]}.{pair[1]}()")

    assert violations == [], f"Forbidden wall-clock calls found: {violations}"
