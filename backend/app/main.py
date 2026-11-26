import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, live, meetings, users
from app.config import Settings, get_settings
from app.db import make_sessionmaker
from app.live import LiveHub

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.jwt_secret == "change-me" and not settings.dev_login:
        raise RuntimeError("Set Z2_JWT_SECRET before running without Z2_DEV_LOGIN.")
    if settings.run_bot and not settings.telegram_bot_token:
        raise RuntimeError("Z2_RUN_BOT needs Z2_TELEGRAM_BOT_TOKEN.")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        bot = None
        if settings.run_bot:
            from app import bot as bot_module

            bot = bot_module.build_application(settings, app.state.sessionmaker)
            await bot_module.start_polling(bot)
            log.info("Telegram bot polling started")
        try:
            yield
        finally:
            if bot is not None:
                await bot_module.stop_polling(bot)

    app = FastAPI(title="Zone 2 Meeting API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.sessionmaker = make_sessionmaker(settings.database_url)
    app.state.hub = LiveHub()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health():
        return {"ok": True}

    for module in (auth, users, meetings, live):
        api.include_router(module.router)
    app.include_router(api)

    if settings.static_dir:
        static = Path(settings.static_dir)
        if not (static / "index.html").is_file():
            raise RuntimeError(f"Z2_STATIC_DIR={static} has no index.html; build the web app first.")
        # Mounted last so /api routes win. The web app has no client-side router, so html=True is enough.
        app.mount("/", StaticFiles(directory=static, html=True), name="web")
    return app
