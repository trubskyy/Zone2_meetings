"""Deployment wiring: database URLs, migrations, and serving the built web app."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import normalize_database_url
from app.main import create_app

BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "given, expected",
    [
        ("postgres://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
        ("postgresql://u:p@h/db?sslmode=require", "postgresql+psycopg://u:p@h/db?sslmode=require"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("sqlite:///./zone2.db", "sqlite:///./zone2.db"),
    ],
)
def test_normalize_database_url(given, expected):
    assert normalize_database_url(given) == expected


def _alembic(url: str) -> Config:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.attributes["database_url"] = url
    return cfg


def test_migrations_match_models(tmp_path):
    """`alembic upgrade head` must build exactly the schema in app/models.py; otherwise add a migration."""
    cfg = _alembic(f"sqlite:///{tmp_path / 'm.db'}")
    command.upgrade(cfg, "head")
    command.check(cfg)  # raises if models have changes that no migration covers
    command.downgrade(cfg, "base")


def test_single_migration_head():
    assert len(ScriptDirectory.from_config(_alembic("sqlite://")).get_heads()) == 1


def test_serves_web_app_and_api(tmp_path, settings):
    (tmp_path / "index.html").write_text("<!doctype html><title>Zone 2</title>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    with TestClient(create_app(settings.model_copy(update={"static_dir": str(tmp_path)}))) as c:
        assert "Zone 2" in c.get("/").text
        assert "Zone 2" in c.get("/?startapp=m1").text
        assert c.get("/assets/app.js").status_code == 200
        assert c.get("/api/health").json() == {"ok": True}
        assert c.get("/api/does-not-exist").status_code == 404


def test_static_dir_without_build_fails_fast(tmp_path, settings):
    with pytest.raises(RuntimeError, match="index.html"):
        create_app(settings.model_copy(update={"static_dir": str(tmp_path)}))


def test_run_bot_requires_token():
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        create_app(Settings(database_url="sqlite://", dev_login=True, run_bot=True, telegram_bot_token=""))
