# Fitness-Comm App — System Architecture & Tech Stack

> Detailed system architecture diagram, sequence flows, data model outline, and pragmatic tech-stack recommendation for a Python-based app combining multiperson communication (Zoom/Telegram-like) and fitness integrations (Garmin, Apple Health, Strava, Fitbit).

---

## 1) High-level summary

This app connects three big areas:

1. **Real-time multi-person communication** (video, audio, chat, screen share) — for live classes and coaching.
2. **Fitness data ingestion & sync** (Garmin, Apple Health via mobile, Strava, Fitbit) — for participant metrics and historical analytics.
3. **Backend orchestration + frontend UI** — authentication, session management, persistence, analytics, billing, and dashboards.

Primary language: **Python (FastAPI)** for backend services.
Frontend: **React / Next.js** for web; **React Native** or **Flutter** for mobile (we recommend React Native for shared JS/TS knowledge with web stack).

---

## 2) Components (logical)

- **Client Apps**
  - Web SPA (Next.js + React)
  - Mobile app (React Native) for iOS/Android — required for HealthKit access on iOS

- **API Gateway / Edge**
  - Vercel/Cloudflare Workers / AWS API Gateway (edge caching, rate limiting, TLS)

- **Backend Services (Python / FastAPI)**
  - Auth Service (OAuth2 / JWT)
  - Session Management Service (rooms, tokens)
  - Signaling Service (if building your own WebRTC) — otherwise thin wrapper for 3rd-party provider tokens
  - Fitness Sync Service (OAuth flows, webhook receivers, sync jobs)
  - Real-time Messaging Service (WebSockets / PubSub)
  - Ingestion & Processing (background workers)
  - Billing Service (Stripe)

- **Real-Time Layer (recommended: 3rd-party)**
  - Agora / Twilio / Daily.co / Vonage for video/audio
  - Optional: Self-managed WebRTC stack (Coturn STUN/TURN, Janus or mediasoup) — only if necessary

- **Data Stores**
  - Relational DB: PostgreSQL (primary)
  - Time-series / metrics DB: TimescaleDB (Postgres extension) or InfluxDB for high-resolution HR/power/time data
  - Cache: Redis (sessions, presence, rate-limiting)
  - Object Storage: S3-compatible (recordings, assets)

- **Background / Job Queue**
  - Celery + Redis or Dramatiq + Redis

- **Observability**
  - Metrics: Prometheus + Grafana
  - Tracing: OpenTelemetry -> Jaeger
  - Logs: centralized logging (CloudWatch / Elastic / Datadog)

- **CI / CD**
  - GitHub Actions or GitLab CI for build/test/deploy pipelines

- **Infrastructure / Hosting**
  - AWS (recommended) or GCP / Azure
  - Containerization: Docker, orchestration: ECS / EKS / or managed platforms (Railway / Render / Fly / Vercel)

- **3rd-Party Integrations**
  - Garmin Health API (enterprise onboarding + webhooks)
  - Apple HealthKit (on-device; sync via mobile app upload to backend)
  - Strava / Fitbit / Polar OAuth2 APIs
  - Payment: Stripe
  - Push notifications: Firebase Cloud Messaging & APNs

---

## 3) Visual architecture (ASCII block diagram)

```
[Web / Mobile Clients] <----HTTPS----> [API Gateway / Edge]
      |                                      |
      | Websocket / WS                       | REST / Auth / Token
      v                                      v
[Realtime SDK (Agora/Twilio)] <-----> [Backend: Session Service / Token Provider]
      ^                                      |
      | Webhook / Recording                  | Pub/Sub
      v                                      v
[Object Storage: S3] <-----> [Background Workers / Transcoding]

[Backend: FastAPI Services] <-----> [Postgres/TimescaleDB]
          |                                 |
          | Redis (presence, pubsub)         | Celery/Queue
          v                                 v
    [Fitness Sync Service] <-----> [3rd Party APIs: Garmin / Strava / Fitbit]
          ^
          |
  (Mobile app uploads HealthKit exports)

Monitoring -> Prometheus/Grafana | Tracing -> Jaeger
CI/CD -> GitHub Actions -> Container Registry -> Deploy
```

---

## 4) Sequence flow — Live fitness class (recommended using provider)

1. User authenticates via OAuth/JWT.
2. User requests to join a "Live Class".
3. Frontend calls backend -> backend creates a session and requests a join token from video provider (Agora/Twilio).
4. Backend returns ephemeral join token to the client.
5. Client joins the video session via provider SDK.
6. Client begins sending local telemetry (if user permits): HR from paired device or mobile HealthKit upload.
7. Telemetry goes to:
   - Direct client -> backend over WebSocket (if device can push) OR
   - Provider webhook flow (Garmin/Strava) -> backend Fitness Sync service
8. Backend publishes telemetry to a Redis pub/sub channel for that session room.
9. Instructor and other clients subscribed to the room receive live telemetry updates and render overlays.
10. When class ends, video provider optionally sends a recording webhook -> background worker stores recording in S3 and generates a clip/summary.
11. Background worker produces session analytics (avg HR, zones, calories) and stores results in Postgres / TimescaleDB.

---

## 5) Data model (high-level)

Tables (Postgres):
- users (id, name, email, auth_provider, created_at)
- profiles (user_id, height, weight, timezone, preferences)
- fitness_devices (id, user_id, provider, external_id, token_info)
- activities (id, user_id, type, started_at, ended_at, summary_json, source)
- metrics (id, activity_id, ts, hr, cadence, power, lat, lon)
- sessions (id, host_id, start_ts, end_ts, room_id, provider, recording_url)
- session_participants (session_id, user_id, join_ts, leave_ts, avg_hr)
- invoices / subscriptions

**Indexing & storage:**
- Use Timescale/Postgres hypertables (or separate time-series DB) for `metrics` for fast range queries and downsampling.
- Partition `activities` monthly if you expect very large scale.

---

## 6) Tech stack recommendation (by layer)

### Frontend
- **Web:** Next.js + React + TypeScript
  - UI: Radix/UI or MUI + Tailwind CSS
  - Realtime client: simple WebSocket client + provider SDKs
- **Mobile:** React Native (TypeScript) or Flutter (Dart)
  - iOS: native HealthKit access (use `react-native-health` or create a small native module)

### Backend
- **Language / Framework:** Python + FastAPI (asyncio-native, automatic OpenAPI)
- **ORM / DB:** SQLAlchemy (1.4+ with async) or Prisma (if you prefer JS layer) — for Python: SQLModel is also a great fit built on SQLAlchemy
- **Auth:** OAuth2 + JWT (use `fastapi-users` or `Authlib` for OAuth flows)
- **WebSockets:** `fastapi` WebSocket route + `uvicorn`/`hypercorn`
- **Background workers:** Celery or Dramatiq + Redis
- **Queueing & PubSub:** Redis (primary), consider Kafka for extremely large scale

### Real-time video
- **Provider (recommended):** Agora or Daily.co or Twilio Video
  - Fast to integrate, robust, SDKs for Web/Mobile, recording, NAT traversal
- **If self-hosting:** coturn (STUN/TURN) + mediasoup or Janus (complex)

### Storage
- **Primary DB:** PostgreSQL (AWS RDS or Neon / Supabase)
- **Timeseries:** TimescaleDB on top of Postgres or InfluxDB for fine-grained HR/power data
- **Cache:** Redis (sessions, pub/sub)
- **Object storage:** AWS S3 (or Supabase Storage / DigitalOcean Spaces)

### Integrations & 3rd party
- **Garmin Health API** (enterprise) — webhooks, periodic fetch
- **Apple HealthKit** — mobile app collects and uploads
- **Strava, Fitbit** — OAuth2 REST APIs
- **Payments:** Stripe
- **Push notifications:** FCM + APNs

### Observability & Security
- **Metrics:** Prometheus + Grafana
- **Tracing:** OpenTelemetry + Jaeger
- **Logging:** ELK stack or Datadog
- **WAF / DDoS:** Cloudflare or AWS Shield
- **Secrets management:** AWS Secrets Manager / HashiCorp Vault

### Dev Tools
- **CI/CD:** GitHub Actions
- **IaC:** Terraform or Pulumi
- **Container registry:** GitHub Container Registry or ECR

---

## 7) Security & privacy considerations

- **HIPAA?** If storing sensitive health data or offering medical advice, consider HIPAA compliance and sign BAAs. Apple HealthKit data usually falls under sensitive PHI — treat accordingly.
- **Least privilege** for all tokens and secrets.
- **End-to-end encryption**: standard provider video streams are encrypted in transit; if you must guarantee end-to-end for video, check provider capabilities or implement client-side encryption (hard).
- **Consent & data residency:** explicit user consent for health data, clear retention policies, allow data export/deletion (GDPR).

---

## 8) Cost & scaling notes

- **Video provider** costs will be your largest recurring cost (per-minute billing usually). Optimize by hosting short sessions, reducing recording retention, and using server-side heuristics for recording only when needed.
- **Storage + DB** costs depend on retention of raw telemetry. Consider rolling up high-frequency telemetry into compressed summaries (1s -> 15s -> minute) for long-term retention.
- **Autoscaling**: use managed services for ease (ECS/Fargate, RDS autoscaling). Use spot instances for non-critical batch jobs.

---

## 9) Minimal Viable Product (MVP) scope — to validate quickly

- Web + mobile signup/login
- Create/join live session with multi-person video via Agora/Twilio
- Simple chat and participant list
- Integrate Strava OAuth and display latest activity
- Mobile HealthKit upload (HR stream) to backend over WebSocket
- Live HR overlay for instructor
- Save session summary (avg HR, durations)

This MVP avoids Garmin enterprise onboarding and complex self-hosted WebRTC while proving the core product value.

---

## 10) Developer ergonomics & recommended libraries (Python)

- `fastapi`, `uvicorn`, `httpx` (async HTTP client)
- `sqlmodel` or `sqlalchemy` + `alembic` for migrations
- `pydantic` for validation
- `redis-py` and `aioredis`
- `celery` or `dramatiq`
- `authlib` for OAuth2
- `sentry` for error tracking
- `opentelemetry` instrumentation

---

## 11) Example project layout (FastAPI)

```
/app
  /app/api
    v1
      auth.py
      sessions.py
      users.py
      fitness.py
  /app/core
    config.py
    security.py
  /app/db
    models.py
    crud.py
    session.py
  /app/services
    video_provider.py
    fitness_sync.py
    webhook_handlers.py
  /app/workers
    tasks.py
  /app/schemas
    pydantic_models.py
  /tests
  Dockerfile
  alembic/
  requirements.txt
```

---

## 12) Next steps I can help with (pick one):
- Draw an interactive architecture diagram (Mermaid flow / Graphviz) you can iterate on.
- Produce the detailed OpenAPI endpoints for the core flows (auth, sessions, telemetry ingest).
- Create an example FastAPI project scaffold (boilerplate) with auth, WebSocket room, and token provider for Agora.
- Draft a HealthKit mobile upload module in React Native.


---

*If you want I can convert the ASCII diagram into a Mermaid diagram or a PNG schematic. Tell me which of the "Next steps" you'd like and I will produce it.*



---

## ADDITIONAL DELIVERABLES REQUESTED

You've asked for **all** of the following. I've added them here so you have one place to iterate:

1. Architecture diagram (Zoom App version)
2. Architecture diagram (Teams App version)
3. Side-by-side comparison: Zoom vs Teams vs Standalone
4. MVP feature plan for a Zoom-based fitness app
5. Full technical scaffold (FastAPI backend + Zoom App frontend)

---

### 1) Architecture diagram — Zoom App version (Mermaid)

```mermaid
flowchart LR
  subgraph Clients
    A[Web Client (Next.js)
Instructor/Participant] --- B[Mobile Companion App
(React Native)];
  end

  A -- HTTPS --> API[API Gateway / FastAPI Backend]
  B -- HTTPS --> API
  API -- REST/OAuth --> Zoom[Zoom Platform (Meeting + App SDK)]
  Zoom -- SDK Token --> A
  Zoom -- SDK Token --> B
  API -- Pub/Sub --> Redis[Redis (presence/pubsub)]
  API -- DB --> Postgres[(Postgres / TimescaleDB)]
  API -- S3 --> Storage[(S3 recordings / assets)]
  API -- Webhook --> Garmin[Garmin / Strava / Fitbit]
  B -- Upload HealthKit --> API
  API -- Queue --> Workers[Background Workers (Celery/Dramatiq)]
  Workers -- Process --> Storage
  Workers -- Store Analytics --> Postgres
  Redis -- Notify --> A
  Redis -- Notify --> B

  classDef cloud fill:#f9f,stroke:#333,stroke-width:1px;
  class Zoom cloud;
```

**Notes:** Zoom handles video/audio; your app is an in-meeting panel or shared app. Use Zoom OAuth for auth and Zoom SDK for in-meeting tokens. Mobile app handles HealthKit and uploads HR streams.

---

### 2) Architecture diagram — Teams App version (Mermaid)

```mermaid
flowchart LR
  subgraph Clients
    W[Teams Web Client / Desktop] --- M[Mobile Companion App]
  end

  W -- Embedded Tab / Side Panel --> TeamsPlatform[Teams Platform (JS SDK / SSO)]
  TeamsPlatform -- HTTPS --> API[API Gateway / FastAPI Backend]
  M -- HTTPS --> API
  API -- DB --> Postgres[(Postgres / TimescaleDB)]
  API -- S3 --> Storage[(S3 recordings / assets)]
  API -- Webhook --> Garmin[Garmin / Strava / Fitbit]
  M -- Upload HealthKit --> API
  API -- Pub/Sub --> Redis[Redis]
  Workers[Background Workers] --> API
  API -- Graph API --> Azure[Microsoft Graph (optional)]
  TeamsPlatform -- SSO --> Azure

  classDef cloud fill:#f9f,stroke:#333,stroke-width:1px;
  class TeamsPlatform,Azure cloud;
```

**Notes:** Teams apps use Azure AD SSO and the Teams JS SDK. Teams gives strong enterprise distribution and single-sign-on for corporate users.

---

### 3) Side-by-side comparison: Zoom vs Teams vs Standalone

| Category | Zoom App | Teams App | Standalone App (own video) |
|---|---:|---:|---:|
| Video infrastructure | Provided by Zoom (no infra) | Provided by Teams | You must manage (Agora/Twilio or WebRTC stack) |
| Time to market | Fast | Fast (enterprise fit) | Slow (months) |
| Enterprise adoption | Good (meetings-focused) | Excellent (Azure AD, org-wide) | Harder but full control |
| UI control over video | Limited (side panels) | Limited (tabs/panels) | Full control (overlays, UX) |
| HealthKit / Mobile data | Requires companion mobile app | Requires companion mobile app | Requires companion mobile app |
| Cost profile | Lower infra cost; marketplace fees | Lower infra cost; integration work | Higher recurring video costs + infra |
| Compliance & Reviews | Zoom Marketplace review | Microsoft validation & enterprise checks | You control compliance; more responsibility |
| Recording / Storage | Zoom can provide recordings; you can store | Teams meetings -> recordings via Graph or cloud | You control recording & storage flow |


---

### 4) MVP Feature Plan — Zoom-based fitness app (6-week plan)

**Goal:** Rapidly validate instructor+class use-case with live HR overlay and session summaries.

**Week 0 (Prep)**
- Create Zoom developer account and app; read Zoom App SDK docs
- Set up project repos (backend/frontend/mobile)
- Provision staging AWS account, Postgres, Redis, S3

**Week 1 — Backend auth & basic APIs**
- FastAPI skeleton, user model, JWT + Zoom OAuth
- Postgres schema: users, sessions, session_participants
- Basic CI (GitHub Actions)

**Week 2 — Zoom app + frontend shell**
- Simple Next.js app embedded as Zoom app panel
- Frontend auth using Zoom OAuth and your backend
- UI: join/create session, participant list

**Week 3 — Integrate Zoom meeting tokens & join flow**
- Backend generates ephemeral join tokens with Zoom SDK
- Frontend uses Zoom Web SDK to join meeting panel
- Add chat and basic presence via Redis pubsub

**Week 4 — Mobile HealthKit upload & HR stream**
- Small React Native module to read HealthKit HR (or simulate data)
- Mobile app connects to backend via WebSocket and streams HR
- Backend pubsub forwards HR to session room
- Frontend displays live HR tiles for participants

**Week 5 — Session recording & analytics**
- Capture optional Zoom recording webhook -> store in S3
- Background worker computes avg HR, zones, calories
- Store session summary in Postgres

**Week 6 — Polish & beta tests**
- Improve UI/UX, error handling
- Add consent and data privacy flows
- Beta test with small instructor group
- Collect feedback and metrics

MVP success metrics: 50 sessions with HR overlay used by instructors, NPS from instructors > 40, retention of participants > 40% after 1 week.

---

### 5) Full technical scaffold — FastAPI backend + Zoom App frontend

#### File structure (expanded)

```
/fitness-zoom-app
  /backend
    Dockerfile
    /app
      main.py  # FastAPI app entry
      config.py
      /api
        auth.py
        sessions.py
        fitness.py
      /core
        security.py
      /db
        models.py
        crud.py
        session.py
      /workers
        tasks.py
      /services
        zoom_provider.py
        fitness_sync.py
      /schemas
        pydantic_models.py
      alembic/
    requirements.txt
    pytest/
  /frontend
    /nextjs-zoom-app
      package.json
      pages/_app.tsx
      pages/index.tsx
      pages/session/[id].tsx
      components/HRTile.tsx
      components/SessionPanel.tsx
      zoom-sdk-wrapper.ts
  /mobile
    /rn-healthkit
      package.json
      App.js
      native-modules/healthkit-module (iOS)
```

#### Example FastAPI endpoints (high-level)

- `POST /auth/zoom-callback` — exchange Zoom OAuth code for user token and create local user
- `GET /sessions` — list available sessions
- `POST /sessions` — create a session (host only)
- `POST /sessions/{id}/token` — generate ephemeral Zoom join token for the user
- `WS /ws/sessions/{id}` — websocket for HR streams and real-time events (presence, chat)
- `POST /webhooks/zoom/recording` — handle recording finished event
- `POST /webhooks/garmin` — handle Garmin push (if integrated)

#### Sample code snippets (very short)

`backend/app/services/zoom_provider.py` (pseudo)

```python
import httpx
from app.core.config import settings

async def create_zoom_meeting_token(user_id: int, meeting_id: str) -> str:
    # call Zoom API (JWT or OAuth) to create/join token
    async with httpx.AsyncClient() as client:
        r = await client.post("https://api.zoom.us/v2/meetings/{}/reg...".format(meeting_id), headers={...})
        r.raise_for_status()
        data = r.json()
    return data["join_token"]
```

`backend/app/api/sessions.py` (pseudo)

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/{session_id}/token")
async def get_token(session_id: str, user=Depends(get_current_user)):
    token = await zoom_provider.create_zoom_meeting_token(user.id, session_id)
    return {"token": token}
```

`frontend/zoom-sdk-wrapper.ts` (pseudo)

```ts
import { ZoomMtg } from '@zoomus/websdk'

export function joinMeeting(token: string, meetingNumber: string, userName: string) {
  ZoomMtg.init({
    leaveUrl: window.location.href,
    success: () => {
      ZoomMtg.join({
        meetingNumber,
        userName,
        signature: token,
      })
    }
  })
}
```

---

## What I added and how to use it

All of the above sections (Zoom & Teams diagrams, comparison, MVP plan, scaffold) have been appended to the canvas document **"Fitness-Comm App — System Architecture & Tech Stack"**. Open the document to review and iterate.

If you want, I can now:

- Generate the **actual FastAPI project skeleton** files and put them in a zip for download. (I can create code for the backend endpoints and a simple Next.js frontend.)
- Produce a **Mermaid-to-PNG** render of both diagrams.
- Scaffold the **React Native HealthKit module** with example code for iOS (Swift) and RN bridge.

Which of these should I produce now? (Pick any — I will generate the code and files immediately.)

