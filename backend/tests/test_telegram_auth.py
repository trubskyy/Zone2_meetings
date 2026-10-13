import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.auth.telegram import TelegramAuthError, verify_login_widget, verify_webapp_init_data
from tests.conftest import BOT_TOKEN


def _sign(fields: dict, secret: bytes) -> str:
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    return hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()


def make_init_data(user: dict, token: str = BOT_TOKEN, auth_date: int | None = None) -> str:
    fields = {"auth_date": str(auth_date or int(time.time())), "query_id": "AAE", "user": json.dumps(user)}
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = _sign(fields, secret)
    return urlencode(fields)


def make_widget(data: dict, token: str = BOT_TOKEN) -> dict:
    fields = {k: str(v) for k, v in data.items()}
    fields["hash"] = _sign(fields, hashlib.sha256(token.encode()).digest())
    return fields


def test_webapp_init_data_valid():
    ident = verify_webapp_init_data(make_init_data({"id": 42, "first_name": "Ana"}), BOT_TOKEN, 3600)
    assert ident.telegram_id == 42
    assert ident.display_name == "Ana"


def test_webapp_init_data_rejects_wrong_token_and_tampering():
    data = make_init_data({"id": 42, "first_name": "Ana"}, token="999:OTHER")
    with pytest.raises(TelegramAuthError):
        verify_webapp_init_data(data, BOT_TOKEN, 3600)
    good = make_init_data({"id": 42, "first_name": "Ana"})
    with pytest.raises(TelegramAuthError):
        verify_webapp_init_data(good.replace("Ana", "Eve"), BOT_TOKEN, 3600)


def test_webapp_init_data_expired():
    old = make_init_data({"id": 1, "first_name": "A"}, auth_date=int(time.time()) - 7200)
    with pytest.raises(TelegramAuthError, match="expired"):
        verify_webapp_init_data(old, BOT_TOKEN, 3600)


def test_login_widget_valid():
    data = make_widget({"id": 7, "first_name": "Bo", "username": "bo", "auth_date": int(time.time())})
    ident = verify_login_widget(data, BOT_TOKEN, 3600)
    assert (ident.telegram_id, ident.username) == (7, "bo")


def test_api_webapp_login_creates_user_once(client):
    init = make_init_data({"id": 555, "first_name": "Cy", "username": "cy"})
    a = client.post("/api/auth/telegram-webapp", json={"init_data": init}).json()
    b = client.post("/api/auth/telegram-webapp", json={"init_data": init}).json()
    assert a["user"]["id"] == b["user"]["id"]
    assert a["user"]["zones"]["zones"][1]["zone"] == 2
    bad = client.post("/api/auth/telegram-webapp", json={"init_data": init + "x"})
    assert bad.status_code == 401
