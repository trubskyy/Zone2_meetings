from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Naive UTC timestamp. All datetimes are stored naive-UTC so SQLite and Postgres behave alike."""
    return datetime.now(UTC).replace(tzinfo=None)


def normalize_database_url(url: str) -> str:
    """Hosting providers hand out postgres:// or postgresql:// URLs; SQLAlchemy needs the psycopg 3 driver named."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def make_engine(database_url: str) -> Engine:
    database_url = normalize_database_url(database_url)
    kwargs: dict = {}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            # In-memory DB must share one connection across threads (tests).
            kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_pre_ping"] = True
    return create_engine(database_url, **kwargs)


def make_sessionmaker(database_url: str) -> sessionmaker[Session]:
    engine = make_engine(database_url)
    # Import models so they register on Base.metadata.
    from app import models  # noqa: F401

    # SQLite (local dev and tests) creates tables directly. Postgres is managed only by Alembic
    # migrations (`alembic upgrade head`, run at container start); see migrations/.
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.sessionmaker() as db:
        yield db
