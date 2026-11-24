"""Level 10 Meeting lifecycle, timer overrun, facilitator RBAC, rating, and summary tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.clock import FrozenClock


def _auth_headers(api_client: TestClient, user_id: str) -> dict[str, str]:
    resp = api_client.post("/api/v1/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_meeting_lifecycle_timer_overrun_ratings_and_immutable_summary(
    api_client: TestClient, frozen_clock: FrozenClock
) -> None:
    u2_headers = _auth_headers(api_client, "u2")
    u3_headers = _auth_headers(api_client, "u3")
    u5_headers = _auth_headers(api_client, "u5")

    # Initially no active meeting for team_lead
    active0 = api_client.get("/api/v1/teams/team_lead/meetings/active", headers=u2_headers)
    assert active0.status_code == 200
    assert active0.json()["data"]["meeting"] is None

    # Observer u5 cannot start a meeting -> 403
    obs_start = api_client.post("/api/v1/teams/team_lead/meetings", headers=u5_headers)
    assert obs_start.status_code == 403

    # Facilitator u2 starts meeting -> 201
    started = api_client.post("/api/v1/teams/team_lead/meetings", headers=u2_headers)
    assert started.status_code == 201
    mt = started.json()["data"]
    mt_id = mt["id"]
    assert mt["section"] == "scorecard"
    assert mt["scorecard_week"] == "2026-11-02"
    assert mt["timer"] == {
        "allotted_seconds": 300,
        "elapsed_seconds": 0,
        "remaining_seconds": 300,
        "over_time": False,
    }
    assert [a["user_id"] for a in mt["attendees"]] == ["u2"]

    # Second concurrent active meeting -> 409 CONFLICT
    dup = api_client.post("/api/v1/teams/team_lead/meetings", headers=u3_headers)
    assert dup.status_code == 409

    # Member u3 and Observer u5 join -> persistent attendees
    assert api_client.post(f"/api/v1/meetings/{mt_id}/join", headers=u3_headers).status_code == 200
    joined = api_client.post(f"/api/v1/meetings/{mt_id}/join", headers=u5_headers)
    assert joined.status_code == 200
    assert [a["user_id"] for a in joined.json()["data"]["attendees"]] == ["u2", "u3", "u5"]

    # Advance frozen clock past 5m scorecard allotment -> over_time=True, does NOT auto-advance
    frozen_clock.advance(seconds=310)
    ticked = api_client.get(f"/api/v1/meetings/{mt_id}", headers=u2_headers).json()["data"]
    assert ticked["section"] == "scorecard"
    assert ticked["timer"]["over_time"] is True
    assert ticked["timer"]["remaining_seconds"] == -10

    # Non-facilitator u3 cannot advance or end -> 403
    assert (
        api_client.post(f"/api/v1/meetings/{mt_id}/advance", headers=u3_headers).status_code == 403
    )
    assert api_client.post(f"/api/v1/meetings/{mt_id}/end", headers=u3_headers).status_code == 403

    # Facilitator advances scorecard -> ids
    ids_state = api_client.post(f"/api/v1/meetings/{mt_id}/advance", headers=u2_headers)
    assert ids_state.status_code == 200
    assert ids_state.json()["data"]["section"] == "ids"
    assert ids_state.json()["data"]["timer"]["allotted_seconds"] == 3600

    # Solve issue i3 and create a To-Do during IDS
    frozen_clock.advance(seconds=60)
    assert (
        api_client.post(
            "/api/v1/issues/i3/solve",
            headers=u2_headers,
            json={"resolution_note": "Agreed on vendor consolidation."},
        ).status_code
        == 200
    )
    todo_resp = api_client.post(
        "/api/v1/issues/i3/todos",
        headers=u2_headers,
        json={"title": "Send consolidation notice", "owner_id": "u3", "meeting_id": mt_id},
    )
    assert todo_resp.status_code == 201
    created_todo_id = todo_resp.json()["data"]["id"]

    # Facilitator advances ids -> conclude
    conclude_state = api_client.post(f"/api/v1/meetings/{mt_id}/advance", headers=u2_headers)
    assert conclude_state.status_code == 200
    assert conclude_state.json()["data"]["section"] == "conclude"
    assert conclude_state.json()["data"]["timer"]["allotted_seconds"] == 600
    assert [t["id"] for t in conclude_state.json()["data"]["todos_created"]] == [created_todo_id]

    # Observer u5 cannot rate -> 403
    assert (
        api_client.put(
            f"/api/v1/meetings/{mt_id}/rating", headers=u5_headers, json={"rating": 8}
        ).status_code
        == 403
    )

    # Rating out of 1..10 -> 422
    assert (
        api_client.put(
            f"/api/v1/meetings/{mt_id}/rating", headers=u2_headers, json={"rating": 11}
        ).status_code
        == 422
    )

    # u2 rates 8, u3 rates 9, u2 updates to 9 -> average = (9+9)/2 = 9.0
    assert (
        api_client.put(
            f"/api/v1/meetings/{mt_id}/rating", headers=u2_headers, json={"rating": 8}
        ).status_code
        == 200
    )
    assert (
        api_client.put(
            f"/api/v1/meetings/{mt_id}/rating", headers=u3_headers, json={"rating": 9}
        ).status_code
        == 200
    )
    r_upd = api_client.put(
        f"/api/v1/meetings/{mt_id}/rating", headers=u2_headers, json={"rating": 9}
    )
    assert r_upd.status_code == 200
    assert r_upd.json()["data"]["average_rating"] == 9.0

    # Summary before end -> 409
    assert (
        api_client.get(f"/api/v1/meetings/{mt_id}/summary", headers=u2_headers).status_code == 409
    )

    # Facilitator advances conclude -> ended (stores immutable summary)
    ended = api_client.post(f"/api/v1/meetings/{mt_id}/advance", headers=u2_headers)
    assert ended.status_code == 200
    end_data = ended.json()["data"]
    assert end_data["section"] == "ended"
    assert end_data["summary"] is not None
    assert end_data["summary"]["scorecard_week"] == "2026-11-02"
    assert end_data["summary"]["issues_solved"] == ["i3"]
    assert end_data["summary"]["todos_created"] == [created_todo_id]
    assert end_data["summary"]["attendee_ids"] == ["u2", "u3", "u5"]
    assert end_data["summary"]["rating"] == 9.0

    # Rating after end -> 409
    assert (
        api_client.put(
            f"/api/v1/meetings/{mt_id}/rating", headers=u2_headers, json={"rating": 5}
        ).status_code
        == 409
    )

    # GET /summary returns identical immutable snapshot
    summary_resp = api_client.get(f"/api/v1/meetings/{mt_id}/summary", headers=u5_headers)
    assert summary_resp.status_code == 200
    assert summary_resp.json()["data"] == end_data["summary"]


def test_seeded_meeting_summaries_and_non_member_404(api_client: TestClient) -> None:
    u2_headers = _auth_headers(api_client, "u2")
    u6_headers = _auth_headers(api_client, "u6")

    mt1 = api_client.get("/api/v1/meetings/mt1/summary", headers=u2_headers)
    assert mt1.status_code == 200
    assert mt1.json()["data"]["rating"] == 8.0
    assert mt1.json()["data"]["issues_solved"] == ["i7"]
    assert mt1.json()["data"]["todos_created"] == ["t20"]

    mt2 = api_client.get("/api/v1/meetings/mt2/summary", headers=u2_headers)
    assert mt2.status_code == 200
    assert mt2.json()["data"]["rating"] == 8.3
    assert mt2.json()["data"]["issues_solved"] == ["i6"]
    assert mt2.json()["data"]["todos_created"] == ["t30"]

    # Non-member u6 gets 404 on team_lead meetings
    assert api_client.get("/api/v1/meetings/mt1", headers=u6_headers).status_code == 404
    assert api_client.get("/api/v1/meetings/mt1/summary", headers=u6_headers).status_code == 404
    assert (
        api_client.post("/api/v1/teams/team_lead/meetings", headers=u6_headers).status_code == 404
    )
