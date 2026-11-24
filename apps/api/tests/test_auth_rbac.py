"""Tests for signed-token authentication, centralized RBAC, team isolation, and error envelope."""

from __future__ import annotations

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.deps import TeamAccessContext, assert_eligible_team_owner, require_team_write
from app.clock import FrozenClock, get_clock
from app.errors import AppError
from app.main import create_app


def _login_headers(client: TestClient, user_id: str) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"user_id": user_id})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_seeded_users_and_login_by_id_or_case_insensitive_email(
    api_client: TestClient,
) -> None:
    users_res = api_client.get("/api/v1/auth/users")
    assert users_res.status_code == 200
    users = users_res.json()
    assert [u["id"] for u in users] == ["u1", "u2", "u3", "u4", "u5", "u6", "u7", "u8", "u9"]

    by_id = api_client.post("/api/v1/auth/login", json={"user_id": "u2"})
    assert by_id.status_code == 200
    data = by_id.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["id"] == "u2"
    assert sorted(t["id"] for t in data["user"]["teams"]) == ["team_lead", "team_sales"]

    by_email = api_client.post("/api/v1/auth/login", json={"email": "BLAKE@ACME.TEST"})
    assert by_email.status_code == 200
    assert by_email.json()["user"]["id"] == "u2"


def test_login_validation_and_invalid_credentials_error_envelope(api_client: TestClient) -> None:
    empty_res = api_client.post("/api/v1/auth/login", json={})
    assert empty_res.status_code == 422
    body = empty_res.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "message" in body
    assert "fields" in body

    unknown_res = api_client.post("/api/v1/auth/login", json={"user_id": "u999"})
    assert unknown_res.status_code == 401
    assert unknown_res.json() == {
        "code": "INVALID_CREDENTIALS",
        "message": "Unknown user.",
    }


def test_missing_or_tampered_token_returns_401(api_client: TestClient) -> None:
    for path in ("/api/v1/me", "/api/v1/teams", "/api/v1/teams/team_lead"):
        res = api_client.get(path)
        assert res.status_code == 401
        assert res.json()["code"] == "UNAUTHORIZED"

    valid_headers = _login_headers(api_client, "u2")
    tampered_token = valid_headers["Authorization"] + "tampered"
    bad_res = api_client.get("/api/v1/me", headers={"Authorization": tampered_token})
    assert bad_res.status_code == 401
    assert bad_res.json()["code"] == "UNAUTHORIZED"


def test_team_isolation_and_admin_all_team_access(api_client: TestClient) -> None:
    # Admin u1 sees all 3 teams even though seed membership only lists team_lead
    u1_headers = _login_headers(api_client, "u1")
    u1_teams = api_client.get("/api/v1/teams", headers=u1_headers)
    assert u1_teams.status_code == 200
    assert sorted(t["id"] for t in u1_teams.json()) == ["team_lead", "team_ops", "team_sales"]
    for tid in ("team_lead", "team_sales", "team_ops"):
        assert api_client.get(f"/api/v1/teams/{tid}", headers=u1_headers).status_code == 200

    # Team Member u6 (Sales only) gets 404 on Leadership and guessed IDs
    u6_headers = _login_headers(api_client, "u6")
    assert [t["id"] for t in api_client.get("/api/v1/teams", headers=u6_headers).json()] == [
        "team_sales"
    ]
    assert api_client.get("/api/v1/teams/team_sales", headers=u6_headers).status_code == 200

    for forbidden_team in ("team_lead", "team_ops", "team_does_not_exist"):
        res = api_client.get(f"/api/v1/teams/{forbidden_team}", headers=u6_headers)
        assert res.status_code == 404
        assert res.json() == {"code": "TEAM_NOT_FOUND", "message": "Team not found."}

    # Observer u5 (Leadership only) can read team_lead, gets 404 on team_sales
    u5_headers = _login_headers(api_client, "u5")
    assert api_client.get("/api/v1/teams/team_lead", headers=u5_headers).status_code == 200
    assert api_client.get("/api/v1/teams/team_sales", headers=u5_headers).status_code == 404


def test_require_team_write_enforces_403_for_observer_and_404_for_non_member(
    seeded_db: Session, frozen_clock: FrozenClock
) -> None:
    _ = seeded_db
    app = create_app()
    app.dependency_overrides[get_clock] = lambda: frozen_clock

    @app.post("/api/v1/teams/{team_id}/_write-probe")
    def write_probe(ctx: TeamAccessContext = Depends(require_team_write)) -> dict[str, str]:
        return {"user_id": ctx.user.id, "team_id": ctx.team.id}

    with TestClient(app) as client:
        # Observer u5 in own team -> 403 FORBIDDEN
        u5_headers = _login_headers(client, "u5")
        obs_own = client.post("/api/v1/teams/team_lead/_write-probe", headers=u5_headers)
        assert obs_own.status_code == 403
        assert obs_own.json()["code"] == "FORBIDDEN"

        # Observer u5 in non-member team -> 404 TEAM_NOT_FOUND (no existence leak)
        obs_other = client.post("/api/v1/teams/team_sales/_write-probe", headers=u5_headers)
        assert obs_other.status_code == 404
        assert obs_other.json()["code"] == "TEAM_NOT_FOUND"

        # Team Member u2 writes own teams (lead + sales), 404 on ops
        u2_headers = _login_headers(client, "u2")
        res_lead = client.post("/api/v1/teams/team_lead/_write-probe", headers=u2_headers)
        res_sales = client.post("/api/v1/teams/team_sales/_write-probe", headers=u2_headers)
        res_ops = client.post("/api/v1/teams/team_ops/_write-probe", headers=u2_headers)
        assert res_lead.status_code == 200
        assert res_sales.status_code == 200
        assert res_ops.status_code == 404

        # Admin u1 writes all 3 teams including sales & ops
        u1_headers = _login_headers(client, "u1")
        for tid in ("team_lead", "team_sales", "team_ops"):
            res = client.post(f"/api/v1/teams/{tid}/_write-probe", headers=u1_headers)
            assert res.status_code == 200


def test_eligible_team_owners_includes_all_admins_and_rejects_observers_or_outsiders(
    api_client: TestClient, seeded_db: Session
) -> None:
    u1_headers = _login_headers(api_client, "u1")

    lead_owners = api_client.get("/api/v1/teams/team_lead/owners", headers=u1_headers)
    assert lead_owners.status_code == 200
    assert [u["id"] for u in lead_owners.json()] == ["u1", "u2", "u3", "u4"]

    # Admin u1 MUST be eligible on team_sales & team_ops; Observers u5/u7 excluded
    sales_owners = api_client.get("/api/v1/teams/team_sales/owners", headers=u1_headers)
    assert [u["id"] for u in sales_owners.json()] == ["u1", "u2", "u6"]

    ops_owners = api_client.get("/api/v1/teams/team_ops/owners", headers=u1_headers)
    assert [u["id"] for u in ops_owners.json()] == ["u1", "u4", "u8", "u9"]

    # Direct validator checks
    assert assert_eligible_team_owner("u1", "team_sales", "co_1", seeded_db).id == "u1"
    for invalid_owner in ("u5", "u6", "u7"):
        with pytest.raises(AppError) as exc_info:
            assert_eligible_team_owner(invalid_owner, "team_lead", "co_1", seeded_db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.fields and "owner_id" in exc_info.value.fields
