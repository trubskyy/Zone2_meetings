import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

BOT_TOKEN = "123456:TEST-TOKEN"


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", dev_login=True, telegram_bot_token=BOT_TOKEN, jwt_secret="test-secret-that-is-at-least-32-bytes-long")


@pytest.fixture
def client(settings) -> TestClient:
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def login(client):
    """login("Ana") -> (auth headers, token, user json)"""

    def _login(name: str):
        r = client.post("/api/auth/dev", json={"name": name})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        return {"Authorization": f"Bearer {token}"}, token, r.json()["user"]

    return _login
