"""Scorecard Measurable and weekly Score ORM models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Measurable(Base):
    __tablename__ = "measurables"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="measurables_name_non_empty"),
        CheckConstraint("length(btrim(unit)) > 0", name="measurables_unit_non_empty"),
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

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(
        Text, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    goal_type: Mapped[str] = mapped_column(Text, nullable=False)
    goal_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    goal_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    goal_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        # Leading column measurable_id serves both FK cascades and 13-week range queries
        UniqueConstraint("measurable_id", "week_start", name="uq_scores_measurable_week"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    measurable_id: Mapped[str] = mapped_column(
        Text, ForeignKey("measurables.id", ondelete="CASCADE"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
