import enum
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, utcnow


class Activity(enum.StrEnum):
    bike = "bike"
    treadmill = "treadmill"
    walk = "walk"
    run = "run"
    any = "any"


class Visibility(enum.StrEnum):
    public = "public"
    private = "private"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64))
    photo_url: Mapped[str | None] = mapped_column(String(512))

    # Zone inputs; all optional; see app/zones.py for how defaults are derived.
    birth_year: Mapped[int | None]
    resting_hr: Mapped[int | None]
    max_hr: Mapped[int | None]
    zone2_low: Mapped[int | None]
    zone2_high: Mapped[int | None]
    share_bpm: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(140))
    topic: Mapped[str] = mapped_column(String(2000), default="")
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    starts_at: Mapped[datetime]
    duration_min: Mapped[int] = mapped_column(default=45)
    activity: Mapped[Activity] = mapped_column(default=Activity.any)
    visibility: Mapped[Visibility] = mapped_column(default=Visibility.public)
    invite_code: Mapped[str | None] = mapped_column(String(32), index=True)
    # Telegram voice-chat invite link (or any audio link) — we don't host audio inside Telegram.
    voice_link: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    host: Mapped[User] = relationship()
    attendances: Mapped[list["Attendance"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("meeting_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(default=utcnow)
    left_at: Mapped[datetime | None]

    # Aggregates only — raw HR samples are not persisted (see docs/risks-and-safety.md).
    samples: Mapped[int] = mapped_column(default=0)
    avg_hr: Mapped[float | None]
    tracked_seconds: Mapped[float] = mapped_column(default=0.0)
    zone2_seconds: Mapped[float] = mapped_column(default=0.0)

    meeting: Mapped[Meeting] = relationship(back_populates="attendances")
    user: Mapped[User] = relationship()
