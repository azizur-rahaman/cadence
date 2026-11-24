"""Rocks API and RBAC verification tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _auth_headers(api_client: TestClient, user_id: str) -> dict[str, str]:
    resp = api_client.post("/api/v1/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_team_rocks_returns_computed_status_progress_and_milestones(
    api_client: TestClient,
) -> None:
    headers = _auth_headers(api_client, "u2")
    resp = api_client.get("/api/v1/teams/team_lead/rocks", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["quarter"] == "2026-Q4"
    assert data["today"] == "2026-11-11"
    by_id = {r["id"]: r for r in data["items"]}
    assert list(by_id.keys()) == ["r1", "r2", "r3", "r4", "r5"]

    assert by_id["r1"]["status"] == "on_track"
    assert by_id["r1"]["progress_percent"] == 33
    r1_ms = {m["id"]: m for m in by_id["r1"]["milestones"]}
    assert r1_ms["ms2"]["is_past_due"] is False

    assert by_id["r2"]["status"] == "off_track"
    assert by_id["r2"]["progress_percent"] == 13
    r2_ms = {m["id"]: m for m in by_id["r2"]["milestones"]}
    assert r2_ms["ms5"]["is_past_due"] is True

    assert by_id["r3"]["status"] == "complete"
    assert by_id["r3"]["progress_percent"] == 100
    assert by_id["r4"]["status"] == "off_track"
    assert by_id["r4"]["progress_percent"] == 0
    assert by_id["r5"]["status"] == "on_track"
    assert by_id["r5"]["progress_percent"] == 0


def test_rocks_rbac_observer_can_read_non_member_404_admin_all_teams(
    api_client: TestClient,
) -> None:
    u5_headers = _auth_headers(api_client, "u5")
    assert api_client.get("/api/v1/teams/team_lead/rocks", headers=u5_headers).status_code == 200

    u6_headers = _auth_headers(api_client, "u6")
    assert api_client.get("/api/v1/teams/team_lead/rocks", headers=u6_headers).status_code == 404

    u1_headers = _auth_headers(api_client, "u1")
    sales = api_client.get("/api/v1/teams/team_sales/rocks", headers=u1_headers)
    assert sales.status_code == 200
    assert [r["id"] for r in sales.json()["data"]["items"]] == ["r6"]
