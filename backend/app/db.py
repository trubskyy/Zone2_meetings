from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Naive UTC timestamp. All datetimes are stored naive-UTC so SQLite and Postgres behave alike."""
    return datetime.now(UTC).replace(tzinfo=None)


def make_sessionmaker(database_url: str) -> sessionmaker[Session]:
    kwargs: dict = {}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            # In-memory DB must share one connection across threads (tests).
            kwargs["poolclass"] = StaticPool
    engine = create_engine(database_url, **kwargs)
    # Import models so they register on Base.metadata before create_all.
    from app import models  # noqa: F401

    # Phase 1 uses create_all; switch to Alembic migrations before the first production schema change.
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.sessionmaker() as db:
        yield db
