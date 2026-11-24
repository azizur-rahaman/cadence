"""Issues and To-Dos ORM models with partial unique index for duplicate-free source Issues."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) > 0", name="issues_title_non_empty"),
        CheckConstraint(
            "priority IS NULL OR (priority >= 1 AND priority <= 5)",
            name="issues_priority_range",
        ),
        CheckConstraint(
            "solved_at IS NULL OR length(btrim(coalesce(resolution_note, ''))) > 0",
            name="issues_solved_requires_note",
        ),
        CheckConstraint(
            "(source_measurable_id IS NULL) = (source_week_start IS NULL)",
            name="issues_source_pair_consistent",
        ),
        Index(
            "uq_issues_unsolved_source",
            "source_measurable_id",
            "source_week_start",
            unique=True,
            postgresql_where=text("solved_at IS NULL AND source_measurable_id IS NOT NULL"),
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
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_measurable_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("measurables.id", ondelete="SET NULL"), nullable=True
    )
    source_week_start: Mapped[date | None] = mapped_column(Date, nullable=True)


class Todo(Base):
    __tablename__ = "todos"
    __table_args__ = (CheckConstraint("length(btrim(title)) > 0", name="todos_title_non_empty"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    owner_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_issue_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meeting_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True
    )
