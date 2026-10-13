# Zone2_meetings
Zone 2 meetings project

This repository contains a prototype of the Zone 2 Meeting concept that combines biometric tracking and meeting functionality with a Telegram-based chat backbone.

Features implemented in this prototype:
- Flask backend with REST endpoints for meetings and biometrics
- Basic React UI (in `App.jsx`) to list and join meetings
- Telegram bot for chat integration (polling mode), supporting /list, /create, /join and /leave
- Support for registering Telegram participants and forwarding messages between meeting participants by telegram id

Prerequisites
- Python 3.9+
- Node.js (optional, to serve the front-end)

Setup
1. Create a Python virtualenv and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. (Optional) Create a Telegram Bot and obtain a token from @BotFather. Set it as an environment variable:

```bash
export TELEGRAM_TOKEN='123456:ABC-DEF'
```

3. Start the Flask server:

```bash
python main.py
```

The app will start on http://localhost:5000 and, if the token is set, also start a Telegram bot polling loop.

Using the Telegram bot
1. Open a chat with your bot.
2. Run `/list` to see meetings, `/create Meeting Title` to create one, `/join <id>` to join, and send messages to broadcast to other participants.

Notes
- This prototype uses in-memory data structures (no persistent database). Meetings, participants, and messages will reset on server restart.
- The Telegram integration is implemented using polling for simplicity. For production you should use webhooks and deploy securely.

