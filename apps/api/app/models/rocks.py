"""Quarterly Rock and Milestone ORM models."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Rock(Base):
    __tablename__ = "rocks"
    __table_args__ = (
        CheckConstraint(
            "seeded_status IN ('on_track', 'off_track', 'complete')",
            name="rocks_seeded_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    owner_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    quarter: Mapped[str] = mapped_column(String(16), nullable=False)
    seeded_status: Mapped[str] = mapped_column(String(32), nullable=False)


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rock_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("rocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
