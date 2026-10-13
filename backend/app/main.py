from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, live, meetings, users
from app.config import Settings, get_settings
from app.db import make_sessionmaker
from app.live import LiveHub


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.jwt_secret == "change-me" and not settings.dev_login:
        raise RuntimeError("Set Z2_JWT_SECRET before running without Z2_DEV_LOGIN.")
    app = FastAPI(title="Zone 2 Meeting API", version="0.1.0")
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
    return app

