"""Level 10 Meeting, Attendee, Rating, and Immutable Summary ORM models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        CheckConstraint(
            "section IN ('scorecard', 'ids', 'conclude', 'ended')",
            name="meetings_section_valid",
        ),
        CheckConstraint(
            "(section = 'ended') = (ended_at IS NOT NULL)",
            name="meetings_ended_state_consistent",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="meetings_ended_after_started",
        ),
        Index("ix_meetings_team_started_at", "team_id", text("started_at DESC")),
        Index(
            "uq_meetings_one_active_per_team",
            "team_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(
        Text, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    facilitator_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(Text, nullable=False, default="scorecard")
    section_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scorecard_week: Mapped[date] = mapped_column(Date, nullable=False)


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"
    __table_args__ = (Index("ix_meeting_attendees_user_id", "user_id"),)

    meeting_id: Mapped[str] = mapped_column(
        Text, ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MeetingRating(Base):
    __tablename__ = "meeting_ratings"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 10", name="meeting_ratings_range"),
        Index("ix_meeting_ratings_user_id", "user_id"),
    )

    meeting_id: Mapped[str] = mapped_column(
        Text, ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"

    meeting_id: Mapped[str] = mapped_column(
        Text, ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
