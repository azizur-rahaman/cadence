"""Issues and To-Dos ORM models with partial unique index and query-driven indexes."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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
            "solved_at IS NULL OR solved_at >= created_at",
            name="issues_solved_after_created",
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
        Index(
            "ix_issues_team_unsolved_order",
            "team_id",
            text("priority DESC NULLS LAST"),
            "created_at",
            postgresql_where=text("solved_at IS NULL"),
        ),
        Index(
            "ix_issues_team_solved_at",
            "team_id",
            text("solved_at DESC"),
            postgresql_where=text("solved_at IS NOT NULL"),
        ),
        Index(
            "ix_issues_source_measurable_id",
            "source_measurable_id",
            postgresql_where=text("source_measurable_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(
        Text, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_measurable_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("measurables.id", ondelete="SET NULL"), nullable=True
    )
    source_week_start: Mapped[date | None] = mapped_column(Date, nullable=True)


class Todo(Base):
    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) > 0", name="todos_title_non_empty"),
        Index("ix_todos_team_due_date", "team_id", "due_date"),
        Index(
            "ix_todos_team_open_due",
            "team_id",
            "due_date",
            postgresql_where=text("done_at IS NULL"),
        ),
        Index("ix_todos_team_created_at", "team_id", "created_at"),
        Index(
            "ix_todos_source_issue_id",
            "source_issue_id",
            postgresql_where=text("source_issue_id IS NOT NULL"),
        ),
        Index(
            "ix_todos_meeting_id",
            "meeting_id",
            postgresql_where=text("meeting_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(
        Text, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_issue_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("issues.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meeting_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True
    )
