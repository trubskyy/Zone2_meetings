"""In-memory live state for meetings in progress.

Single-process by design (see docs/architecture.md, decision 5). Clients send a reading
(HR or self-reported effort) at least every few seconds; time between readings is credited
to the zone of the previous reading, capped at MAX_GAP_S so a dropped client doesn't accrue time.
"""

import asyncio
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.zones import EFFORT_ZONES, ZoneProfile

MAX_GAP_S = 15.0


@dataclass
class LiveParticipant:
    user_id: int
    name: str
    profile: ZoneProfile
    share_bpm: bool
    sockets: set[WebSocket] = field(default_factory=set)
    zone: int | None = None
    bpm: int | None = None
    source: str | None = None  # "hr" | "effort"
    last_ts: float | None = None
    tracked_s: float = 0.0
    zone2_s: float = 0.0
    hr_sum: float = 0.0
    hr_samples: int = 0

    def record(self, *, bpm: int | None = None, effort: str | None = None, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        if self.last_ts is not None and self.zone is not None:
            dt = min(now - self.last_ts, MAX_GAP_S)
            self.tracked_s += dt
            if self.zone == 2:
                self.zone2_s += dt
        self.last_ts = now

        if bpm is not None:
            self.bpm, self.source = bpm, "hr"
            self.zone = self.profile.classify(bpm)
            self.hr_sum += bpm
            self.hr_samples += 1
        elif effort is not None:
            self.bpm, self.source = None, "effort"
            self.zone = EFFORT_ZONES[effort]

    def public_state(self) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "zone": self.zone,
            "bpm": self.bpm if self.share_bpm else None,
            "source": self.source,
            "zone2_pct": round(100 * self.zone2_s / self.tracked_s) if self.tracked_s else None,
        }


class LiveHub:
    def __init__(self) -> None:
        self.rooms: dict[int, dict[int, LiveParticipant]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, meeting_id: int, ws: WebSocket, participant: LiveParticipant) -> LiveParticipant:
        async with self._lock:
            room = self.rooms.setdefault(meeting_id, {})
            existing = room.get(participant.user_id)
            if existing is None:
                room[participant.user_id] = existing = participant
            existing.sockets.add(ws)
            return existing

    async def disconnect(self, meeting_id: int, ws: WebSocket, user_id: int) -> LiveParticipant | None:
        """Remove a socket. Returns the participant if this was their last connection."""
        async with self._lock:
            room = self.rooms.get(meeting_id, {})
            p = room.get(user_id)
            if p is None:
                return None
            p.sockets.discard(ws)
            if p.sockets:
                return None
            del room[user_id]
            if not room:
                self.rooms.pop(meeting_id, None)
            return p

    def state(self, meeting_id: int) -> dict:
        room = self.rooms.get(meeting_id, {})
        return {"type": "state", "participants": [p.public_state() for p in room.values()]}

    async def broadcast(self, meeting_id: int) -> None:
        message = self.state(meeting_id)
        sockets = [ws for p in list(self.rooms.get(meeting_id, {}).values()) for ws in list(p.sockets)]
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                pass  # the socket's own handler will clean up on disconnect
