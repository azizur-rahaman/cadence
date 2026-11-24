"""Quarterly Rock and Milestone ORM models."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Rock(Base):
    __tablename__ = "rocks"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) > 0", name="rocks_title_non_empty"),
        CheckConstraint("quarter ~ '^[0-9]{4}-Q[1-4]$'", name="rocks_quarter_format"),
        CheckConstraint(
            "seeded_status IN ('on_track', 'off_track', 'complete')",
            name="rocks_seeded_status_valid",
        ),
        Index("ix_rocks_team_quarter", "team_id", "quarter"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(
        Text, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quarter: Mapped[str] = mapped_column(Text, nullable=False)
    seeded_status: Mapped[str] = mapped_column(Text, nullable=False)


class Milestone(Base):
    __tablename__ = "milestones"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) > 0", name="milestones_title_non_empty"),
        Index("ix_milestones_rock_due", "rock_id", "due_date"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    rock_id: Mapped[str] = mapped_column(
        Text, ForeignKey("rocks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
