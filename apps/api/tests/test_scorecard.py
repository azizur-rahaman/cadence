"""Scorecard API, RBAC, inline upsert, and 20x concurrent Make it an Issue tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Issue


def _auth_headers(api_client: TestClient, user_id: str) -> dict[str, str]:
    resp = api_client.post("/api/v1/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_scorecard_returns_13_weeks_statuses_and_linked_issues(
    api_client: TestClient,
) -> None:
    headers = _auth_headers(api_client, "u2")
    resp = api_client.get("/api/v1/teams/team_lead/scorecard", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True

    data = body["data"]
    assert data["team_id"] == "team_lead"
    assert data["current_week_start"] == "2026-11-09"
    assert data["last_closed_week_start"] == "2026-11-02"
    assert len(data["weeks"]) == 13
    assert data["weeks"][0] == "2026-08-17"
    assert data["weeks"][-1] == "2026-11-09"

    by_id = {m["id"]: m for m in data["measurables"]}
    assert list(by_id.keys()) == ["m1", "m2", "m3", "m4", "m5"]

    m1_cells = {c["week_start"]: c for c in by_id["m1"]["cells"]}
    assert m1_cells["2026-11-02"]["status"] == "off_track"
    assert m1_cells["2026-11-02"]["unsolved_issue_id"] == "i5"
    assert m1_cells["2026-11-09"]["status"] == "pending"
    assert m1_cells["2026-11-09"]["value"] is None

    # i6 is solved, so (m4, 2026-10-26) must not report an unsolved_issue_id
    m4_cells = {c["week_start"]: c for c in by_id["m4"]["cells"]}
    assert m4_cells["2026-10-26"]["status"] == "off_track"
    assert m4_cells["2026-10-26"]["unsolved_issue_id"] is None

    # m5 has current-week score 520 -> on_track, missing 2026-11-02 -> off_track
    m5_cells = {c["week_start"]: c for c in by_id["m5"]["cells"]}
    assert m5_cells["2026-11-09"]["status"] == "on_track"
    assert m5_cells["2026-11-09"]["value"] == 520.0
    assert m5_cells["2026-11-02"]["status"] == "off_track"
    assert m5_cells["2026-11-02"]["value"] is None


def test_scorecard_rbac_boundaries(api_client: TestClient) -> None:
    # Non-member u6 (team_sales) gets 404 on team_lead
    u6_headers = _auth_headers(api_client, "u6")
    assert (
        api_client.get("/api/v1/teams/team_lead/scorecard", headers=u6_headers).status_code == 404
    )
    assert (
        api_client.put(
            "/api/v1/teams/team_lead/measurables/m1/scores/2026-11-09",
            headers=u6_headers,
            json={"value": 12},
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            "/api/v1/teams/team_lead/issues/from-measurable",
            headers=u6_headers,
            json={"measurable_id": "m5", "week_start": "2026-11-02"},
        ).status_code
        == 404
    )

    # Observer u5 can read team_lead (200), but gets 403 on writes
    u5_headers = _auth_headers(api_client, "u5")
    assert (
        api_client.get("/api/v1/teams/team_lead/scorecard", headers=u5_headers).status_code == 200
    )
    assert (
        api_client.put(
            "/api/v1/teams/team_lead/measurables/m1/scores/2026-11-09",
            headers=u5_headers,
            json={"value": 12},
        ).status_code
        == 403
    )
    assert (
        api_client.post(
            "/api/v1/teams/team_lead/issues/from-measurable",
            headers=u5_headers,
            json={"measurable_id": "m5", "week_start": "2026-11-02"},
        ).status_code
        == 403
    )

    # Admin u1 can read & write team_sales without a membership row
    u1_headers = _auth_headers(api_client, "u1")
    resp = api_client.put(
        "/api/v1/teams/team_sales/measurables/m6/scores/2026-11-09",
        headers=u1_headers,
        json={"value": 55},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "on_track"


def test_upsert_score_recomputes_status_and_validates_monday(api_client: TestClient) -> None:
    headers = _auth_headers(api_client, "u2")

    # Non-Monday rejected with 422
    bad_day = api_client.put(
        "/api/v1/teams/team_lead/measurables/m1/scores/2026-11-10",
        headers=headers,
        json={"value": 12},
    )
    assert bad_day.status_code == 422
    assert bad_day.json()["error"]["code"] == "VALIDATION_ERROR"

    # Cross-team measurable rejected with 404
    wrong_team = api_client.put(
        "/api/v1/teams/team_lead/measurables/m6/scores/2026-11-09",
        headers=headers,
        json={"value": 55},
    )
    assert wrong_team.status_code == 404

    # Upsert m1 current week: 12 -> on_track, then 8 -> off_track
    r1 = api_client.put(
        "/api/v1/teams/team_lead/measurables/m1/scores/2026-11-09",
        headers=headers,
        json={"value": 12},
    )
    assert r1.status_code == 200
    assert r1.json()["data"] == {
        "measurable_id": "m1",
        "week_start": "2026-11-09",
        "value": 12.0,
        "status": "on_track",
        "unsolved_issue_id": None,
    }

    r2 = api_client.put(
        "/api/v1/teams/team_lead/measurables/m1/scores/2026-11-09",
        headers=headers,
        json={"value": 8},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "off_track"


def test_make_issue_from_measurable_dedup_solved_recreate_and_validation(
    api_client: TestClient,
) -> None:
    headers = _auth_headers(api_client, "u2")

    # Pre-existing unsolved i5 on (m1, 2026-11-02) -> 200 OK with existing i5
    existing = api_client.post(
        "/api/v1/teams/team_lead/issues/from-measurable",
        headers=headers,
        json={"measurable_id": "m1", "week_start": "2026-11-02"},
    )
    assert existing.status_code == 200
    assert existing.json()["data"]["created"] is False
    assert existing.json()["data"]["issue"]["id"] == "i5"

    # Previously solved i6 on (m4, 2026-10-26) -> 201 Created with new Issue
    recreated = api_client.post(
        "/api/v1/teams/team_lead/issues/from-measurable",
        headers=headers,
        json={"measurable_id": "m4", "week_start": "2026-10-26"},
    )
    assert recreated.status_code == 201
    new_issue = recreated.json()["data"]["issue"]
    assert recreated.json()["data"]["created"] is True
    assert new_issue["id"] != "i6"
    assert new_issue["title"] == "Payroll runs, week of Oct 26"
    assert new_issue["source"] == {"measurable_id": "m4", "week_start": "2026-10-26"}

    # On-track cell rejected with 422
    on_track = api_client.post(
        "/api/v1/teams/team_lead/issues/from-measurable",
        headers=headers,
        json={"measurable_id": "m5", "week_start": "2026-11-09"},
    )
    assert on_track.status_code == 422

    # Pending cell rejected with 422
    pending = api_client.post(
        "/api/v1/teams/team_lead/issues/from-measurable",
        headers=headers,
        json={"measurable_id": "m1", "week_start": "2026-11-09"},
    )
    assert pending.status_code == 422


def test_make_issue_from_measurable_20x_concurrent_atomic_dedup(
    api_client: TestClient, seeded_db: Session
) -> None:
    """20 simultaneous requests for the same off-track cell must yield 1x 201 + 19x 200."""
    headers = _auth_headers(api_client, "u2")
    workers = 20
    barrier = Barrier(workers)

    def _fire(_: int) -> tuple[int, bool, str]:
        barrier.wait()
        resp = api_client.post(
            "/api/v1/teams/team_lead/issues/from-measurable",
            headers=headers,
            json={"measurable_id": "m5", "week_start": "2026-11-02"},
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()["data"]
        return resp.status_code, data["created"], data["issue"]["id"]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_fire, range(workers)))

    statuses = [r[0] for r in results]
    created_flags = [r[1] for r in results]
    issue_ids = {r[2] for r in results}

    assert statuses.count(201) == 1
    assert statuses.count(200) == workers - 1
    assert created_flags.count(True) == 1
    assert created_flags.count(False) == workers - 1
    assert len(issue_ids) == 1

    # Confirm PostgreSQL holds exactly 1 unsolved linked issue for (m5, 2026-11-02)
    seeded_db.expire_all()
    count = seeded_db.execute(
        select(func.count())
        .select_from(Issue)
        .where(
            Issue.source_measurable_id == "m5",
            Issue.source_week_start == date(2026, 11, 2),
            Issue.solved_at.is_(None),
        )
    ).scalar_one()
    assert count == 1
