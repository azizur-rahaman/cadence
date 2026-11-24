"""Database integrity tests proving PostgreSQL enforces all CHECK & partial unique constraints."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cli.seed import seed_database
from app.models import (
    Issue,
    Measurable,
    Meeting,
    MeetingRating,
    MeetingSummary,
    Score,
    Todo,
    User,
)


def test_idempotent_seed_counts_and_derived_meeting_summaries(seeded_db: Session) -> None:
    expected = {
        "companies": 1,
        "teams": 3,
        "users": 9,
        "memberships": 11,
        "measurables": 7,
        "scores": 83,
        "rocks": 7,
        "milestones": 12,
        "issues": 9,
        "todos": 20,
        "meetings": 2,
        "meeting_attendees": 10,
        "meeting_ratings": 7,
        "meeting_summaries": 2,
    }

    # Re-run seed a second time and verify identical counts
    counts_second_run = seed_database(seeded_db)
    assert counts_second_run == expected

    # Verify mt1 & mt2 derived summaries match seed.json ground truth
    mt1 = seeded_db.execute(
        select(MeetingSummary).where(MeetingSummary.meeting_id == "mt1")
    ).scalar_one()
    assert mt1.snapshot == {
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

    mt2 = seeded_db.execute(
        select(MeetingSummary).where(MeetingSummary.meeting_id == "mt2")
    ).scalar_one()
    assert mt2.snapshot == {
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


def test_db_rejects_invalid_user_role(seeded_db: Session) -> None:
    seeded_db.add(
        User(
            id="u_bad",
            company_id="co_1",
            name="Bad Role",
            email="bad@acme.test",
            role="superadmin",
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


def test_db_rejects_invalid_measurable_goal_shape(seeded_db: Session) -> None:
    seeded_db.add(
        Measurable(
            id="m_bad",
            team_id="team_lead",
            name="Broken Goal",
            owner_id="u2",
            unit="count",
            goal_type="between",
            goal_value=None,
            goal_min=Decimal("10"),
            goal_max=Decimal("5"),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


def test_db_rejects_duplicate_score_for_measurable_week(seeded_db: Session) -> None:
    seeded_db.add(Score(measurable_id="m1", week_start=date(2026, 11, 2), value=Decimal("99")))
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


@pytest.mark.parametrize("bad_priority", [0, 6])
def test_db_rejects_issue_priority_out_of_range(seeded_db: Session, bad_priority: int) -> None:
    seeded_db.add(
        Issue(
            id=f"i_bad_{bad_priority}",
            team_id="team_lead",
            title="Bad priority",
            owner_id="u2",
            priority=bad_priority,
            created_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


def test_db_rejects_blank_issue_title_and_solved_without_note(seeded_db: Session) -> None:
    seeded_db.add(
        Issue(
            id="i_blank",
            team_id="team_lead",
            title="   ",
            owner_id="u2",
            created_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()

    seeded_db.add(
        Issue(
            id="i_no_note",
            team_id="team_lead",
            title="Solved with blank note",
            owner_id="u2",
            created_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
            solved_at=datetime(2026, 11, 11, 15, 5, tzinfo=UTC),
            resolution_note="   ",
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


def test_partial_unique_index_blocks_duplicate_unsolved_source_issue_but_allows_after_solved(
    seeded_db: Session,
) -> None:
    # i5 is ALREADY unsolved for (m1, 2026-11-02) -> must be rejected by Postgres
    seeded_db.add(
        Issue(
            id="i_dup_m1",
            team_id="team_lead",
            title="Duplicate m1 Nov 2",
            owner_id="u2",
            created_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
            source_measurable_id="m1",
            source_week_start=date(2026, 11, 2),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()

    # i6 is SOLVED for (m4, 2026-10-26) -> new unsolved Issue MUST be allowed
    seeded_db.add(
        Issue(
            id="i_new_m4",
            team_id="team_lead",
            title="Payroll runs, week of Oct 26",
            owner_id="u3",
            created_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
            source_measurable_id="m4",
            source_week_start=date(2026, 10, 26),
        )
    )
    seeded_db.commit()


def test_partial_unique_index_enforces_one_active_meeting_per_team(seeded_db: Session) -> None:
    now = datetime(2026, 11, 11, 15, 0, tzinfo=UTC)
    seeded_db.add(
        Meeting(
            id="mt_live_1",
            team_id="team_lead",
            facilitator_id="u2",
            section="scorecard",
            section_started_at=now,
            started_at=now,
            ended_at=None,
            scorecard_week=date(2026, 11, 2),
        )
    )
    seeded_db.commit()

    seeded_db.add(
        Meeting(
            id="mt_live_2",
            team_id="team_lead",
            facilitator_id="u3",
            section="scorecard",
            section_started_at=now,
            started_at=now,
            ended_at=None,
            scorecard_week=date(2026, 11, 2),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


@pytest.mark.parametrize("bad_rating", [0, 11])
def test_db_rejects_meeting_rating_out_of_range(seeded_db: Session, bad_rating: int) -> None:
    seeded_db.add(
        MeetingRating(
            meeting_id="mt1",
            user_id="u4",
            rating=bad_rating,
            updated_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()


def test_db_rejects_blank_todo_title(seeded_db: Session) -> None:
    seeded_db.add(
        Todo(
            id="t_blank",
            team_id="team_lead",
            title="   ",
            owner_id="u2",
            due_date=date(2026, 11, 18),
            created_at=datetime(2026, 11, 11, 15, 0, tzinfo=UTC),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.commit()
    seeded_db.rollback()
