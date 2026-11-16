# Vision

## One line

**Talk while you move.** Zone 2 Meeting is a place to take meetings, in public sessions or private ones, while riding, walking or running at Zone 2 intensity. It runs inside Telegram and as a standalone app.

## The insight

The usual quick field check for Zone 2 is the **talk test**: you can hold a full conversation, but you couldn't sing. A meeting *is* a talk test. If you can keep the conversation going, you are very likely in the right zone. Exercise and talk don't compete here; they reinforce each other.

The second insight comes from the market. A walking-meeting app on its own has been tried (see [`business/market.md`](https://github.com/trubskyy/zone2-company/blob/main/business/market.md) in the company repo). People rarely switch meeting tools for health reasons alone. They do join *communities* and *rituals*, and they come back for them. So we lead with the community and treat the meeting tool as the means.

## What we are building

1. **Zone 2 Club**: scheduled public sessions with a host and a topic, for example "Founders ride", "Spanish conversation walk", "Book club: *Outlive* ch. 4" or "Marathon base-building chat". Each runs 30–60 minutes. Everyone moves at Zone 2 and talks.
2. **Private sessions**: 1:1s and small groups among people who already know each other, such as a coach and client, a mentor and mentee, co-founders, or friends.
3. **Teams** (later): company "Move & Meet" programs, plus a lightweight companion that sits alongside Zoom, Meet or Teams instead of replacing them.

## Surfaces

| Surface | Role |
|---|---|
| **Telegram Mini App + bot** | The community home: discovery, sign-up, reminders, the live zone dashboard, streaks. Audio uses Telegram's native group voice chat. |
| **Standalone web app (PWA)** | The same web code outside Telegram, with sign-in via the Telegram Login Widget, and later its own audio (LiveKit) for people and companies who don't use Telegram. |
| **Native companion (later)** | Only for what a web view can't do: reading Bluetooth heart-rate sensors on iOS and Android, and reading Apple HealthKit or Watch data. |

## Supported activities

Indoor first, because it is safer and the data is more reliable:
- **Stationary bike / smart trainer.** The primary case.
- **Treadmill / incline walking.**
- **Outdoor walking or running.** Audio only, with no screen interaction needed.
- **Outdoor cycling.** Audio only, with explicit safety guidance (see [risks-and-safety.md](risks-and-safety.md)).

## Principles

- **The zone, not the number.** Others in a session see "Zone 2" or "a bit high", never your raw heart rate, unless you choose to share it.
- **No sensor? Still welcome.** The talk test and a self-reported effort scale are valid inputs.
- **Hands-free during the session.** Anything you need mid-session must work by voice or not at all.
- **Community over features.** We add a feature only when the concierge MVP shows the friction it removes.

## What success looks like in year one

- People come back without being reminded. Week-4 retention of session attendees is the primary metric.
- A small, recognisable culture: hosts, regular rides, in-jokes, streaks.
- Evidence we can show companies: retention, zone adherence, and qualitative stories.
