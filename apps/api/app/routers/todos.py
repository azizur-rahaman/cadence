"""To-Dos listing (with weekly 90% completion & overdue flags) and done/undo toggle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import (
    TeamAccessContext,
    assert_team_write,
    get_current_user,
    require_team_read,
)
from app.clock import Clock, get_clock
from app.db import get_db
from app.dto import (
    ApiErrorResponse,
    ApiResponse,
    TodoDto,
    TodoListDto,
    TodoWeekCompletionDto,
    ToggleTodoDoneRequestDto,
    ok,
)
from app.errors import AppError
from app.models import Company, Todo, User
from app.rules import (
    TodoRecord,
    compute_todo_completion_for_week,
    get_company_tz,
    is_todo_overdue,
    last_13_weeks,
    last_closed_week,
    today_in_tz,
)

router = APIRouter(tags=["To-Dos"])


def _todo_to_dto(todo: Todo, owner_name: str, *, overdue: bool) -> TodoDto:
    return TodoDto(
        id=todo.id,
        team_id=todo.team_id,
        title=todo.title,
        owner_id=todo.owner_id,
        owner_name=owner_name,
        due_date=todo.due_date,
        done_at=todo.done_at,
        is_overdue=overdue,
        source_issue_id=todo.source_issue_id,
        created_at=todo.created_at,
        meeting_id=todo.meeting_id,
    )


@router.get(
    "/teams/{team_id}/todos",
    response_model=ApiResponse[TodoListDto],
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def list_team_todos(
    request: Request,
    ctx: TeamAccessContext = Depends(require_team_read),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[TodoListDto]:
    """List team To-Dos with server-computed overdue flags and 13-week 90% completion metrics."""
    company = db.get(Company, ctx.team.company_id)
    tz = get_company_tz(company.timezone if company is not None else None)
    now = clock.now()
    today = today_in_tz(now, tz)
    weeks = last_13_weeks(now, tz)
    current_week = weeks[-1]
    closed_week = last_closed_week(now, tz)

    rows = db.execute(select(Todo).where(Todo.team_id == ctx.team.id)).scalars().all()
    owner_ids = {t.owner_id for t in rows}
    owners = (
        {
            u.id: u.name
            for u in db.execute(select(User).where(User.id.in_(owner_ids))).scalars().all()
        }
        if owner_ids
        else {}
    )

    records = [TodoRecord(id=t.id, due_date=t.due_date, done_at=t.done_at) for t in rows]

    weekly_completion: dict[str, TodoWeekCompletionDto | None] = {}
    for w in weeks:
        comp = compute_todo_completion_for_week(records, w, tz=tz)
        weekly_completion[w.isoformat()] = (
            TodoWeekCompletionDto(
                week_start=w.isoformat(),
                due=comp.due,
                done=comp.done,
                rate_percent=comp.rate_percent,
                meets_target=comp.meets_target,
            )
            if comp is not None
            else None
        )

    open_rows = sorted(
        (t for t in rows if t.done_at is None),
        key=lambda t: (t.due_date, t.id),
    )
    done_rows = sorted(
        (t for t in rows if t.done_at is not None),
        key=lambda t: (t.done_at, t.id),
        reverse=True,
    )

    items: list[TodoDto] = []
    overdue_count = 0
    for t in open_rows + done_rows:
        overdue = is_todo_overdue(
            TodoRecord(id=t.id, due_date=t.due_date, done_at=t.done_at),
            today=today,
        )
        if overdue:
            overdue_count += 1
        items.append(_todo_to_dto(t, owners.get(t.owner_id, t.owner_id), overdue=overdue))

    payload = TodoListDto(
        team_id=ctx.team.id,
        today=today.isoformat(),
        current_week_start=current_week.isoformat(),
        last_closed_week_start=closed_week.isoformat(),
        overdue_count=overdue_count,
        current_week_completion=weekly_completion.get(current_week.isoformat()),
        last_closed_week_completion=weekly_completion.get(closed_week.isoformat()),
        weekly_completion=weekly_completion,
        items=items,
    )
    return ok(payload, request=request, clock=clock)


@router.patch(
    "/todos/{todo_id}",
    response_model=ApiResponse[TodoDto],
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
def toggle_todo_done(
    todo_id: str,
    body: ToggleTodoDoneRequestDto,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> ApiResponse[TodoDto]:
    """Mark a To-Do done (sets `done_at = clock.now()`) or undo (`done_at = None`)."""
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "To-Do not found.")

    team = assert_team_write(user, todo.team_id, db)

    if body.done:
        if todo.done_at is None:
            todo.done_at = clock.now()
    else:
        todo.done_at = None

    db.commit()
    db.refresh(todo)

    company = db.get(Company, team.company_id)
    tz = get_company_tz(company.timezone if company is not None else None)
    today = today_in_tz(clock.now(), tz)
    overdue = is_todo_overdue(
        TodoRecord(id=todo.id, due_date=todo.due_date, done_at=todo.done_at),
        today=today,
    )

    owner = db.get(User, todo.owner_id)
    owner_name = owner.name if owner is not None else todo.owner_id
    return ok(_todo_to_dto(todo, owner_name, overdue=overdue), request=request, clock=clock)
