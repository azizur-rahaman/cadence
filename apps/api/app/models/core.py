"""Core organization, team, user, and membership ORM models."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="companies_name_non_empty"),
        CheckConstraint("length(btrim(timezone)) > 0", name="companies_timezone_non_empty"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="America/Chicago")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (CheckConstraint("length(btrim(name)) > 0", name="teams_name_non_empty"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        Text, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="users_name_non_empty"),
        CheckConstraint("length(btrim(email)) > 0", name="users_email_non_empty"),
        CheckConstraint("role IN ('admin', 'team_member', 'observer')", name="users_role_valid"),
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        Text, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (Index("ix_memberships_team_id", "team_id"),)

    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[str] = mapped_column(
        Text, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
