"""Exhaustive unit & boundary tests for the pure-Python business rules engine (E10-S1)."""

from __future__ import annotations

import ast
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from app.rules import (
    DEFAULT_TZ,
    IssueRecord,
    MeasurableGoal,
    MilestoneRecord,
    RockRecord,
    TodoRecord,
    compute_meeting_rating,
    compute_meeting_scorecard_week,
    compute_timer_state,
    compute_todo_completion_for_week,
    evaluate_measurable_status,
    evaluate_rock,
    format_issue_title_from_measurable,
    is_todo_done_on_time,
    is_todo_overdue,
    last_13_weeks,
    last_closed_week,
    ordered_unsolved_issue_ids,
    overdue_todo_ids,
    quarter_of,
    round_half_up_1dp,
    round_half_up_percent,
    today_in_tz,
    week_start_of,
)


def test_rules_package_has_zero_fastapi_or_sqlalchemy_imports() -> None:
    """Enforce AGENTS.md invariant: app/rules/ must remain 100% pure Python."""
    rules_dir = Path(__file__).resolve().parent.parent / "app" / "rules"
    forbidden_roots = {"fastapi", "starlette", "sqlalchemy", "alembic", "psycopg"}
    violations: list[str] = []

    for py_file in sorted(rules_dir.rglob("*.py")):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in forbidden_roots:
                        violations.append(f"{py_file.name}:{node.lineno} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in forbidden_roots:
                    violations.append(f"{py_file.name}:{node.lineno} imports from {node.module}")

    assert violations == [], f"Non-pure imports found in app/rules/: {violations}"


def test_time_utils_dst_week_boundaries_and_13_week_window() -> None:
    app_now = datetime(2026, 11, 11, 15, 0, tzinfo=UTC)
    assert today_in_tz(app_now, DEFAULT_TZ) == date(2026, 11, 11)
    assert quarter_of(date(2026, 11, 11)) == "2026-Q4"
    assert quarter_of(date(2026, 1, 1)) == "2026-Q1"
    assert quarter_of(date(2026, 6, 30)) == "2026-Q2"
    assert quarter_of(date(2026, 7, 1)) == "2026-Q3"

    assert last_closed_week(app_now, DEFAULT_TZ) == date(2026, 11, 2)
    weeks = last_13_weeks(app_now, DEFAULT_TZ)
    assert len(weeks) == 13
    assert weeks[0] == date(2026, 8, 17)
    assert weeks[-1] == date(2026, 11, 9)

    # DST ended Sunday Nov 1, 2026 at 02:00 local (CDT UTC-5 -> CST UTC-6)
    # t11: 2026-11-02T05:30:00Z = Sun Nov 1 23:30 CST -> still week of Oct 26
    t11_ws = week_start_of(datetime(2026, 11, 2, 5, 30, tzinfo=UTC), DEFAULT_TZ)
    assert t11_ws == date(2026, 10, 26)
    # Mon Nov 2 00:00 CST = 2026-11-02T06:00:00Z -> week of Nov 2
    mon_ws = week_start_of(datetime(2026, 11, 2, 6, 0, tzinfo=UTC), DEFAULT_TZ)
    assert mon_ws == date(2026, 11, 2)
    # t28: 2026-11-09T05:59:00Z = Sun Nov 8 23:59 CST -> still week of Nov 2
    t28_ws = week_start_of(datetime(2026, 11, 9, 5, 59, tzinfo=UTC), DEFAULT_TZ)
    assert t28_ws == date(2026, 11, 2)
    # t29: 2026-11-09T06:01:00Z = Mon Nov 9 00:01 CST -> week of Nov 9 (late for Nov 2!)
    t29_ws = week_start_of(datetime(2026, 11, 9, 6, 1, tzinfo=UTC), DEFAULT_TZ)
    assert t29_ws == date(2026, 11, 9)


def test_half_up_rounding_avoids_bankers_rounding() -> None:
    # 1/8 = 12.5% -> 13% (Python round(12.5) would wrongly return 12)
    assert round_half_up_percent(1, 8) == 13
    assert round_half_up_percent(2, 3) == 67
    assert round_half_up_percent(1, 3) == 33
    # 33/4 = 8.25 -> 8.3 (Python round(8.25, 1) would wrongly return 8.2)
    assert round_half_up_1dp(33, 4) == 8.3
    assert round_half_up_1dp(24, 3) == 8.0


def test_measurable_status_all_goal_types_and_missing_scores() -> None:
    curr = date(2026, 11, 9)
    closed = date(2026, 11, 2)
    ev = evaluate_measurable_status

    g_at_least = MeasurableGoal("at_least", value=Decimal("10"))
    assert ev(g_at_least, Decimal("10"), week_start=closed, current_week_start=curr) == "on_track"
    assert (
        ev(g_at_least, Decimal("9.99"), week_start=closed, current_week_start=curr) == "off_track"
    )

    # m2 boundary: 3.0 against at_most 3.0 -> on_track
    g_at_most = MeasurableGoal("at_most", value=Decimal("3.0"))
    assert ev(g_at_most, Decimal("3.0"), week_start=closed, current_week_start=curr) == "on_track"
    assert ev(g_at_most, Decimal("3.1"), week_start=closed, current_week_start=curr) == "off_track"

    # m3 boundaries: 2 and 4 against between 2..4 -> on_track; 1.8 & 4.5 -> off_track
    g_between = MeasurableGoal("between", min_value=Decimal("2"), max_value=Decimal("4"))
    assert ev(g_between, Decimal("2"), week_start=closed, current_week_start=curr) == "on_track"
    assert ev(g_between, Decimal("4"), week_start=closed, current_week_start=curr) == "on_track"
    assert ev(g_between, Decimal("1.8"), week_start=closed, current_week_start=curr) == "off_track"
    assert ev(g_between, Decimal("4.5"), week_start=closed, current_week_start=curr) == "off_track"

    # m4 exactly 1: 0 and 2 -> off_track
    g_exactly = MeasurableGoal("exactly", value=Decimal("1"))
    assert ev(g_exactly, Decimal("1"), week_start=closed, current_week_start=curr) == "on_track"
    assert ev(g_exactly, Decimal("0"), week_start=closed, current_week_start=curr) == "off_track"
    assert ev(g_exactly, Decimal("2"), week_start=closed, current_week_start=curr) == "off_track"

    # Missing closed -> off_track; missing current -> pending; present current -> evaluated
    g_cash = MeasurableGoal("at_least", value=Decimal("500"))
    assert ev(g_cash, None, week_start=closed, current_week_start=curr) == "off_track"
    assert ev(g_cash, None, week_start=curr, current_week_start=curr) == "pending"
    assert ev(g_cash, Decimal("520"), week_start=curr, current_week_start=curr) == "on_track"

    assert format_issue_title_from_measurable("New deals closed", date(2026, 11, 2)) == (
        "New deals closed, week of Nov 2"
    )


def test_todo_completion_dst_edges_exact_90_target_and_overdue() -> None:
    t11 = TodoRecord("t11", date(2026, 10, 30), datetime(2026, 11, 2, 5, 30, tzinfo=UTC))
    t28 = TodoRecord("t28", date(2026, 11, 6), datetime(2026, 11, 9, 5, 59, tzinfo=UTC))
    t29 = TodoRecord("t29", date(2026, 11, 8), datetime(2026, 11, 9, 6, 1, tzinfo=UTC))
    assert is_todo_done_on_time(t11) is True
    assert is_todo_done_on_time(t28) is True
    assert is_todo_done_on_time(t29) is False

    # Seed team_lead week 2026-11-02: 9 of 10 done on time = exact 90% -> meets_target=True
    nov2_todos = [
        TodoRecord(f"t2{i}", date(2026, 11, 4), datetime(2026, 11, 4, 18, 0, tzinfo=UTC))
        for i in range(8)
    ] + [t28, t29]
    res_90 = compute_todo_completion_for_week(nov2_todos, date(2026, 11, 2))
    assert res_90 is not None
    assert res_90.to_dict() == {"due": 10, "done": 9, "rate_percent": 90, "meets_target": True}

    # Exact ratio trap: 26/29 = 89.655% rounds to 90%, MUST have meets_target=False!
    tricky = [
        TodoRecord(f"ok_{i}", date(2026, 11, 4), datetime(2026, 11, 4, 18, 0, tzinfo=UTC))
        for i in range(26)
    ] + [TodoRecord(f"miss_{i}", date(2026, 11, 4), None) for i in range(3)]
    res_tricky = compute_todo_completion_for_week(tricky, date(2026, 11, 2))
    assert res_tricky is not None
    assert res_tricky.rate_percent == 90
    assert res_tricky.meets_target is False

    # Zero due -> None
    assert compute_todo_completion_for_week(nov2_todos, date(2026, 8, 17)) is None

    # Current week with 3 undone todos -> non-null 0%
    curr_todos = [
        TodoRecord("t30", date(2026, 11, 11), None),
        TodoRecord("t31", date(2026, 11, 10), None),
        TodoRecord("t32", date(2026, 11, 13), None),
        TodoRecord("t12", date(2026, 11, 1), None),
    ]
    res_curr = compute_todo_completion_for_week(curr_todos, date(2026, 11, 9))
    assert res_curr is not None
    assert res_curr.to_dict() == {"due": 3, "done": 0, "rate_percent": 0, "meets_target": False}

    # Overdue check on Nov 11 vs Nov 12
    assert is_todo_overdue(curr_todos[0], today=date(2026, 11, 11)) is False
    assert overdue_todo_ids(curr_todos, today=date(2026, 11, 11)) == ["t12", "t31"]
    assert overdue_todo_ids(curr_todos, today=date(2026, 11, 12)) == ["t12", "t30", "t31"]


def test_rocks_status_and_progress_all_edge_cases() -> None:
    today = date(2026, 11, 11)

    # r1: ms2 due today -> NOT past due -> on_track, 1/3 = 33%
    r1 = RockRecord(
        "r1",
        "2026-Q4",
        "on_track",
        [
            MilestoneRecord("ms1", date(2026, 10, 15), True),
            MilestoneRecord("ms2", date(2026, 11, 11), False),
            MilestoneRecord("ms3", date(2026, 12, 1), False),
        ],
    )
    assert evaluate_rock(r1, today=today).to_dict() == {
        "status": "on_track",
        "progress_percent": 33,
    }
    # Next day (Nov 12): ms2 becomes past due -> r1 flips to off_track
    assert evaluate_rock(r1, today=date(2026, 11, 12)).status == "off_track"

    # r2: ms5 due Nov 10 -> past due -> off_track; 1/8 = 12.5% -> 13%
    r2 = RockRecord(
        "r2",
        "2026-Q4",
        "on_track",
        [MilestoneRecord("ms4", date(2026, 10, 10), True)]
        + [MilestoneRecord("ms5", date(2026, 11, 10), False)]
        + [MilestoneRecord(f"ms{i}", date(2026, 12, i), False) for i in range(6, 12)],
    )
    assert evaluate_rock(r2, today=today).to_dict() == {
        "status": "off_track",
        "progress_percent": 13,
    }

    # Zero-milestone rocks: complete -> 100%, off_track/on_track -> 0%
    r3 = RockRecord("r3", "2026-Q4", "complete", [])
    r4 = RockRecord("r4", "2026-Q4", "off_track", [])
    r5 = RockRecord("r5", "2026-Q4", "on_track", [])
    assert evaluate_rock(r3, today=today).to_dict() == {
        "status": "complete",
        "progress_percent": 100,
    }
    assert evaluate_rock(r4, today=today).to_dict() == {
        "status": "off_track",
        "progress_percent": 0,
    }
    assert evaluate_rock(r5, today=today).to_dict() == {
        "status": "on_track",
        "progress_percent": 0,
    }


def test_issue_order_priority_ties_null_last_and_excludes_solved() -> None:
    issues = [
        IssueRecord("i1", 5, datetime(2026, 10, 20, 14, 0, tzinfo=UTC), None),
        IssueRecord("i2", 5, datetime(2026, 10, 14, 16, 0, tzinfo=UTC), None),
        IssueRecord("i3", 3, datetime(2026, 10, 5, 15, 0, tzinfo=UTC), None),
        IssueRecord("i4", None, datetime(2026, 9, 1, 15, 0, tzinfo=UTC), None),
        IssueRecord("i5", 4, datetime(2026, 11, 9, 16, 0, tzinfo=UTC), None),
        IssueRecord(
            "i6",
            2,
            datetime(2026, 11, 3, 14, 0, tzinfo=UTC),
            datetime(2026, 11, 4, 15, 40, tzinfo=UTC),
        ),
    ]
    assert ordered_unsolved_issue_ids(issues) == ["i2", "i1", "i5", "i3", "i4"]


def test_meeting_rating_scorecard_week_and_timer_overrun() -> None:
    assert compute_meeting_rating([8, 9, 7]) == 8.0
    assert compute_meeting_rating([8, 9, 8, 8]) == 8.3
    assert compute_meeting_rating([]) is None

    assert compute_meeting_scorecard_week(datetime(2026, 10, 28, 15, 0, tzinfo=UTC)) == date(
        2026, 10, 19
    )
    assert compute_meeting_scorecard_week(datetime(2026, 11, 4, 15, 0, tzinfo=UTC)) == date(
        2026, 10, 26
    )

    started = datetime(2026, 11, 11, 15, 0, 0, tzinfo=UTC)
    mid = compute_timer_state("scorecard", started, datetime(2026, 11, 11, 15, 2, 0, tzinfo=UTC))
    assert mid.allotted_seconds == 300
    assert mid.remaining_seconds == 180
    assert mid.over_time is False

    over = compute_timer_state("scorecard", started, datetime(2026, 11, 11, 15, 5, 5, tzinfo=UTC))
    assert over.remaining_seconds == -5
    assert over.over_time is True
