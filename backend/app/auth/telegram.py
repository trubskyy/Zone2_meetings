"""Verification of Telegram-signed identity payloads.

Two flavours, both HMAC-SHA256 with a key derived from the bot token:
- Mini App `initData` (inside Telegram): secret = HMAC_SHA256(key="WebAppData", msg=bot_token)
- Login Widget (standalone web):        secret = SHA256(bot_token)
See https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
and https://core.telegram.org/widgets/login#checking-authorization
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class TelegramAuthError(ValueError):
    pass


@dataclass(frozen=True)
class TelegramIdentity:
    telegram_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None

    @property
    def display_name(self) -> str:
        return " ".join(p for p in (self.first_name, self.last_name) if p) or (self.username or "Rider")


def _check_fields(fields: dict[str, str], secret: bytes, max_age_s: int, now: float | None) -> None:
    received = fields.pop("hash", None)
    if not received:
        raise TelegramAuthError("missing hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    expected = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise TelegramAuthError("bad signature")
    try:
        auth_date = int(fields["auth_date"])
    except (KeyError, ValueError) as e:
        raise TelegramAuthError("missing auth_date") from e
    if (now or time.time()) - auth_date > max_age_s:
        raise TelegramAuthError("auth data expired")


def verify_webapp_init_data(init_data: str, bot_token: str, max_age_s: int, now: float | None = None) -> TelegramIdentity:
    if not bot_token:
        raise TelegramAuthError("bot token not configured")
    fields = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    _check_fields(fields, secret, max_age_s, now)
    try:
        user = json.loads(fields["user"])
    except (KeyError, json.JSONDecodeError) as e:
        raise TelegramAuthError("missing user") from e
    return TelegramIdentity(
        telegram_id=int(user["id"]),
        first_name=user.get("first_name", ""),
        last_name=user.get("last_name"),
        username=user.get("username"),
        photo_url=user.get("photo_url"),
    )


def verify_login_widget(data: dict, bot_token: str, max_age_s: int, now: float | None = None) -> TelegramIdentity:
    if not bot_token:
        raise TelegramAuthError("bot token not configured")
    fields = {k: str(v) for k, v in data.items() if v is not None}
    secret = hashlib.sha256(bot_token.encode()).digest()
    _check_fields(fields, secret, max_age_s, now)
    return TelegramIdentity(
        telegram_id=int(fields["id"]),
        first_name=fields.get("first_name", ""),
        last_name=fields.get("last_name"),
        username=fields.get("username"),
        photo_url=fields.get("photo_url"),
    )
