"""Issues and To-Dos API, RBAC, owner validation, and completion rate tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _auth_headers(api_client: TestClient, user_id: str) -> dict[str, str]:
    resp = api_client.post("/api/v1/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_issues_returns_canonical_order_and_solved_list(api_client: TestClient) -> None:
    headers = _auth_headers(api_client, "u2")
    resp = api_client.get("/api/v1/teams/team_lead/issues", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert [i["id"] for i in data["unsolved"]] == ["i2", "i1", "i5", "i3", "i4"]
    assert [i["id"] for i in data["solved"]] == ["i6", "i7"]


def test_create_update_priority_and_solve_issue_flow(api_client: TestClient) -> None:
    headers = _auth_headers(api_client, "u2")

    # Reject blank title
    bad_title = api_client.post(
        "/api/v1/teams/team_lead/issues",
        headers=headers,
        json={"title": "   "},
    )
    assert bad_title.status_code == 422

    # Reject Observer owner
    bad_owner = api_client.post(
        "/api/v1/teams/team_lead/issues",
        headers=headers,
        json={"title": "Check vendor SLA", "owner_id": "u5"},
    )
    assert bad_owner.status_code == 422

    # Create valid issue (defaults owner to caller u2)
    created = api_client.post(
        "/api/v1/teams/team_lead/issues",
        headers=headers,
        json={"title": "Fix onboarding drop-off", "priority": 2},
    )
    assert created.status_code == 201
    iss = created.json()["data"]
    assert iss["owner_id"] == "u2"
    assert iss["priority"] == 2
    iss_id = iss["id"]

    # Reject priority out of range (0 / 6)
    assert (
        api_client.patch(
            f"/api/v1/issues/{iss_id}", headers=headers, json={"priority": 6}
        ).status_code
        == 422
    )

    # Update priority to 5 -> moves up among priority-5 items
    patched = api_client.patch(
        f"/api/v1/issues/{iss_id}", headers=headers, json={"priority": 5}
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["priority"] == 5

    # Clear priority to null
    cleared = api_client.patch(
        f"/api/v1/issues/{iss_id}", headers=headers, json={"priority": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["data"]["priority"] is None

    # Solve requires non-blank resolution note
    blank_note = api_client.post(
        f"/api/v1/issues/{iss_id}/solve",
        headers=headers,
        json={"resolution_note": "   "},
    )
    assert blank_note.status_code == 422

    # Solve succeeds
    solved = api_client.post(
        f"/api/v1/issues/{iss_id}/solve",
        headers=headers,
        json={"resolution_note": "Added guided checklist to signup."},
    )
    assert solved.status_code == 200
    assert solved.json()["data"]["solved_at"] == "2026-11-11T15:00:00Z"
    assert solved.json()["data"]["resolution_note"] == "Added guided checklist to signup."

    # Double solve & priority change on solved issue -> 409 CONFLICT
    assert (
        api_client.post(
            f"/api/v1/issues/{iss_id}/solve",
            headers=headers,
            json={"resolution_note": "Again"},
        ).status_code
        == 409
    )
    assert (
        api_client.patch(
            f"/api/v1/issues/{iss_id}", headers=headers, json={"priority": 3}
        ).status_code
        == 409
    )


def test_create_todo_from_issue_owner_validation_and_default_due_date(
    api_client: TestClient,
) -> None:
    u2_headers = _auth_headers(api_client, "u2")

    # Reject Observer u5 as To-Do owner -> 422
    obs_owner = api_client.post(
        "/api/v1/issues/i2/todos",
        headers=u2_headers,
        json={"title": "Follow up with client", "owner_id": "u5"},
    )
    assert obs_owner.status_code == 422

    # Reject cross-team member u6 (team_sales) on team_lead -> 422
    cross_owner = api_client.post(
        "/api/v1/issues/i2/todos",
        headers=u2_headers,
        json={"title": "Follow up with client", "owner_id": "u6"},
    )
    assert cross_owner.status_code == 422

    # Valid To-Do with omitted due_date -> defaults to today + 7 days (2026-11-18)
    ok_todo = api_client.post(
        "/api/v1/issues/i2/todos",
        headers=u2_headers,
        json={"title": "Send enterprise SLA revision", "owner_id": "u1"},
    )
    assert ok_todo.status_code == 201
    td = ok_todo.json()["data"]
    assert td["owner_id"] == "u1"
    assert td["due_date"] == "2026-11-18"
    assert td["source_issue_id"] == "i2"
    assert td["is_overdue"] is False

    # Admin u1 can own a To-Do on team_sales even without explicit membership
    u6_headers = _auth_headers(api_client, "u6")
    sales_todo = api_client.post(
        "/api/v1/issues/i8/todos",
        headers=u6_headers,
        json={"title": "Approve Q4 promo budget", "owner_id": "u1"},
    )
    assert sales_todo.status_code == 201
    assert sales_todo.json()["data"]["owner_id"] == "u1"


def test_list_todos_completion_metrics_and_toggle_done_undo(api_client: TestClient) -> None:
    headers = _auth_headers(api_client, "u2")
    resp = api_client.get("/api/v1/teams/team_lead/todos", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["today"] == "2026-11-11"
    assert data["overdue_count"] == 2
    assert data["last_closed_week_completion"] == {
        "week_start": "2026-11-02",
        "due": 10,
        "done": 9,
        "rate_percent": 90,
        "meets_target": True,
    }
    assert data["current_week_completion"] == {
        "week_start": "2026-11-09",
        "due": 3,
        "done": 0,
        "rate_percent": 0,
        "meets_target": False,
    }

    by_id = {t["id"]: t for t in data["items"]}
    assert by_id["t12"]["is_overdue"] is True
    assert by_id["t31"]["is_overdue"] is True
    assert by_id["t30"]["is_overdue"] is False

    # Mark overdue t31 done -> done_at set, is_overdue flips False
    done_resp = api_client.patch(
        "/api/v1/todos/t31", headers=headers, json={"done": True}
    )
    assert done_resp.status_code == 200
    assert done_resp.json()["data"]["done_at"] == "2026-11-11T15:00:00Z"
    assert done_resp.json()["data"]["is_overdue"] is False

    # Undo t31 -> done_at None, is_overdue flips back True
    undo_resp = api_client.patch(
        "/api/v1/todos/t31", headers=headers, json={"done": False}
    )
    assert undo_resp.status_code == 200
    assert undo_resp.json()["data"]["done_at"] is None
    assert undo_resp.json()["data"]["is_overdue"] is True


def test_issues_and_todos_rbac_enforcement(api_client: TestClient) -> None:
    # Non-member u6 gets 404 on team_lead routes & resource IDs
    u6_headers = _auth_headers(api_client, "u6")
    assert api_client.get("/api/v1/teams/team_lead/issues", headers=u6_headers).status_code == 404
    assert api_client.get("/api/v1/teams/team_lead/todos", headers=u6_headers).status_code == 404
    assert (
        api_client.patch("/api/v1/issues/i2", headers=u6_headers, json={"priority": 1}).status_code
        == 404
    )
    assert (
        api_client.post(
            "/api/v1/issues/i2/solve", headers=u6_headers, json={"resolution_note": "Nope"}
        ).status_code
        == 404
    )
    assert (
        api_client.patch("/api/v1/todos/t31", headers=u6_headers, json={"done": True}).status_code
        == 404
    )

    # Observer u5 can read (200), gets 403 on all mutations
    u5_headers = _auth_headers(api_client, "u5")
    assert api_client.get("/api/v1/teams/team_lead/issues", headers=u5_headers).status_code == 200
    assert api_client.get("/api/v1/teams/team_lead/todos", headers=u5_headers).status_code == 200
    assert (
        api_client.post(
            "/api/v1/teams/team_lead/issues", headers=u5_headers, json={"title": "Blocked"}
        ).status_code
        == 403
    )
    assert (
        api_client.patch("/api/v1/issues/i2", headers=u5_headers, json={"priority": 1}).status_code
        == 403
    )
    assert (
        api_client.post(
            "/api/v1/issues/i2/solve", headers=u5_headers, json={"resolution_note": "Blocked"}
        ).status_code
        == 403
    )
    assert (
        api_client.post(
            "/api/v1/issues/i2/todos",
            headers=u5_headers,
            json={"title": "Blocked", "owner_id": "u2"},
        ).status_code
        == 403
    )
    assert (
        api_client.patch("/api/v1/todos/t31", headers=u5_headers, json={"done": True}).status_code
        == 403
    )
