# Deploy

One Docker image (`Dockerfile`) holds everything: the built web app, the FastAPI API that serves it on the same origin, and the Telegram bot running inside the API process. On start it runs `alembic upgrade head`, then uvicorn.

**Run exactly one instance.** Live rooms live in process memory (`LiveHub`), and Telegram allows only one process to poll a bot token. Scaling out needs Redis pub/sub and a webhook bot first (see `architecture.md`, "Scaling path").

## What you need

| Thing | Where | Notes |
|---|---|---|
| A host for one always-on container | Fly.io (config in `fly.toml`) | Any host that runs a Dockerfile and doesn't sleep works (Railway, Render paid, a VM). Free tiers that sleep break live rooms and the bot. |
| Managed Postgres | Neon, Supabase, Fly Postgres, Railway | Any `postgres://` or `postgresql://` URL works; the app adds the driver itself. Pick a region close to the app. |
| A Telegram bot | @BotFather `/newbot` | Gives the token and the bot username. |

## Environment

Secrets (set on the host, never in git):

| Variable | Value |
|---|---|
| `Z2_DATABASE_URL` | the Postgres URL from your provider |
| `Z2_TELEGRAM_BOT_TOKEN` | from BotFather |
| `Z2_JWT_SECRET` | a long random string, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `Z2_WEB_APP_URL` | the public HTTPS URL, e.g. `https://zone2-club.fly.dev` (the bot's Open button uses it) |

Set by `fly.toml` / the Dockerfile: `PORT`, `Z2_RUN_BOT=true`, `Z2_STATIC_DIR`, `Z2_CORS_ORIGINS=[]`. `Z2_DEV_LOGIN` stays off in production.

Build args (public, baked into the web build): `VITE_TELEGRAM_BOT_USERNAME` (without @) and `VITE_TELEGRAM_APP_SHORT_NAME`.

## First deploy on Fly.io

```bash
fly auth login
fly launch --no-deploy --copy-config      # keeps fly.toml; pick a unique app name if asked
fly secrets set Z2_DATABASE_URL='postgres://…' Z2_TELEGRAM_BOT_TOKEN='…' \
  Z2_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  Z2_WEB_APP_URL='https://<app>.fly.dev'
fly deploy --ha=false                      # one machine
curl https://<app>.fly.dev/api/health      # {"ok":true}
```

## Telegram setup (BotFather)

1. `/setdomain` on the bot: your app's domain, so the Login Widget works on the website.
2. `/newapp`: create the Mini App with URL `https://<app>.fly.dev`. The short name goes into `VITE_TELEGRAM_APP_SHORT_NAME`. Redeploy after setting the build args.
3. Optional: `/setcommands` with `start - Open Zone 2 Club` and `sessions - Upcoming sessions`.
4. Send `/start` to the bot and tap **Open**.

## Schema changes

Postgres is changed only by Alembic migrations in `backend/migrations/`. After editing `app/models.py`:

```bash
cd backend
alembic revision --autogenerate -m "what changed"   # against a DB at the current head
# review the generated file, then
pytest                                              # test_migrations_match_models fails if a migration is missing
```

The next deploy applies it on start. Local SQLite and tests still use `create_all`.
