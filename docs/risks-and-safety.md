# Risks and safety

## Physical safety

- **Outdoor cycling and running:** audio only. The live view must never require looking at the screen. Show a one-time safety notice before the first outdoor session: stay aware of traffic, keep one ear free or use bone-conduction headphones, and follow local laws.
- **Medical:** this isn't a medical device and gives no medical advice. Onboarding should tell people to see a doctor before starting exercise if they have heart conditions or symptoms. Zones are estimates.
- **Heart-rate spikes:** we may *suggest* easing off ("you've been above Zone 2 for 5 min"). We don't diagnose, and we don't promise emergency detection.

## Privacy and health data

- Heart rate is **special-category health data under GDPR**. Collect it only with explicit opt-in consent, explain why, and let users export and delete it.
- **Zone, not BPM**, is shared by default (`share_bpm = false`).
- **Teams:** employers see aggregate data only, never individual heart rate or attendance used for performance purposes. Put this in the Teams contract.
- Keep raw heart-rate samples only as long as needed. Today we store per-session aggregates only.
- HIPAA generally applies to covered entities (healthcare providers and plans) and their business associates. Check this again if we ever sell to health plans or clinics.

## Product and market

| Risk | Mitigation |
|---|---|
| People won't switch meeting tools (Spot's lesson) | Lead with community sessions. For teams, be a companion to their existing meeting tool. |
| Novelty fades after week 2 | Rituals (fixed weekly slots), hosts, streaks. Measure week-4 retention first. |
| Telegram's audience doesn't fit Western companies | Standalone PWA with Login Widget now, email login later. |
| Talking during exercise is harder than expected for unfit people | Zone 2 for a beginner is slow. Encourage walking or easy spinning, and make "easy" a valid choice. |

## Technical

| Risk | Mitigation |
|---|---|
| No Web Bluetooth in iOS web views (including Telegram) | Self-reported effort works everywhere. A native companion comes in phase 3. |
| Telegram Bot API limits (bots can't run voice chats) | Use native voice-chat links. Our own audio only in standalone. |
| Microphone and WebRTC inside the Telegram web view | Test early in phase 0. |
| Single-process `LiveHub` | Fine for the beta. Redis pub/sub when we scale beyond one instance. |
| Telegram platform policy changes (payments in Stars, Mini App rules) | Keep the standalone surface viable. Watch the Bot API changelog. |
