"""Idempotent seed loader for Cadence (Level 10).

Loads `seed/seed.json` preserving all original IDs (`u1`, `m1`, `t12`, `mt1`, ...),
upserting every record so re-running the loader is completely safe and changes nothing.
Also derives `scorecard_week`, `meeting_id` links, and immutable `meeting_summaries`
for the seeded ended meetings (`mt1`, `mt2`).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.clock import parse_utc_iso
from app.config import get_settings
from app.db import SessionLocal
from app.models import (
    Company,
    Issue,
    Measurable,
    Meeting,
    MeetingAttendee,
    MeetingRating,
    MeetingSummary,
    Membership,
    Milestone,
    Rock,
    Score,
    Team,
    Todo,
    User,
)


def _to_decimal(val: int | float | str | None) -> Decimal | None:
    if val is None:
        return None
    return Decimal(str(val))


def _week_start_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _eval_closed_week_status(measurable: dict[str, Any], score_val: Decimal | None) -> str:
    if score_val is None:
        return "off_track"
    goal = measurable["goal"]
    gtype = goal["type"]
    if gtype == "at_least":
        return "on_track" if score_val >= Decimal(str(goal["value"])) else "off_track"
    if gtype == "at_most":
        return "on_track" if score_val <= Decimal(str(goal["value"])) else "off_track"
    if gtype == "exactly":
        return "on_track" if score_val == Decimal(str(goal["value"])) else "off_track"
    if gtype == "between":
        gmin = Decimal(str(goal["min"]))
        gmax = Decimal(str(goal["max"]))
        return "on_track" if gmin <= score_val <= gmax else "off_track"
    raise ValueError(f"Unsupported goal type: {gtype}")


def _round_rating(ratings: list[int]) -> float | None:
    if not ratings:
        return None
    avg = Decimal(sum(ratings)) / Decimal(len(ratings))
    return float(avg.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def resolve_seed_path(seed_path: str | Path | None = None) -> Path:
    if seed_path is not None:
        return Path(seed_path)
    configured = Path(get_settings().seed_file)
    if configured.is_absolute():
        return configured
    api_root = Path(__file__).resolve().parents[2]
    return api_root / configured


def seed_database(db: Session, seed_path: str | Path | None = None) -> dict[str, int]:
    """Load `seed.json` idempotently into PostgreSQL and return table row counts."""
    path = resolve_seed_path(seed_path)
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    company_data = raw["company"]
    company_id: str = company_data["id"]
    tz = ZoneInfo(company_data["timezone"])

    # 1. Company
    stmt = pg_insert(Company).values(
        id=company_id,
        name=company_data["name"],
        timezone=company_data["timezone"],
    )
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"name": stmt.excluded.name, "timezone": stmt.excluded.timezone},
        )
    )

    # 2. Teams
    for t in raw["teams"]:
        stmt = pg_insert(Team).values(id=t["id"], company_id=company_id, name=t["name"])
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={"company_id": stmt.excluded.company_id, "name": stmt.excluded.name},
            )
        )

    # 3. Users
    for u in raw["users"]:
        stmt = pg_insert(User).values(
            id=u["id"],
            company_id=company_id,
            name=u["name"],
            email=u["email"],
            role=u["role"],
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "company_id": stmt.excluded.company_id,
                    "name": stmt.excluded.name,
                    "email": stmt.excluded.email,
                    "role": stmt.excluded.role,
                },
            )
        )

    # 4. Memberships
    for m in raw["memberships"]:
        stmt = pg_insert(Membership).values(user_id=m["user_id"], team_id=m["team_id"])
        db.execute(stmt.on_conflict_do_nothing(index_elements=["user_id", "team_id"]))

    # 5. Measurables
    for meas in raw["measurables"]:
        goal = meas["goal"]
        stmt = pg_insert(Measurable).values(
            id=meas["id"],
            team_id=meas["team_id"],
            name=meas["name"],
            owner_id=meas["owner_id"],
            unit=meas["unit"],
            goal_type=goal["type"],
            goal_value=_to_decimal(goal.get("value")),
            goal_min=_to_decimal(goal.get("min")),
            goal_max=_to_decimal(goal.get("max")),
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "team_id": stmt.excluded.team_id,
                    "name": stmt.excluded.name,
                    "owner_id": stmt.excluded.owner_id,
                    "unit": stmt.excluded.unit,
                    "goal_type": stmt.excluded.goal_type,
                    "goal_value": stmt.excluded.goal_value,
                    "goal_min": stmt.excluded.goal_min,
                    "goal_max": stmt.excluded.goal_max,
                },
            )
        )

    # 6. Scores
    score_lookup: dict[tuple[str, date], Decimal] = {}
    for sc in raw["scores"]:
        ws = date.fromisoformat(sc["week_start"])
        val = _to_decimal(sc["value"])
        assert val is not None
        score_lookup[(sc["measurable_id"], ws)] = val
        stmt = pg_insert(Score).values(
            measurable_id=sc["measurable_id"],
            week_start=ws,
            value=val,
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["measurable_id", "week_start"],
                set_={"value": stmt.excluded.value},
            )
        )

    # 7. Rocks
    for r in raw["rocks"]:
        stmt = pg_insert(Rock).values(
            id=r["id"],
            team_id=r["team_id"],
            title=r["title"],
            owner_id=r["owner_id"],
            quarter=r["quarter"],
            seeded_status=r["status"],
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "team_id": stmt.excluded.team_id,
                    "title": stmt.excluded.title,
                    "owner_id": stmt.excluded.owner_id,
                    "quarter": stmt.excluded.quarter,
                    "seeded_status": stmt.excluded.seeded_status,
                },
            )
        )

    # 8. Milestones
    for ms in raw["milestones"]:
        stmt = pg_insert(Milestone).values(
            id=ms["id"],
            rock_id=ms["rock_id"],
            title=ms["title"],
            due_date=date.fromisoformat(ms["due_date"]),
            done=bool(ms["done"]),
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "rock_id": stmt.excluded.rock_id,
                    "title": stmt.excluded.title,
                    "due_date": stmt.excluded.due_date,
                    "done": stmt.excluded.done,
                },
            )
        )

    # 9. Meetings (inserted before Todos so todos.meeting_id FK resolves cleanly)
    meeting_windows: list[tuple[str, str, Any, Any]] = []
    for mt in raw["meetings"]:
        started_at = parse_utc_iso(mt["started_at"])
        ended_at = parse_utc_iso(mt["ended_at"])
        started_local_date = started_at.astimezone(tz).date()
        scorecard_week = _week_start_of(started_local_date) - timedelta(weeks=1)
        meeting_windows.append((mt["id"], mt["team_id"], started_at, ended_at))

        stmt = pg_insert(Meeting).values(
            id=mt["id"],
            team_id=mt["team_id"],
            facilitator_id=mt["facilitator_id"],
            section="ended",
            section_started_at=ended_at,
            started_at=started_at,
            ended_at=ended_at,
            scorecard_week=scorecard_week,
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "team_id": stmt.excluded.team_id,
                    "facilitator_id": stmt.excluded.facilitator_id,
                    "section": stmt.excluded.section,
                    "section_started_at": stmt.excluded.section_started_at,
                    "started_at": stmt.excluded.started_at,
                    "ended_at": stmt.excluded.ended_at,
                    "scorecard_week": stmt.excluded.scorecard_week,
                },
            )
        )

        for uid in mt["attendee_ids"]:
            att_stmt = pg_insert(MeetingAttendee).values(
                meeting_id=mt["id"],
                user_id=uid,
                joined_at=started_at,
            )
            db.execute(att_stmt.on_conflict_do_nothing(index_elements=["meeting_id", "user_id"]))

        for rating_entry in mt["ratings"]:
            rat_stmt = pg_insert(MeetingRating).values(
                meeting_id=mt["id"],
                user_id=rating_entry["user_id"],
                rating=int(rating_entry["rating"]),
                updated_at=ended_at,
            )
            db.execute(
                rat_stmt.on_conflict_do_update(
                    index_elements=["meeting_id", "user_id"],
                    set_={
                        "rating": rat_stmt.excluded.rating,
                        "updated_at": rat_stmt.excluded.updated_at,
                    },
                )
            )

    # 10. Issues
    for iss in raw["issues"]:
        source = iss.get("source")
        src_mid = source["measurable_id"] if source else None
        src_ws = date.fromisoformat(source["week_start"]) if source else None
        stmt = pg_insert(Issue).values(
            id=iss["id"],
            team_id=iss["team_id"],
            title=iss["title"],
            owner_id=iss["owner_id"],
            priority=iss.get("priority"),
            created_at=parse_utc_iso(iss["created_at"]),
            solved_at=parse_utc_iso(iss["solved_at"]) if iss.get("solved_at") else None,
            resolution_note=iss.get("resolution_note"),
            source_measurable_id=src_mid,
            source_week_start=src_ws,
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "team_id": stmt.excluded.team_id,
                    "title": stmt.excluded.title,
                    "owner_id": stmt.excluded.owner_id,
                    "priority": stmt.excluded.priority,
                    "created_at": stmt.excluded.created_at,
                    "solved_at": stmt.excluded.solved_at,
                    "resolution_note": stmt.excluded.resolution_note,
                    "source_measurable_id": stmt.excluded.source_measurable_id,
                    "source_week_start": stmt.excluded.source_week_start,
                },
            )
        )

    # 11. Todos (derive meeting_id when created_at falls within a seeded meeting window)
    for td in raw["todos"]:
        created_at = parse_utc_iso(td["created_at"])
        matched_meeting_id: str | None = None
        for mt_id, mt_team_id, mt_start, mt_end in meeting_windows:
            if td["team_id"] == mt_team_id and mt_start <= created_at <= mt_end:
                matched_meeting_id = mt_id
                break

        stmt = pg_insert(Todo).values(
            id=td["id"],
            team_id=td["team_id"],
            title=td["title"],
            owner_id=td["owner_id"],
            due_date=date.fromisoformat(td["due_date"]),
            done_at=parse_utc_iso(td["done_at"]) if td.get("done_at") else None,
            source_issue_id=td.get("source_issue_id"),
            created_at=created_at,
            meeting_id=matched_meeting_id,
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "team_id": stmt.excluded.team_id,
                    "title": stmt.excluded.title,
                    "owner_id": stmt.excluded.owner_id,
                    "due_date": stmt.excluded.due_date,
                    "done_at": stmt.excluded.done_at,
                    "source_issue_id": stmt.excluded.source_issue_id,
                    "created_at": stmt.excluded.created_at,
                    "meeting_id": stmt.excluded.meeting_id,
                },
            )
        )

    # 12. Immutable Meeting Summaries for seeded ended meetings (mt1, mt2)
    for mt in raw["meetings"]:
        started_at = parse_utc_iso(mt["started_at"])
        ended_at = parse_utc_iso(mt["ended_at"])
        scorecard_week = _week_start_of(started_at.astimezone(tz).date()) - timedelta(weeks=1)
        team_measurables = [m for m in raw["measurables"] if m["team_id"] == mt["team_id"]]

        measurable_status = {
            m["id"]: _eval_closed_week_status(m, score_lookup.get((m["id"], scorecard_week)))
            for m in team_measurables
        }
        issues_solved = sorted(
            iss["id"]
            for iss in raw["issues"]
            if iss["team_id"] == mt["team_id"]
            and iss.get("solved_at") is not None
            and started_at <= parse_utc_iso(iss["solved_at"]) <= ended_at
        )
        todos_created = sorted(
            td["id"]
            for td in raw["todos"]
            if td["team_id"] == mt["team_id"]
            and started_at <= parse_utc_iso(td["created_at"]) <= ended_at
        )
        attendee_ids = sorted(mt["attendee_ids"])
        rating_val = _round_rating([int(r["rating"]) for r in mt["ratings"]])

        snapshot = {
            "scorecard_week": scorecard_week.isoformat(),
            "measurable_status": measurable_status,
            "issues_solved": issues_solved,
            "todos_created": todos_created,
            "attendee_ids": attendee_ids,
            "rating": rating_val,
        }
        sum_stmt = pg_insert(MeetingSummary).values(
            meeting_id=mt["id"],
            snapshot=snapshot,
            created_at=ended_at,
        )
        db.execute(
            sum_stmt.on_conflict_do_update(
                index_elements=["meeting_id"],
                set_={
                    "snapshot": sum_stmt.excluded.snapshot,
                    "created_at": sum_stmt.excluded.created_at,
                },
            )
        )

    db.commit()
    return get_row_counts(db)


def get_row_counts(db: Session) -> dict[str, int]:
    models = {
        "companies": Company,
        "teams": Team,
        "users": User,
        "memberships": Membership,
        "measurables": Measurable,
        "scores": Score,
        "rocks": Rock,
        "milestones": Milestone,
        "issues": Issue,
        "todos": Todo,
        "meetings": Meeting,
        "meeting_attendees": MeetingAttendee,
        "meeting_ratings": MeetingRating,
        "meeting_summaries": MeetingSummary,
    }
    return {
        name: int(db.execute(select(func.count()).select_from(model)).scalar_one())
        for name, model in models.items()
    }


def main() -> None:
    with SessionLocal() as db:
        counts = seed_database(db)
    print(json.dumps({"seeded": True, "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
