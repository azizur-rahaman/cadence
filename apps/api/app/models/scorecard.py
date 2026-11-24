"""Scorecard Measurable and weekly Score ORM models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Measurable(Base):
    __tablename__ = "measurables"
    __table_args__ = (
        CheckConstraint(
            "goal_type IN ('at_least', 'at_most', 'between', 'exactly')",
            name="measurables_goal_type_valid",
        ),
        CheckConstraint(
            "("
            "  goal_type = 'between' "
            "  AND goal_min IS NOT NULL AND goal_max IS NOT NULL "
            "  AND goal_min <= goal_max AND goal_value IS NULL"
            ") OR ("
            "  goal_type IN ('at_least', 'at_most', 'exactly') "
            "  AND goal_value IS NOT NULL AND goal_min IS NULL AND goal_max IS NULL"
            ")",
            name="measurables_goal_shape_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    goal_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    goal_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    goal_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("measurable_id", "week_start", name="uq_scores_measurable_week"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    measurable_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("measurables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
