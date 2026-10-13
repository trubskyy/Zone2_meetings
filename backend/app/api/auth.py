import zlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.users import user_out
from app.auth.telegram import TelegramAuthError, TelegramIdentity, verify_login_widget, verify_webapp_init_data
from app.auth.tokens import get_settings_dep, issue_token
from app.config import Settings
from app.db import get_db
from app.models import User
from app.schemas import DevAuthIn, LoginWidgetAuthIn, TokenOut, WebAppAuthIn

router = APIRouter(prefix="/auth", tags=["auth"])


def _upsert(db: Session, ident: TelegramIdentity) -> User:
    user = db.scalar(select(User).where(User.telegram_id == ident.telegram_id))
    if user is None:
        user = User(telegram_id=ident.telegram_id, display_name=ident.display_name)
        db.add(user)
    # Keep Telegram-sourced fields fresh; display_name is user-editable after creation.
    user.username = ident.username
    user.photo_url = ident.photo_url
    db.commit()
    db.refresh(user)
    return user


def _token_response(user: User, settings: Settings) -> TokenOut:
    return TokenOut(token=issue_token(user.id, settings), user=user_out(user))


@router.post("/telegram-webapp", response_model=TokenOut)
def telegram_webapp(body: WebAppAuthIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)):
    try:
        ident = verify_webapp_init_data(body.init_data, settings.telegram_bot_token, settings.telegram_auth_max_age_s)
    except TelegramAuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    return _token_response(_upsert(db, ident), settings)


@router.post("/telegram-login", response_model=TokenOut)
def telegram_login(body: LoginWidgetAuthIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)):
    try:
        ident = verify_login_widget(body.model_dump(), settings.telegram_bot_token, settings.telegram_auth_max_age_s)
    except TelegramAuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    return _token_response(_upsert(db, ident), settings)


@router.post("/dev", response_model=TokenOut)
def dev_login(body: DevAuthIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)):
    if not settings.dev_login:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # Negative ids can never collide with real Telegram users.
    telegram_id = body.telegram_id or -zlib.crc32(body.name.encode())
    ident = TelegramIdentity(telegram_id=telegram_id, first_name=body.name)
    return _token_response(_upsert(db, ident), settings)
