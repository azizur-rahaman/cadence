"""WebSocket real-time synchronization, auth, and reconnect snapshot tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def _login_token(api_client: TestClient, user_id: str) -> str:
    resp = api_client.post("/api/v1/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200
    return str(resp.json()["data"]["access_token"])


def test_meeting_ws_snapshot_broadcast_and_reconnect(api_client: TestClient) -> None:
    u2_token = _login_token(api_client, "u2")
    u3_token = _login_token(api_client, "u3")
    u2_headers = {"Authorization": f"Bearer {u2_token}"}

    started = api_client.post("/api/v1/teams/team_lead/meetings", headers=u2_headers)
    assert started.status_code == 201
    mt_id = started.json()["data"]["id"]

    with api_client.websocket_connect(f"/api/v1/meetings/{mt_id}/ws?token={u2_token}") as ws1:
        snap1 = ws1.receive_json()
        assert snap1["type"] == "snapshot"
        assert snap1["meeting"]["section"] == "scorecard"
        assert "u2" in snap1["online_user_ids"]
        # Consume own attendee_joined broadcast
        _ = ws1.receive_json()

        with api_client.websocket_connect(
            f"/api/v1/meetings/{mt_id}/ws?token={u3_token}"
        ) as ws2:
            snap2 = ws2.receive_json()
            assert snap2["type"] == "snapshot"
            assert sorted(snap2["online_user_ids"]) == ["u2", "u3"]
            _ = ws2.receive_json()  # attendee_joined
            joined_evt = ws1.receive_json()
            assert joined_evt["type"] == "attendee_joined"
            assert sorted(joined_evt["online_user_ids"]) == ["u2", "u3"]

            # Facilitator advances -> both sockets receive state_updated
            adv = api_client.post(f"/api/v1/meetings/{mt_id}/advance", headers=u2_headers)
            assert adv.status_code == 200

            evt1 = ws1.receive_json()
            evt2 = ws2.receive_json()
            assert evt1["type"] == "state_updated"
            assert evt1["meeting"]["section"] == "ids"
            assert evt2["type"] == "state_updated"
            assert evt2["meeting"]["section"] == "ids"

    # Reconnecting receives a fresh snapshot with current section ("ids")
    with api_client.websocket_connect(f"/api/v1/meetings/{mt_id}/ws?token={u3_token}") as ws3:
        reconnected = ws3.receive_json()
        assert reconnected["type"] == "snapshot"
        assert reconnected["meeting"]["section"] == "ids"
        assert sorted(a["user_id"] for a in reconnected["meeting"]["attendees"]) == ["u2", "u3"]


def test_meeting_ws_rejects_unauthorized_and_non_member(api_client: TestClient) -> None:
    u2_token = _login_token(api_client, "u2")
    u6_token = _login_token(api_client, "u6")
    started = api_client.post(
        "/api/v1/teams/team_lead/meetings",
        headers={"Authorization": f"Bearer {u2_token}"},
    )
    mt_id = started.json()["data"]["id"]

    with (
        pytest.raises(WebSocketDisconnect) as exc_unauth,
        api_client.websocket_connect(f"/api/v1/meetings/{mt_id}/ws?token=invalid"),
    ):
        pass
    assert exc_unauth.value.code == 4401

    with (
        pytest.raises(WebSocketDisconnect) as exc_non_member,
        api_client.websocket_connect(f"/api/v1/meetings/{mt_id}/ws?token={u6_token}"),
    ):
        pass
    assert exc_non_member.value.code == 4404
