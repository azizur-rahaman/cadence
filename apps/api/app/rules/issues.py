"""Pure Issue ordering rules (BR-40)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IssueRecord:
    id: str
    priority: int | None
    created_at: datetime
    solved_at: datetime | None


def order_unsolved_issues(issues: Iterable[IssueRecord]) -> list[IssueRecord]:
    """Return unsolved Issues ordered by priority 5 -> 1, oldest first, null priority last."""
    unsolved = [issue for issue in issues if issue.solved_at is None]
    return sorted(
        unsolved,
        key=lambda i: (
            0 if i.priority is not None else 1,
            -(i.priority or 0),
            i.created_at,
            i.id,
        ),
    )


def ordered_unsolved_issue_ids(issues: Iterable[IssueRecord]) -> list[str]:
    """Return unsolved Issue IDs in Issue order."""
    return [issue.id for issue in order_unsolved_issues(issues)]
