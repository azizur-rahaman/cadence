"""Per-meeting WebSocket connection hub and snapshot broadcaster."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import BackgroundTasks, WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Meeting


class MeetingHub:
    """Tracks live WebSocket connections per meeting for sub-second state sync."""

    def __init__(self) -> None:
        self._connections: dict[str, dict[WebSocket, str]] = defaultdict(dict)

    async def connect(self, meeting_id: str, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections[meeting_id][websocket] = user_id

    def disconnect(self, meeting_id: str, websocket: WebSocket) -> None:
        room = self._connections.get(meeting_id)
        if not room:
            return
        room.pop(websocket, None)
        if not room:
            self._connections.pop(meeting_id, None)

    def online_user_ids(self, meeting_id: str) -> list[str]:
        room = self._connections.get(meeting_id)
        if not room:
            return []
        return sorted(set(room.values()))

    async def broadcast(self, meeting_id: str, payload: dict[str, Any]) -> None:
        room = self._connections.get(meeting_id)
        if not room:
            return
        dead: list[WebSocket] = []
        for ws in list(room.keys()):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(meeting_id, ws)


meeting_hub = MeetingHub()


def notify_team_workspace_change(
    background_tasks: BackgroundTasks,
    team_id: str,
    scope: str,
    db: Session,
) -> None:
    """Broadcast a lightweight invalidation event if `team_id` has an active meeting."""
    active_meeting_id = db.execute(
        select(Meeting.id).where(Meeting.team_id == team_id, Meeting.ended_at.is_(None))
    ).scalar_one_or_none()
    if active_meeting_id is not None:
        background_tasks.add_task(
            meeting_hub.broadcast,
            active_meeting_id,
            {"type": "workspace_updated", "scope": scope, "team_id": team_id},
        )
