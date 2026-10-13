from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.auth.tokens import decode_token
from app.db import utcnow
from app.live import LiveHub, LiveParticipant
from app.models import Attendance, User
from app.zones import EFFORT_ZONES, profile_for_user

router = APIRouter(tags=["live"])

# Close codes in the 4000 range are application-defined.
CLOSE_UNAUTHORIZED = 4401
CLOSE_NOT_JOINED = 4403


@router.websocket("/meetings/{meeting_id}/live")
async def live(ws: WebSocket, meeting_id: int, token: str = ""):
    settings = ws.app.state.settings
    hub: LiveHub = ws.app.state.hub
    sessionmaker = ws.app.state.sessionmaker

    # Accept before closing so browsers see our 44xx code instead of a generic handshake failure (1006).
    await ws.accept()
    user_id = decode_token(token, settings)
    with sessionmaker() as db:
        user = db.get(User, user_id) if user_id else None
        if user is None:
            await ws.close(code=CLOSE_UNAUTHORIZED)
            return
        joined = db.scalar(
            select(Attendance.id).where(Attendance.meeting_id == meeting_id, Attendance.user_id == user.id)
        )
        if joined is None:
            await ws.close(code=CLOSE_NOT_JOINED)
            return
        participant = LiveParticipant(
            user_id=user.id, name=user.display_name, profile=profile_for_user(user), share_bpm=user.share_bpm
        )

    participant = await hub.connect(meeting_id, ws, participant)
    await hub.broadcast(meeting_id)
    try:
        while True:
            msg = await ws.receive_json()
            kind = msg.get("type") if isinstance(msg, dict) else None
            if kind == "hr" and isinstance(msg.get("bpm"), int) and 30 <= msg["bpm"] <= 230:
                participant.record(bpm=msg["bpm"])
            elif kind == "effort" and msg.get("level") in EFFORT_ZONES:
                participant.record(effort=msg["level"])
            else:
                await ws.send_json({"type": "error", "detail": "expected {type: hr, bpm} or {type: effort, level}"})
                continue
            await hub.broadcast(meeting_id)
    except (WebSocketDisconnect, ValueError):  # ValueError: client sent non-JSON
        pass
    finally:
        last = await hub.disconnect(meeting_id, ws, participant.user_id)
        if last is not None:
            _persist(sessionmaker, meeting_id, last)
            await hub.broadcast(meeting_id)


def _persist(sessionmaker, meeting_id: int, p: LiveParticipant) -> None:
    with sessionmaker() as db:
        att = db.scalar(select(Attendance).where(Attendance.meeting_id == meeting_id, Attendance.user_id == p.user_id))
        if att is None:
            return
        if p.hr_samples:
            prev_sum = (att.avg_hr or 0) * att.samples
            att.samples += p.hr_samples
            att.avg_hr = round((prev_sum + p.hr_sum) / att.samples, 1)
        att.tracked_seconds += p.tracked_s
        att.zone2_seconds += p.zone2_s
        att.left_at = utcnow()
        db.commit()
