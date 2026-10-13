from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl, PlainSerializer, model_validator

from app.models import Activity, Visibility


def _to_naive_utc(d: datetime) -> datetime:
    return d.astimezone(UTC).replace(tzinfo=None) if d.tzinfo else d


# Stored naive-UTC (see app.db.utcnow); always serialized with an explicit Z.
UtcDatetime = Annotated[
    datetime,
    AfterValidator(_to_naive_utc),
    PlainSerializer(lambda d: d.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z"), return_type=str),
]


# --- auth ---

class WebAppAuthIn(BaseModel):
    init_data: str


class LoginWidgetAuthIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    first_name: str = ""
    auth_date: int
    hash: str


class DevAuthIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    telegram_id: int | None = None


class TokenOut(BaseModel):
    token: str
    user: "UserOut"


# --- users ---

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    display_name: str
    username: str | None = None
    photo_url: str | None = None


class UserOut(UserPublic):
    birth_year: int | None = None
    resting_hr: int | None = None
    max_hr: int | None = None
    zone2_low: int | None = None
    zone2_high: int | None = None
    share_bpm: bool = False
    zones: dict | None = None


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=128)
    birth_year: int | None = Field(None, ge=1900, le=2020)
    resting_hr: int | None = Field(None, ge=30, le=120)
    max_hr: int | None = Field(None, ge=100, le=230)
    zone2_low: int | None = Field(None, ge=60, le=200)
    zone2_high: int | None = Field(None, ge=60, le=210)
    share_bpm: bool | None = None

    @model_validator(mode="after")
    def _zone2_order(self):
        if self.zone2_low and self.zone2_high and self.zone2_low >= self.zone2_high:
            raise ValueError("zone2_low must be below zone2_high")
        return self


# --- meetings ---

class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    topic: str = Field("", max_length=2000)
    starts_at: UtcDatetime
    duration_min: int = Field(45, ge=10, le=240)
    activity: Activity = Activity.any
    visibility: Visibility = Visibility.public
    voice_link: HttpUrl | None = None


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    topic: str
    host: UserPublic
    starts_at: UtcDatetime
    duration_min: int
    activity: Activity
    visibility: Visibility
    voice_link: str | None
    attendee_count: int = 0
    joined: bool = False
    # Only returned to the host.
    invite_code: str | None = None


class JoinIn(BaseModel):
    invite_code: str | None = None


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user: UserPublic
    joined_at: UtcDatetime
    left_at: UtcDatetime | None
    avg_hr: float | None
    tracked_seconds: float
    zone2_seconds: float


class MeetingSummary(BaseModel):
    meeting: MeetingOut
    attendees: list[AttendanceOut]
    total_zone2_minutes: float


TokenOut.model_rebuild()
