"""Issues CRUD, priority update, solve, and create-To-Do-from-Issue endpoints."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import (
    TeamAccessContext,
    assert_eligible_team_owner,
    assert_team_write,
    get_current_user,
    require_team_read,
    require_team_write,
)
from app.clock import Clock, get_clock
from app.db import get_db
from app.dto import (
    ApiErrorResponse,
    ApiResponse,
    CreateIssueRequestDto,
    CreateTodoRequestDto,
    IssueDto,
    IssueListDto,
    IssueSourceDto,
    SolveIssueRequestDto,
    TodoDto,
    UpdateIssuePriorityRequestDto,
    ok,
)
from app.errors import AppError
from app.models import Company, Issue, Meeting, Todo, User
from app.realtime.hub import notify_team_workspace_change
from app.rules import (
    IssueRecord,
    TodoRecord,
    get_company_tz,
    is_todo_overdue,
    order_unsolved_issues,
    today_in_tz,
)

router = APIRouter(tags=["Issues"])


def _issue_to_dto(issue: Issue, owner_name: str) -> IssueDto:
    source = (
        IssueSourceDto(
            measurable_id=issue.source_measurable_id,
            week_start=issue.source_week_start,
        )
        if issue.source_measurable_id is not None and issue.source_week_start is not None
        else None
    )
    return IssueDto(
        id=issue.id,
        team_id=issue.team_id,
        title=issue.title,
        owner_id=issue.owner_id,
        owner_name=owner_name,
        priority=issue.priority,
        created_at=issue.created_at,
        solved_at=issue.solved_at,
        resolution_note=issue.resolution_note,
        source=source,
    )


def _load_issue_or_404(issue_id: str, db: Session) -> Issue:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Issue not found.")
    return issue


@router.get(
    "/teams/{team_id}/issues",
    response_model=ApiResponse[IssueListDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def list_team_issues(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[IssueListDto]:
    """List unsolved (in canonical Issue order) and solved Issues for `team_id`."""
    rows = db.execute(select(Issue).where(Issue.team_id == ctx.team.id)).scalars().all()
    owner_ids = {i.owner_id for i in rows}
    owners = (
        {
            u.id: u.name
            for u in db.execute(select(User).where(User.id.in_(owner_ids))).scalars().all()
        }
        if owner_ids
        else {}
    )
    by_id = {i.id: i for i in rows}

    ordered_records = order_unsolved_issues(
        [
            IssueRecord(
                id=i.id,
                priority=i.priority,
                created_at=i.created_at,
                solved_at=i.solved_at,
            )
            for i in rows
        ]
    )
    unsolved_dtos = [
        _issue_to_dto(by_id[r.id], owners.get(by_id[r.id].owner_id, by_id[r.id].owner_id))
        for r in ordered_records
    ]

    solved_rows = sorted(
        (i for i in rows if i.solved_at is not None),
        key=lambda i: (i.solved_at, i.id),
        reverse=True,
    )
    solved_dtos = [
        _issue_to_dto(i, owners.get(i.owner_id, i.owner_id)) for i in solved_rows
    ]

    return ok(
        IssueListDto(unsolved=unsolved_dtos, solved=solved_dtos),
        request=request,
        clock=clock,
    )


@router.post(
    "/teams/{team_id}/issues",
    response_model=ApiResponse[IssueDto],
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def create_issue(
    body: CreateIssueRequestDto,
    request: Request,
    background_tasks: BackgroundTasks,
    ctx: TeamAccessContext = Depends(require_team_write),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[IssueDto]:
    """Create a new unsolved Issue for `team_id`."""
    owner_id = body.owner_id or ctx.user.id
    owner = assert_eligible_team_owner(owner_id, ctx.team.id, ctx.team.company_id, db)

    issue = Issue(
        id=f"iss_{uuid.uuid4().hex[:12]}",
        team_id=ctx.team.id,
        title=body.title,
        owner_id=owner.id,
        priority=body.priority,
        created_at=clock.now(),
        solved_at=None,
        resolution_note=None,
        source_measurable_id=None,
        source_week_start=None,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    notify_team_workspace_change(background_tasks, ctx.team.id, "issues", db)
    return ok(_issue_to_dto(issue, owner.name), request=request, clock=clock)


@router.patch(
    "/issues/{issue_id}",
    response_model=ApiResponse[IssueDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def update_issue_priority(
    issue_id: str,
    body: UpdateIssuePriorityRequestDto,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[IssueDto]:
    """Update an unsolved Issue's priority (1..5 or null)."""
    issue = _load_issue_or_404(issue_id, db)
    assert_team_write(user, issue.team_id, db)

    if issue.solved_at is not None:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Cannot change priority of an already solved issue.",
        )

    issue.priority = body.priority
    db.commit()
    db.refresh(issue)

    owner = db.get(User, issue.owner_id)
    owner_name = owner.name if owner is not None else issue.owner_id
    notify_team_workspace_change(background_tasks, issue.team_id, "issues", db)
    return ok(_issue_to_dto(issue, owner_name), request=request, clock=clock)


@router.post(
    "/issues/{issue_id}/solve",
    response_model=ApiResponse[IssueDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def solve_issue(
    issue_id: str,
    body: SolveIssueRequestDto,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[IssueDto]:
    """Mark an Issue as solved with a mandatory resolution note."""
    issue = _load_issue_or_404(issue_id, db)
    assert_team_write(user, issue.team_id, db)

    if issue.solved_at is not None:
        raise AppError(status.HTTP_409_CONFLICT, "CONFLICT", "Issue is already solved.")

    issue.solved_at = clock.now()
    issue.resolution_note = body.resolution_note
    db.commit()
    db.refresh(issue)

    owner = db.get(User, issue.owner_id)
    owner_name = owner.name if owner is not None else issue.owner_id
    notify_team_workspace_change(background_tasks, issue.team_id, "issues", db)
    return ok(_issue_to_dto(issue, owner_name), request=request, clock=clock)


@router.post(
    "/issues/{issue_id}/todos",
    response_model=ApiResponse[TodoDto],
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def create_todo_from_issue(
    issue_id: str,
    body: CreateTodoRequestDto,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[TodoDto]:
    """Create a To-Do linked to an Issue, validating owner eligibility and defaulting due +7d."""
    issue = _load_issue_or_404(issue_id, db)
    team = assert_team_write(user, issue.team_id, db)
    owner = assert_eligible_team_owner(body.owner_id, team.id, team.company_id, db)

    if body.meeting_id is not None:
        meeting = db.get(Meeting, body.meeting_id)
        if meeting is None or meeting.team_id != team.id:
            raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Meeting not found.")

    company = db.get(Company, team.company_id)
    tz = get_company_tz(company.timezone if company is not None else None)
    now = clock.now()
    today = today_in_tz(now, tz)
    due_date = body.due_date if body.due_date is not None else today + timedelta(days=7)

    todo = Todo(
        id=f"td_{uuid.uuid4().hex[:12]}",
        team_id=team.id,
        title=body.title,
        owner_id=owner.id,
        due_date=due_date,
        done_at=None,
        source_issue_id=issue.id,
        created_at=now,
        meeting_id=body.meeting_id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)

    overdue = is_todo_overdue(
        TodoRecord(id=todo.id, due_date=todo.due_date, done_at=todo.done_at),
        today=today,
    )
    dto = TodoDto(
        id=todo.id,
        team_id=todo.team_id,
        title=todo.title,
        owner_id=todo.owner_id,
        owner_name=owner.name,
        due_date=todo.due_date,
        done_at=todo.done_at,
        is_overdue=overdue,
        source_issue_id=todo.source_issue_id,
        created_at=todo.created_at,
        meeting_id=todo.meeting_id,
    )
    notify_team_workspace_change(background_tasks, team.id, "todos", db)
    return ok(dto, request=request, clock=clock)
