import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth.tokens import current_user
from app.db import get_db, utcnow
from app.models import Attendance, Meeting, User, Visibility
from app.schemas import AttendanceOut, JoinIn, MeetingCreate, MeetingOut, MeetingSummary, UserPublic

router = APIRouter(prefix="/meetings", tags=["meetings"])

MAX_DURATION = timedelta(minutes=240)


def meeting_out(m: Meeting, viewer: User) -> MeetingOut:
    return MeetingOut(
        id=m.id,
        title=m.title,
        topic=m.topic,
        host=UserPublic.model_validate(m.host),
        starts_at=m.starts_at,
        duration_min=m.duration_min,
        activity=m.activity,
        visibility=m.visibility,
        voice_link=m.voice_link,
        attendee_count=len(m.attendances),
        joined=any(a.user_id == viewer.id for a in m.attendances),
        invite_code=m.invite_code if m.host_id == viewer.id else None,
    )


def _can_see(m: Meeting, user: User, invite_code: str | None = None) -> bool:
    return (
        m.visibility == Visibility.public
        or m.host_id == user.id
        or any(a.user_id == user.id for a in m.attendances)
        or (invite_code is not None and secrets.compare_digest(invite_code, m.invite_code or ""))
    )


def load_meeting(db: Session, meeting_id: int) -> Meeting:
    m = db.scalar(
        select(Meeting)
        .where(Meeting.id == meeting_id)
        .options(selectinload(Meeting.attendances).selectinload(Attendance.user), selectinload(Meeting.host))
    )
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "meeting not found")
    return m


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    mine: bool = Query(False, description="Only meetings I host or joined"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    now = utcnow()
    joined_ids = select(Attendance.meeting_id).where(Attendance.user_id == user.id)
    q = (
        select(Meeting)
        .where(Meeting.starts_at >= now - MAX_DURATION)
        .options(selectinload(Meeting.attendances), selectinload(Meeting.host))
        .order_by(Meeting.starts_at)
    )
    mine_clause = or_(Meeting.host_id == user.id, Meeting.id.in_(joined_ids))
    q = q.where(mine_clause) if mine else q.where(or_(Meeting.visibility == Visibility.public, mine_clause))
    meetings = [m for m in db.scalars(q) if m.starts_at + timedelta(minutes=m.duration_min) > now]
    return [meeting_out(m, user) for m in meetings]


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(body: MeetingCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = Meeting(
        title=body.title,
        topic=body.topic,
        host_id=user.id,
        starts_at=body.starts_at,
        duration_min=body.duration_min,
        activity=body.activity,
        visibility=body.visibility,
        voice_link=str(body.voice_link) if body.voice_link else None,
        invite_code=secrets.token_urlsafe(6) if body.visibility == Visibility.private else None,
    )
    m.attendances.append(Attendance(user_id=user.id))
    db.add(m)
    db.commit()
    return meeting_out(load_meeting(db, m.id), user)


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(
    meeting_id: int,
    invite_code: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    m = load_meeting(db, meeting_id)
    if not _can_see(m, user, invite_code):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "meeting not found")
    return meeting_out(m, user)


@router.post("/{meeting_id}/join", response_model=MeetingOut)
def join_meeting(meeting_id: int, body: JoinIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = load_meeting(db, meeting_id)
    if not _can_see(m, user, body.invite_code):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "meeting not found")
    if not any(a.user_id == user.id for a in m.attendances):
        m.attendances.append(Attendance(user_id=user.id))
        db.commit()
    return meeting_out(load_meeting(db, meeting_id), user)


@router.post("/{meeting_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_meeting(meeting_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    att = db.scalar(select(Attendance).where(Attendance.meeting_id == meeting_id, Attendance.user_id == user.id))
    if att is None:
        return
    if att.tracked_seconds == 0:
        db.delete(att)  # signed up but never rode — just un-RSVP
    else:
        att.left_at = utcnow()
    db.commit()


@router.get("/{meeting_id}/summary", response_model=MeetingSummary)
def meeting_summary(meeting_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = load_meeting(db, meeting_id)
    if not _can_see(m, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "meeting not found")
    attendees = []
    for a in m.attendances:
        out = AttendanceOut.model_validate(a)
        # Average HR is health data: only visible to its owner or if they opted in to sharing.
        if a.user_id != user.id and not a.user.share_bpm:
            out.avg_hr = None
        attendees.append(out)
    total = sum(a.zone2_seconds for a in m.attendances) / 60
    return MeetingSummary(meeting=meeting_out(m, user), attendees=attendees, total_zone2_minutes=round(total, 1))
