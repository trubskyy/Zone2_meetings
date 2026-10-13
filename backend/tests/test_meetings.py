from datetime import UTC, datetime, timedelta

import pytest
from starlette.websockets import WebSocketDisconnect


def _soon(minutes: int = 10) -> str:
    return (datetime.now(UTC) + timedelta(minutes=minutes)).isoformat()


def _create(client, headers, **kw):
    body = {"title": "Founders ride", "starts_at": _soon(), "activity": "bike", **kw}
    r = client.post("/api/meetings", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_requires_auth(client):
    assert client.get("/api/meetings").status_code == 401


def test_dev_login_disabled_by_default(client, settings):
    settings.dev_login = False
    assert client.post("/api/auth/dev", json={"name": "x"}).status_code == 404


def test_create_list_join_leave(client, login):
    host, _, _ = login("Host")
    guest, _, _ = login("Guest")
    m = _create(client, host, voice_link="https://t.me/zone2club?videochat")
    assert m["joined"] and m["attendee_count"] == 1 and m["starts_at"].endswith("Z")

    listed = client.get("/api/meetings", headers=guest).json()
    assert [x["id"] for x in listed] == [m["id"]]
    assert not listed[0]["joined"]

    joined = client.post(f"/api/meetings/{m['id']}/join", json={}, headers=guest).json()
    assert joined["joined"] and joined["attendee_count"] == 2
    assert client.get("/api/meetings?mine=true", headers=guest).json()[0]["id"] == m["id"]

    assert client.post(f"/api/meetings/{m['id']}/leave", headers=guest).status_code == 204
    assert client.get(f"/api/meetings/{m['id']}", headers=guest).json()["attendee_count"] == 1


def test_finished_meetings_drop_off_the_list(client, login):
    h, _, _ = login("Host")
    _create(client, h, starts_at=(datetime.now(UTC) - timedelta(hours=2)).isoformat(), duration_min=30)
    assert client.get("/api/meetings", headers=h).json() == []


def test_private_meeting_needs_invite_code(client, login):
    host, _, _ = login("Host")
    guest, _, _ = login("Guest")
    m = _create(client, host, visibility="private")
    code = m["invite_code"]
    assert code
    assert client.get("/api/meetings", headers=guest).json() == []
    assert client.get(f"/api/meetings/{m['id']}", headers=guest).status_code == 404
    assert client.post(f"/api/meetings/{m['id']}/join", json={"invite_code": "nope"}, headers=guest).status_code == 404
    seen = client.get(f"/api/meetings/{m['id']}?invite_code={code}", headers=guest).json()
    assert seen["invite_code"] is None  # only the host sees the code
    assert client.post(f"/api/meetings/{m['id']}/join", json={"invite_code": code}, headers=guest).json()["joined"]


def test_profile_update_changes_zones(client, login):
    h, _, _ = login("Ana")
    r = client.patch("/api/me", json={"resting_hr": 50, "max_hr": 190, "share_bpm": True}, headers=h)
    me = r.json()
    assert me["share_bpm"] and me["zones"]["max_hr"] == 190 and not me["zones"]["estimated"]
    bad = client.patch("/api/me", json={"zone2_low": 150, "zone2_high": 140}, headers=h)
    assert bad.status_code == 422


def test_live_room_shares_zone_not_bpm(client, login):
    host, host_token, host_user = login("Host")
    guest, guest_token, _ = login("Guest")
    m = _create(client, host)
    url = f"/api/meetings/{m['id']}/live"

    with pytest.raises(WebSocketDisconnect) as exc:  # not joined yet
        with client.websocket_connect(f"{url}?token={guest_token}") as ws:
            ws.receive_json()
    assert exc.value.code == 4403
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"{url}?token=garbage") as ws:
            ws.receive_json()
    assert exc.value.code == 4401

    with client.websocket_connect(f"{url}?token={host_token}") as ws:
        assert ws.receive_json()["participants"][0]["zone"] is None
        ws.send_json({"type": "hr", "bpm": 135})
        state = ws.receive_json()
        me = state["participants"][0]
        assert me["user_id"] == host_user["id"] and me["zone"] == 2 and me["bpm"] is None
        ws.send_json({"type": "effort", "level": "breathless"})
        assert ws.receive_json()["participants"][0]["zone"] == 4
        ws.send_json({"type": "hr", "bpm": 5})
        assert ws.receive_json()["type"] == "error"

    summary = client.get(f"/api/meetings/{m['id']}/summary", headers=host).json()
    me = summary["attendees"][0]
    assert me["avg_hr"] == 135.0 and me["left_at"] is not None

    client.post(f"/api/meetings/{m['id']}/join", json={}, headers=guest)
    others_view = client.get(f"/api/meetings/{m['id']}/summary", headers=guest).json()
    host_row = next(a for a in others_view["attendees"] if a["user"]["id"] == host_user["id"])
    assert host_row["avg_hr"] is None  # host hasn't opted in to sharing BPM
