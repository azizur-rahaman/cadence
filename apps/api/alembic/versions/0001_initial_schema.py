"""Initial Cadence (Level 10) schema with CHECK constraints and partial unique indexes.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name="fk_teams_company_id_companies", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_teams"),
    )
    op.create_index("ix_teams_company_id", "teams", ["company_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "role IN ('admin', 'team_member', 'observer')", name="ck_users_users_role_valid"
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name="fk_users_company_id_companies", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])

    op.create_table(
        "memberships",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_memberships_user_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"], name="fk_memberships_team_id_teams", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "team_id", name="pk_memberships"),
    )

    op.create_table(
        "measurables",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("goal_type", sa.String(length=32), nullable=False),
        sa.Column("goal_value", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("goal_min", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("goal_max", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.CheckConstraint(
            "goal_type IN ('at_least', 'at_most', 'between', 'exactly')",
            name="ck_measurables_measurables_goal_type_valid",
        ),
        sa.CheckConstraint(
            "("
            "  goal_type = 'between' "
            "  AND goal_min IS NOT NULL AND goal_max IS NOT NULL "
            "  AND goal_min <= goal_max AND goal_value IS NULL"
            ") OR ("
            "  goal_type IN ('at_least', 'at_most', 'exactly') "
            "  AND goal_value IS NOT NULL AND goal_min IS NULL AND goal_max IS NULL"
            ")",
            name="ck_measurables_measurables_goal_shape_valid",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"], name="fk_measurables_team_id_teams", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_measurables_owner_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_measurables"),
    )
    op.create_index("ix_measurables_team_id", "measurables", ["team_id"])

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("measurable_id", sa.String(length=64), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.ForeignKeyConstraint(
            ["measurable_id"],
            ["measurables.id"],
            name="fk_scores_measurable_id_measurables",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_scores"),
        sa.UniqueConstraint("measurable_id", "week_start", name="uq_scores_measurable_week"),
    )
    op.create_index("ix_scores_measurable_id", "scores", ["measurable_id"])

    op.create_table(
        "rocks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("quarter", sa.String(length=16), nullable=False),
        sa.Column("seeded_status", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "seeded_status IN ('on_track', 'off_track', 'complete')",
            name="ck_rocks_rocks_seeded_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"], name="fk_rocks_team_id_teams", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_rocks_owner_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rocks"),
    )
    op.create_index("ix_rocks_team_id", "rocks", ["team_id"])

    op.create_table(
        "milestones",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("rock_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["rock_id"], ["rocks.id"], name="fk_milestones_rock_id_rocks", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_milestones"),
    )
    op.create_index("ix_milestones_rock_id", "milestones", ["rock_id"])

    op.create_table(
        "meetings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("facilitator_id", sa.String(length=64), nullable=False),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("section_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scorecard_week", sa.Date(), nullable=False),
        sa.CheckConstraint(
            "section IN ('scorecard', 'ids', 'conclude', 'ended')",
            name="ck_meetings_meetings_section_valid",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"], name="fk_meetings_team_id_teams", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["facilitator_id"],
            ["users.id"],
            name="fk_meetings_facilitator_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_meetings"),
    )
    op.create_index("ix_meetings_team_id", "meetings", ["team_id"])
    op.create_index(
        "uq_meetings_one_active_per_team",
        "meetings",
        ["team_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )

    op.create_table(
        "issues",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("source_measurable_id", sa.String(length=64), nullable=True),
        sa.Column("source_week_start", sa.Date(), nullable=True),
        sa.CheckConstraint("length(btrim(title)) > 0", name="ck_issues_issues_title_non_empty"),
        sa.CheckConstraint(
            "priority IS NULL OR (priority >= 1 AND priority <= 5)",
            name="ck_issues_issues_priority_range",
        ),
        sa.CheckConstraint(
            "solved_at IS NULL OR length(btrim(coalesce(resolution_note, ''))) > 0",
            name="ck_issues_issues_solved_requires_note",
        ),
        sa.CheckConstraint(
            "(source_measurable_id IS NULL) = (source_week_start IS NULL)",
            name="ck_issues_issues_source_pair_consistent",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"], name="fk_issues_team_id_teams", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_issues_owner_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_measurable_id"],
            ["measurables.id"],
            name="fk_issues_source_measurable_id_measurables",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_issues"),
    )
    op.create_index("ix_issues_team_id", "issues", ["team_id"])
    op.create_index(
        "uq_issues_unsolved_source",
        "issues",
        ["source_measurable_id", "source_week_start"],
        unique=True,
        postgresql_where=sa.text("solved_at IS NULL AND source_measurable_id IS NOT NULL"),
    )

    op.create_table(
        "todos",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("done_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_issue_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meeting_id", sa.String(length=64), nullable=True),
        sa.CheckConstraint("length(btrim(title)) > 0", name="ck_todos_todos_title_non_empty"),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"], name="fk_todos_team_id_teams", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_todos_owner_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_issue_id"],
            ["issues.id"],
            name="fk_todos_source_issue_id_issues",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name="fk_todos_meeting_id_meetings",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_todos"),
    )
    op.create_index("ix_todos_team_id", "todos", ["team_id"])

    op.create_table(
        "meeting_attendees",
        sa.Column("meeting_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name="fk_meeting_attendees_meeting_id_meetings",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_meeting_attendees_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("meeting_id", "user_id", name="pk_meeting_attendees"),
    )

    op.create_table(
        "meeting_ratings",
        sa.Column("meeting_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 10", name="ck_meeting_ratings_meeting_ratings_range"
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name="fk_meeting_ratings_meeting_id_meetings",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_meeting_ratings_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("meeting_id", "user_id", name="pk_meeting_ratings"),
    )

    op.create_table(
        "meeting_summaries",
        sa.Column("meeting_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name="fk_meeting_summaries_meeting_id_meetings",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("meeting_id", name="pk_meeting_summaries"),
    )


def downgrade() -> None:
    op.drop_table("meeting_summaries")
    op.drop_table("meeting_ratings")
    op.drop_table("meeting_attendees")
    op.drop_index("ix_todos_team_id", table_name="todos")
    op.drop_table("todos")
    op.drop_index("uq_issues_unsolved_source", table_name="issues")
    op.drop_index("ix_issues_team_id", table_name="issues")
    op.drop_table("issues")
    op.drop_index("uq_meetings_one_active_per_team", table_name="meetings")
    op.drop_index("ix_meetings_team_id", table_name="meetings")
    op.drop_table("meetings")
    op.drop_index("ix_milestones_rock_id", table_name="milestones")
    op.drop_table("milestones")
    op.drop_index("ix_rocks_team_id", table_name="rocks")
    op.drop_table("rocks")
    op.drop_index("ix_scores_measurable_id", table_name="scores")
    op.drop_table("scores")
    op.drop_index("ix_measurables_team_id", table_name="measurables")
    op.drop_table("measurables")
    op.drop_table("memberships")
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_teams_company_id", table_name="teams")
    op.drop_table("teams")
    op.drop_table("companies")
