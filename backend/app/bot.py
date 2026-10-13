"""Telegram bot: the front door to the Mini App.

Run with `python -m app.bot`. It reads the same DB as the API (Z2_DATABASE_URL).
Telegram requires the Mini App URL (Z2_WEB_APP_URL) to be HTTPS — use a tunnel in development.
"""

import logging
from datetime import timedelta

from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import get_settings
from app.db import make_sessionmaker, utcnow
from app.models import Meeting, Visibility

log = logging.getLogger(__name__)

WELCOME = (
    "Welcome to Zone 2 Club 🚴‍♀️🏃\n\n"
    "Take meetings while you ride, walk or run at an easy, conversational pace.\n"
    "If you can talk in full sentences but couldn't sing, you're probably in Zone 2.\n\n"
    "/sessions — upcoming public sessions"
)


def _open_button(url: str, text: str = "Open Zone 2 Club") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, web_app=WebAppInfo(url=url))]])


def build_application() -> Application:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("Set Z2_TELEGRAM_BOT_TOKEN to run the bot.")
    sessionmaker = make_sessionmaker(settings.database_url)
    web_app_url = settings.web_app_url

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(WELCOME, reply_markup=_open_button(web_app_url))

    async def sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        now = utcnow()
        with sessionmaker() as db:
            upcoming = db.scalars(
                select(Meeting)
                .where(Meeting.visibility == Visibility.public, Meeting.starts_at >= now - timedelta(minutes=30))
                .order_by(Meeting.starts_at)
                .limit(10)
            ).all()
            lines = [f"• {m.starts_at:%a %d %b %H:%M} UTC — {m.title} ({m.activity.value})" for m in upcoming]
        text = "Upcoming sessions:\n" + "\n".join(lines) if lines else "No sessions scheduled yet — host one!"
        await update.effective_message.reply_text(text, reply_markup=_open_button(web_app_url, "Join or host"))

    async def post_init(app: Application) -> None:
        # Adds the persistent "Open" button next to the chat input.
        await app.bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Open", web_app=WebAppInfo(url=web_app_url)))

    application = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sessions", sessions))
    return application


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    build_application().run_polling()


if __name__ == "__main__":
    main()
