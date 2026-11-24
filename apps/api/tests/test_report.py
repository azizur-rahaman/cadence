"""Integration tests for the rules report builder and CLI at default and alternate APP_NOW dates."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.cli.report import generate_rules_report_from_db


def test_rules_report_default_app_now_matches_ground_truth(seeded_db: Session) -> None:
    app_now = datetime(2026, 11, 11, 15, 0, tzinfo=UTC)
    report = generate_rules_report_from_db(seeded_db, now=app_now)

    assert report["now"] == "2026-11-11T15:00:00Z"
    assert sorted(report["teams"].keys()) == ["team_lead", "team_ops", "team_sales"]

    lead = report["teams"]["team_lead"]
    # 13-week window: Aug 17 through Nov 9
    m1_weeks = list(lead["measurable_status"]["m1"].keys())
    assert len(m1_weeks) == 13
    assert m1_weeks[0] == "2026-08-17"
    assert m1_weeks[-1] == "2026-11-09"

    # Current week: m1..m4 pending, m5 has score 520 -> on_track
    for mid in ("m1", "m2", "m3", "m4"):
        assert lead["measurable_status"][mid]["2026-11-09"] == "pending"
    assert lead["measurable_status"]["m5"]["2026-11-09"] == "on_track"
    assert lead["measurable_status"]["m5"]["2026-10-19"] == "off_track"
    assert lead["measurable_status"]["m5"]["2026-11-02"] == "off_track"

    # Boundary scores
    assert lead["measurable_status"]["m2"]["2026-09-07"] == "on_track"
    assert lead["measurable_status"]["m3"]["2026-08-24"] == "on_track"
    assert lead["measurable_status"]["m3"]["2026-08-31"] == "on_track"
    assert lead["measurable_status"]["m3"]["2026-09-07"] == "off_track"
    assert lead["measurable_status"]["m4"]["2026-08-31"] == "off_track"
    assert lead["measurable_status"]["m4"]["2026-09-21"] == "off_track"

    # To-Do completion including DST boundaries & exact 90%
    tc = lead["todo_completion"]
    assert len(tc) == 13
    assert tc["2026-09-14"] == {"due": 2, "done": 2, "rate_percent": 100, "meets_target": True}
    assert tc["2026-10-26"] == {"due": 3, "done": 2, "rate_percent": 67, "meets_target": False}
    assert tc["2026-11-02"] == {"due": 10, "done": 9, "rate_percent": 90, "meets_target": True}
    assert tc["2026-11-09"] == {"due": 3, "done": 0, "rate_percent": 0, "meets_target": False}
    null_weeks = [w for w, val in tc.items() if val is None]
    assert len(null_weeks) == 9

    assert lead["overdue_todos"] == ["t12", "t31"]

    # Rocks
    assert lead["rocks"] == {
        "r1": {"status": "on_track", "progress_percent": 33},
        "r2": {"status": "off_track", "progress_percent": 13},
        "r3": {"status": "complete", "progress_percent": 100},
        "r4": {"status": "off_track", "progress_percent": 0},
        "r5": {"status": "on_track", "progress_percent": 0},
    }

    # Issues
    assert lead["issue_order"] == ["i2", "i1", "i5", "i3", "i4"]

    # Seeded ended meetings
    assert lead["meetings"]["mt1"] == {
        "scorecard_week": "2026-10-19",
        "measurable_status": {
            "m1": "on_track",
            "m2": "on_track",
            "m3": "on_track",
            "m4": "on_track",
            "m5": "off_track",
        },
        "issues_solved": ["i7"],
        "todos_created": ["t20"],
        "attendee_ids": ["u1", "u2", "u3", "u4", "u5"],
        "rating": 8.0,
    }
    assert lead["meetings"]["mt2"] == {
        "scorecard_week": "2026-10-26",
        "measurable_status": {
            "m1": "off_track",
            "m2": "on_track",
            "m3": "on_track",
            "m4": "off_track",
            "m5": "on_track",
        },
        "issues_solved": ["i6"],
        "todos_created": ["t30"],
        "attendee_ids": ["u1", "u2", "u3", "u4", "u5"],
        "rating": 8.3,
    }

    # team_sales & team_ops
    sales = report["teams"]["team_sales"]
    assert sales["todo_completion"]["2026-11-09"] == {
        "due": 1,
        "done": 0,
        "rate_percent": 0,
        "meets_target": False,
    }
    assert sum(1 for v in sales["todo_completion"].values() if v is None) == 12
    assert sales["overdue_todos"] == []
    assert sales["rocks"] == {"r6": {"status": "on_track", "progress_percent": 0}}
    assert sales["issue_order"] == ["i8"]
    assert sales["meetings"] == {}

    ops = report["teams"]["team_ops"]
    assert ops["todo_completion"]["2026-11-02"] == {
        "due": 1,
        "done": 1,
        "rate_percent": 100,
        "meets_target": True,
    }
    assert sum(1 for v in ops["todo_completion"].values() if v is None) == 12
    assert ops["overdue_todos"] == []
    assert ops["rocks"] == {"r7": {"status": "on_track", "progress_percent": 0}}
    assert ops["issue_order"] == ["i9"]
    assert ops["meetings"] == {}


def test_rules_report_alternate_dates_recompute_dynamically(seeded_db: Session) -> None:
    # One day later: 2026-11-12 -> t30 overdue, r1 flips to off_track (ms2 past due)
    next_day = generate_rules_report_from_db(
        seeded_db, now=datetime(2026, 11, 12, 15, 0, tzinfo=UTC)
    )
    assert next_day["now"] == "2026-11-12T15:00:00Z"
    assert next_day["teams"]["team_lead"]["overdue_todos"] == ["t12", "t30", "t31"]
    assert next_day["teams"]["team_lead"]["rocks"]["r1"] == {
        "status": "off_track",
        "progress_percent": 33,
    }
    assert next_day["teams"]["team_sales"]["overdue_todos"] == []

    # Next Monday: 2026-11-16 -> 13-week window shifts; 2026-11-09 closes; t32 & t40 overdue
    next_week = generate_rules_report_from_db(
        seeded_db, now=datetime(2026, 11, 16, 15, 0, tzinfo=UTC)
    )
    lead_weeks = list(next_week["teams"]["team_lead"]["measurable_status"]["m1"].keys())
    assert lead_weeks[0] == "2026-08-24"
    assert lead_weeks[-1] == "2026-11-16"
    lead_ms = next_week["teams"]["team_lead"]["measurable_status"]
    for mid in ("m1", "m2", "m3", "m4"):
        assert lead_ms[mid]["2026-11-09"] == "off_track"
        assert lead_ms[mid]["2026-11-16"] == "pending"
    assert lead_ms["m5"]["2026-11-09"] == "on_track"
    assert lead_ms["m5"]["2026-11-16"] == "pending"
    assert next_week["teams"]["team_lead"]["overdue_todos"] == ["t12", "t30", "t31", "t32"]
    assert next_week["teams"]["team_sales"]["overdue_todos"] == ["t40"]


def test_rules_report_cli_prints_clean_unwrapped_json(seeded_db: Session) -> None:
    env = os.environ.copy()
    env["APP_NOW"] = "2026-11-12T15:00:00Z"
    env["CLOCK_MODE"] = "frozen"

    proc = subprocess.run(
        [sys.executable, "-m", "app.cli.report"],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    payload = json.loads(proc.stdout)
    assert payload["now"] == "2026-11-12T15:00:00Z"
    assert payload["teams"]["team_lead"]["overdue_todos"] == ["t12", "t30", "t31"]
    assert payload["teams"]["team_lead"]["rocks"]["r1"]["status"] == "off_track"
