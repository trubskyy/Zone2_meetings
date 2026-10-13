# Business model

The previous plan projected 1M users and a 64% operating margin in 24 months. This document replaces it with a bottom-up model built from numbers we can measure. **Every figure here is an assumption to test, not a forecast.**

## Phases

| Phase | Money | Goal |
|---|---|---|
| 0. Concierge MVP (weeks 1–8) | Free. Costs are near zero, using Telegram, a Strava club and forms. | Show that people come back. |
| 1. Mini App beta | Free core. Optional supporter tier in Telegram Stars. | Retention, and willingness to pay at all. |
| 2. Paid tiers | Club Pro (individual), Host tools | Revenue per active member |
| 3. Teams | Per-seat "Move & Meet" programs | Company revenue backed by retention data |

## What we would charge for (hypotheses)

- **Free:** joining public sessions, live zone display, streaks.
- **Club Pro (about $5–8/month):** private sessions, personal zone history and trends, Strava/Garmin recaps, AI session notes.
- **Host tools:** recurring sessions, a member list, paid sessions. We take a commission on host-charged sessions, which suits coaches.
- **Teams (about $6–10/seat/month):** a team calendar, aggregate (never individual) wellness reporting, and an admin view.

On Telegram, sales of digital goods go through **Telegram Stars**. The standalone app uses Stripe. Price in both and compare conversion.

## Cost per user (estimate, check current vendor prices)

Assume an active paying member does 10 sessions × 45 min a month, which is **450 participant-minutes**.

| Item | Rough unit cost | Monthly |
|---|---|---|
| Audio (Telegram native) | $0 | $0 |
| Audio (standalone, hosted WebRTC) | about $0.001/participant-min | about $0.45 |
| Transcription, if on for every session | about $0.003–0.006/min | about $1.35–2.70 |
| AI summary | small | about $0.05–0.20 |
| Hosting/DB | shared | about $0.10 |

**Takeaways:** Telegram-native audio makes the community tier nearly free to run. Transcription is the expensive part, so make it opt-in and Pro-only.

## The model to build (spreadsheet, not prose)

Inputs, all measured during phases 0–1:
1. People reached per channel per week (Telegram channels, Strava clubs, Zwift communities, hosts' audiences)
2. Visit → first session conversion
3. Week-1 and week-4 retention of first-timers
4. Sessions per active member per week
5. Free → paid conversion. Assume **2–5%** until proven otherwise.
6. Monthly churn of payers

Revenue = active members × paid % × price. Model three scenarios, with costs from the table above.

## Funding stance

Bootstrap through phase 1. Consider raising only with a retention curve that has flattened.
