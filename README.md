# Zone 2 Meeting

**Talk while you move.** Take meetings while riding, walking or running at Zone 2, the easy, conversational intensity. It runs as a **Telegram Mini App** and as a **standalone web app**. Around it we're building **Zone 2 Club**, a community of hosted sessions on chosen topics.

> If you can talk in full sentences but couldn't sing, you're probably in Zone 2. A meeting *is* a talk test.

## Docs

| Doc | What's in it |
|---|---|
| [docs/vision.md](docs/vision.md) | Product, audience, principles |
| [docs/roadmap.md](docs/roadmap.md) | Phases with exit tests, current checklist |
| [docs/architecture.md](docs/architecture.md) | Technical decisions, data model, live protocol |
| [docs/risks-and-safety.md](docs/risks-and-safety.md) | Safety, health-data privacy, risks |

Market, business model, positioning, community playbook, content and sales live in the private company repo [`zone2-company`](https://github.com/trubskyy/zone2-company).

## What works today (phase 1)

- Sign in with Telegram: automatic inside the Mini App, through the Login Widget on the web, or a dev login for local work
- Personal heart-rate zones (Karvonen method with a Tanaka max-HR estimate, or your measured Zone 2)
- Host and join public sessions, or private ones by invite link; audio uses a Telegram voice-chat link
- A live room: your zone from a Bluetooth heart-rate strap (Chrome on desktop or Android) or from the talk test; others see your zone, not your BPM
- A post-session summary with your minutes in Zone 2
- A bot: `/start` opens the Mini App, `/sessions` lists upcoming sessions

## Run it locally

Requirements: Python 3.11+ and Node 18+. On Debian or Ubuntu you may first need `sudo apt install python3-venv`.

```bash
# Backend (http://localhost:8000, docs at /docs)
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # dev login on, SQLite file DB
uvicorn app.main:create_app --factory --reload
pytest                          # tests

# Web (http://localhost:5173, proxies /api to :8000)
cd web
npm install
cp .env.example .env.local
npm run dev
```

### Inside Telegram

1. Create a bot with [@BotFather](https://t.me/BotFather) (`/newbot`) and put the token in `backend/.env` as `Z2_TELEGRAM_BOT_TOKEN`.
2. Expose the web dev server over HTTPS, for example `cloudflared tunnel --url http://localhost:5173`, and set `Z2_WEB_APP_URL` to that URL.
3. Run the bot: `cd backend && python -m app.bot`. Send `/start` and tap **Open**.
4. Optional: `/newapp` in BotFather gives a short name for `t.me/<bot>/<app>` invite links, and `/setdomain` enables the Login Widget on the standalone site. Set both in `web/.env.local`.

## Repo layout

```
backend/   FastAPI API, Telegram bot, tests
web/       React + TypeScript Mini App / PWA
docs/      product and technical docs
```
