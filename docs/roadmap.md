# Roadmap

Each phase has an exit test. Move on when the test passes, not when a date arrives.

## Phase 0: Concierge MVP (weeks 1–8, almost no code)

Run **Zone 2 Club** by hand. See the community playbook in the company repo ([`content/community-playbook.md`](https://github.com/trubskyy/zone2-company/blob/main/content/community-playbook.md)).

- A Telegram channel for announcements, plus one group per regular session. Audio uses Telegram's native voice chat.
- A Strava club for activity recaps.
- 5–10 themed sessions per week. Indoor bike first, then walk and run.
- A post-session form: zone self-report, enjoyment, "would you come again?"
- **Technical test in parallel:** confirm microphone access and WebRTC audio inside the Telegram web view on iOS and Android. This decides whether standalone-style audio can ever run inside the Mini App.

**Exit test:** at least 30% of first-time attendees attend again in week 4, and at least 3 hosts run sessions without being asked.

## Phase 1: Mini App beta (this repo's first code)

- [x] Backend skeleton: Telegram auth, profiles, personal zones, meetings, join/leave
- [x] Live zone room over WebSocket (heart rate or self-reported effort)
- [x] Web app: meeting list, create, live view, profile, Web Bluetooth heart rate
- [x] Bot: `/start` opens the Mini App, `/sessions` lists upcoming sessions
- [ ] Deploy (one small VM or a PaaS such as Fly.io or Railway, with managed Postgres)
- [ ] Register the bot and Mini App with BotFather; set the domain for the Login Widget
- [ ] Bot reminders 15 min before a session you joined
- [ ] Streaks and a weekly "Zone 2 minutes" recap message
- [ ] Session recap in the group: who rode, total Zone 2 minutes

**Exit test:** at least 50% of concierge regulars switch to the Mini App, and week-4 retention doesn't fall.

## Phase 2: Standalone and Pro

- Standalone audio with LiveKit
- Strava/Garmin import for after-session recaps
- Opt-in transcription and AI notes (Pro)
- Telegram Stars and Stripe payments; host-paid sessions

**Exit test:** 2–5% of active members pay.

## Phase 3: Native companion and Teams

- React Native companion: Bluetooth heart-rate straps on iOS, Apple Watch / HealthKit, Wear OS
- Bluetooth fitness-machine data (speed and power from trainers and treadmills)
- Teams: shared calendar, aggregate reporting, Zoom/Meet/Teams companion mode

## Parked (revisit only with evidence)

AR glasses overlays, live location maps, emergency beacons, athlete appearances, podcast library.
