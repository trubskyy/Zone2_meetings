# One image: the built web app served by the FastAPI API, with the Telegram bot in the same process.
# Build:  docker build -t zone2 --build-arg VITE_TELEGRAM_BOT_USERNAME=... --build-arg VITE_TELEGRAM_APP_SHORT_NAME=... .
# Run:    see docs/deploy.md for the required Z2_* env vars.

FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# Vite bakes VITE_* in at build time. API calls stay same-origin (VITE_API_URL empty).
ARG VITE_TELEGRAM_BOT_USERNAME=""
ARG VITE_TELEGRAM_APP_SHORT_NAME=""
ENV VITE_API_URL="" VITE_DEV_LOGIN="false" \
    VITE_TELEGRAM_BOT_USERNAME=$VITE_TELEGRAM_BOT_USERNAME \
    VITE_TELEGRAM_APP_SHORT_NAME=$VITE_TELEGRAM_APP_SHORT_NAME
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install ".[postgres]"
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY --from=web /web/dist ./static

RUN useradd --create-home --uid 1000 z2
USER z2

ENV Z2_STATIC_DIR=/app/static Z2_RUN_BOT=true PORT=8000
EXPOSE 8000
# Migrate, then serve. One process only: live rooms are in memory and only one process may poll the bot.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
