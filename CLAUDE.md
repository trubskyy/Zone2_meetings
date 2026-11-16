# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Zone 2 Meeting: people take meetings while exercising at Zone 2 intensity. It ships as a **Telegram Mini App** and a **standalone web app** from one web codebase, with a community program ("Zone 2 Club") around it. Product and technical decisions live in `docs/`. Business, positioning, content and sales live in the separate company repo `~/Documents/Projects/zone2-company` (GitHub `trubskyy/zone2-company`); its `brain/product-facts.md` lists what's shipped, so update it when a feature ships. [docs/architecture.md](docs/architecture.md) is the source of truth for technical choices, and [docs/roadmap.md](docs/roadmap.md) has the current checklist. Update them when you change a decision.

## Commands

```bash
# backend/ (Python 3.11+)
pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload   # API on :8000; there is no module-level `app`
pytest                                           # all tests
pytest tests/test_meetings.py::test_live_room_shares_zone_not_bpm   # single test
python -m app.bot                                # Telegram bot (polling); needs Z2_TELEGRAM_BOT_TOKEN

# web/ (Node 18+)
npm install && npm run dev      # :5173, proxies /api (incl. WebSocket) to :8000
npm run typecheck               # tsc --noEmit; there are no web tests yet
```

Backend settings are env vars prefixed `Z2_` (see `backend/app/config.py`, `backend/.env.example`). Web settings are `VITE_*` (see `web/.env.example`).

## Architecture notes that span files

- **App factory:** `create_app(settings)` stores `settings`, a SQLAlchemy `sessionmaker` and the `LiveHub` on `app.state`. Dependencies (`get_db`, `get_settings_dep`) and the WebSocket handler read from `app.state`, never from module globals. That's how tests get an isolated in-memory DB (`sqlite://` with `StaticPool`) per test. `create_app` refuses to start with the default JWT secret unless `dev_login` is on.
- **Auth:** the Telegram identity is the only identity. `auth/telegram.py` verifies Mini App `initData` (secret = HMAC("WebAppData", token)) and Login Widget payloads (secret = SHA256(token)). Both upsert a `User` by `telegram_id` and return our own JWT. Dev login uses negative `telegram_id`s so it can't collide with real users.
- **Datetimes:** stored as **naive UTC** (`db.utcnow()`). The `UtcDatetime` type in `schemas.py` converts aware input to naive UTC and serializes with a `Z` suffix. Keep this convention; SQLite drops timezone info.
- **Live rooms:** `api/live.py` (WebSocket `/api/meetings/{id}/live?token=`) plus `live.py` (`LiveHub`, `LiveParticipant`). Time between readings is credited to the *previous* reading's zone, capped at `MAX_GAP_S`, so clients must re-send readings periodically. `web/src/useLive.ts` does this every 3 s. Aggregates are written to `Attendance` only when a user's last socket disconnects. The hub is in-memory and single-process by design. The socket is accepted before rejecting with 4401/4403 so browsers see the code; `useLive` doesn't retry those.
- **Privacy rule:** others see a participant's *zone*, and BPM / `avg_hr` only if that user set `share_bpm`. This is enforced in `LiveParticipant.public_state()` and `meeting_summary()`. Keep it when adding endpoints. Raw HR samples are never persisted.
- **Zones:** `zones.py` is pure. It uses Karvonen floors with a Tanaka max-HR estimate, measured `zone2_low/high` override with the ladder kept monotonic, and `EFFORT_ZONES` maps talk-test answers to zones for users without sensors.
- **Audio:** not hosted inside Telegram. A meeting has a `voice_link` (a Telegram voice-chat invite). Standalone audio (LiveKit) is planned, not built.
- **Web:** `telegram.ts` wraps the Mini App SDK so every call is safe outside Telegram. `heartRate.ts` uses Web Bluetooth (Heart Rate service 0x180D), which doesn't exist on iOS, so the talk-test UI must always remain a working fallback. Navigation is a `View` union in `App.tsx` with no router. Invite deep links use the payload `m<id>[_<invite_code>]` via `?startapp=` (Telegram) or `?start=` (web).
- **Schema changes:** tables come from `Base.metadata.create_all`. There are no migrations yet. Introduce Alembic before the first production schema change.

## Repo hygiene

The pre-rewrite prototype and business-plan drafts were deleted on 2026-11-15. They're in git history before commit `24c0ede` if ever needed. Don't revive them.
