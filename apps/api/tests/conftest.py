"""Shared pytest fixtures for database state and frozen clock."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from alembic import command
from app.cli.seed import seed_database
from app.clock import FrozenClock, get_clock, reset_default_clock
from app.config import get_settings
from app.db import SessionLocal
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    """Ensure the test PostgreSQL database is migrated to Alembic head."""
    api_root = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(api_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(api_root / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture()
def frozen_clock() -> Generator[FrozenClock, None, None]:
    clock = FrozenClock(get_settings().app_now)
    reset_default_clock(clock)
    yield clock
    reset_default_clock(None)


@pytest.fixture()
def seeded_db() -> Generator[Session, None, None]:
    """Reset PostgreSQL to a fresh seeded state before each DB test."""
    with SessionLocal() as db:
        db.execute(
            text(
                "TRUNCATE TABLE meeting_summaries, meeting_ratings, meeting_attendees, "
                "todos, issues, meetings, milestones, rocks, scores, measurables, "
                "memberships, users, teams, companies RESTART IDENTITY CASCADE"
            )
        )
        db.commit()
        seed_database(db)
        yield db
        db.rollback()


@pytest.fixture()
def api_client(
    seeded_db: Session, frozen_clock: FrozenClock
) -> Generator[TestClient, None, None]:
    """FastAPI TestClient backed by a freshly seeded DB and frozen APP_NOW clock."""
    _ = seeded_db
    app = create_app()
    app.dependency_overrides[get_clock] = lambda: frozen_clock
    with TestClient(app) as client:
        yield client
