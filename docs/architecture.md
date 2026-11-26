# Architecture

This is the single source of truth for technical decisions. It replaces the three conflicting plans that came before it (FlutterFlow/Supabase, FastAPI/Agora, Zoom/Teams apps).

## Decisions

| # | Decision | Why |
|---|---|---|
| 1 | **One web front end** (React + TypeScript + Vite) runs as the Telegram Mini App *and* the standalone PWA. | One codebase serves both surfaces. Telegram Mini Apps are web pages. |
| 2 | **Python backend: FastAPI + SQLAlchemy 2.** SQLite in development, Postgres in production. | It's async, so WebSockets fit naturally. It keeps the team's Python knowledge. Managed Postgres (Neon or Supabase) works as-is. |
| 3 | **One identity: the Telegram account.** In the Mini App we verify `initData`. Standalone uses the Telegram Login Widget. Both are HMAC-checked with the bot token, and the server issues its own JWT. | Same user on both surfaces, and no passwords. Email login can come later for teams. |
| 4 | **Audio isn't ours inside Telegram.** A meeting stores a `voice_link` to a Telegram group voice chat. Standalone audio (LiveKit) comes in a later phase. | The Bot API appears not to let bots start or join voice chats, and Telegram's native voice chat is free and reliable. |
| 5 | **Live zone data goes over a WebSocket per meeting.** State lives in process memory (`LiveHub`); session totals are written to the DB when someone leaves. | This is the simplest thing that works on one server. Swap in Redis pub/sub when we run more than one. |
| 6 | **Heart rate comes from the client.** Sources in order of priority: (a) Web Bluetooth heart-rate strap on desktop Chrome or Android Chrome; (b) self-reported effort or talk test; (c) later, a native companion for iOS, HealthKit and Wear. Garmin, Strava and Apple cloud APIs are used **only for after-session recaps**. | Cloud fitness APIs aren't real-time. iOS web views (including Telegram's) have no Web Bluetooth. |
| 7 | **Zones are personal.** Default zones use the Karvonen method (percent of heart-rate reserve) with an age-based max-HR estimate (Tanaka formula). Users can override the Zone 2 bounds with lab or field test results. | Fixed BPM cutoffs are wrong for most people. |
| 8 | **Privacy by default.** Other participants see your *zone*; your BPM is shown only if you set `share_bpm`. | Heart rate is health data, and showing it to coworkers raises workplace-surveillance concerns. |
| 9 | **One container, one origin.** The API serves the built web app and runs the bot in-process; Alembic migrates Postgres at start. Fly.io, one always-on machine. See `deploy.md`. | No CORS or WebSocket proxying between two hosts, one thing to deploy, and the in-memory `LiveHub` and polling bot need exactly one process anyway. |

## Layout

```
backend/            FastAPI app (Python 3.11+)
  app/
    main.py         create_app(): wires settings, DB, routers
    config.py       Settings (env vars, prefix Z2_)
    db.py           engine/session factory stored on app.state
    models.py       User, Meeting, Attendance
    schemas.py      Pydantic request/response models
    zones.py        pure zone maths (Karvonen, Tanaka, effort mapping)
    auth/           Telegram initData + Login Widget verification, JWT
    api/            routers: auth, me, meetings, live (WebSocket)
    live.py         LiveHub: in-memory room state and broadcasting
    bot.py          Telegram bot (python-telegram-bot v21, polling; in-process in production)
  migrations/       Alembic migrations (Postgres)
  tests/
web/                React + TS Mini App / PWA
  src/
    telegram.ts     Mini App SDK wrapper (works outside Telegram too)
    api.ts          REST client + auth token handling
    heartRate.ts    Web Bluetooth heart-rate reader
    useLive.ts      WebSocket hook for a live meeting
    components/     screens
docs/               product and technical docs
```

## Data model

- **User**: `telegram_id`, display name, optional `birth_year`, `resting_hr`, `max_hr`, `zone2_low`/`zone2_high` overrides, `share_bpm`.
- **Meeting**: title, topic, host, `starts_at` (UTC), `duration_min`, `activity` (`bike`, `treadmill`, `walk`, `run`, `any`), `visibility` (`public` or `private` with an `invite_code`), `voice_link`.
- **Attendance**: user × meeting, with `joined_at`, `left_at`, `samples`, `avg_hr`, `zone2_seconds`, `tracked_seconds`.

## Live protocol (`/api/meetings/{id}/live?token=<jwt>`)

Client → server:
```json
{"type": "hr", "bpm": 132}
{"type": "effort", "level": "conversational"}
```
`level` is one of `easy`, `conversational`, `short_sentences` or `breathless`. These map to zones 1, 2, 3 and 4.

Server → all clients in the room:
```json
{"type": "state", "participants": [
  {"user_id": 1, "name": "Ana", "zone": 2, "bpm": null, "source": "effort", "zone2_pct": 87}
]}
```

## Scaling path (only when needed)

Postgres and Alembic migrations are in place. Next: Redis pub/sub for `LiveHub`, then LiveKit audio for standalone, then the native companion app.
