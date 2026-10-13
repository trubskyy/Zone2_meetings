import logging
import requests
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_telegram_bot(token, api_base_url='http://localhost:5000/api'):
    """Start a simple Telegram bot that connects users to meetings.

    The bot supports the following commands:
    - /start: welcome message
    - /list: list available meetings
    - /create <title>: create a new meeting
    - /join <id>: join a meeting and register Telegram user id
    - /leave: leave the meeting
    """
    updater = Updater(token)
    dispatcher = updater.dispatcher

    def api_list_meetings():
        r = requests.get(f"{api_base_url}/meetings")
        return r.json() if r.ok else {"success": False}

    def api_join_meeting(meeting_id, telegram_id, name):
        payload = {"telegram_id": telegram_id, "name": name}
        r = requests.post(f"{api_base_url}/meetings/{meeting_id}/telegram-join", json=payload)
        return r.json() if r.ok else {"success": False}

    def api_leave_meeting(meeting_id, telegram_id):
        payload = {"telegram_id": telegram_id}
        r = requests.post(f"{api_base_url}/meetings/{meeting_id}/telegram-leave", json=payload)
        return r.json() if r.ok else {"success": False}

    def api_create_meeting(title, creator_name):
        payload = {"title": title, "time": "TBD", "participants": 1}
        r = requests.post(f"{api_base_url}/meetings", json=payload)
        return r.json() if r.ok else {"success": False}

    def send_welcome(update: Update, context: CallbackContext):
        msg = "Welcome to Zone 2 Meeting bot!\nCommands:\n/list - list meetings\n/create <title> - create meeting\n/join <id> - join meeting\n/leave - leave meeting"
        update.message.reply_text(msg)

    def list_cmd(update: Update, context: CallbackContext):
        data = api_list_meetings()
        if not data.get("success"):
            update.message.reply_text("Failed to fetch meetings.")
            return
        meetings = data.get('meetings', [])
        if not meetings:
            update.message.reply_text("No meetings available.")
            return
        lines = [f"{m['id']} - {m['title']} ({m['participants']} participants) at {m['time']}" for m in meetings]
        update.message.reply_text("\n".join(lines))

    def create_cmd(update: Update, context: CallbackContext):
        args = context.args
        title = " ".join(args) if args else "New Meeting"
        data = api_create_meeting(title, update.effective_user.full_name)
        if data.get('success'):
            mid = data['meeting']['id']
            update.message.reply_text(f"Created meeting {mid} - {title}")
        else:
            update.message.reply_text("Failed to create meeting.")

    def join_cmd(update: Update, context: CallbackContext):
        args = context.args
        if not args:
            update.message.reply_text("Usage: /join <meeting_id>")
            return
        meeting_id = args[0]
        res = api_join_meeting(meeting_id, update.effective_user.id, update.effective_user.full_name)
        if res.get('success'):
            update.message.reply_text(f"You joined meeting {meeting_id}.")
        else:
            update.message.reply_text("Failed to join meeting.")

    def leave_cmd(update: Update, context: CallbackContext):
        # Determine what meeting user is in by querying the API
        # For simplicity, check all meetings and remove from the first that contains this telegram id
        data = api_list_meetings()
        if not data.get('success'):
            update.message.reply_text("Failed to query meetings.")
            return
        meetings = data.get('meetings', [])
        found = False
        for m in meetings:
            # fetch details
            r = requests.get(f"{api_base_url}/meetings/{m['id']}")
            if not r.ok:
                continue
            details = r.json()
            participants = details.get('participants', [])
            for p in participants:
                if p.get('telegram_id') == update.effective_user.id:
                    res = api_leave_meeting(m['id'], update.effective_user.id)
                    if res.get('success'):
                        update.message.reply_text(f"Left meeting {m['id']}")
                        found = True
                        break
            if found:
                break
        if not found:
            update.message.reply_text("You're not currently in any meeting (or the meeting doesn't have Telegram participants). Use /list to check meetings.")

    def unknown(update: Update, context: CallbackContext):
        update.message.reply_text("Sorry, I didn't understand that command.")

    def forward_message_to_meeting(update: Update, context: CallbackContext):
        # When a user sends a message, forward it to other meeting participants
        user_id = update.effective_user.id
        # find the meeting this user is in
        data = api_list_meetings()
        if not data.get('success'):
            return
        meetings = data.get('meetings', [])
        for m in meetings:
            r = requests.get(f"{api_base_url}/meetings/{m['id']}")
            if not r.ok:
                continue
            details = r.json()
            participants = details.get('participants', [])
            # find if this user is a participant
            if any(p.get('telegram_id') == user_id for p in participants):
                # broadcast to others
                for p in participants:
                    if p.get('telegram_id') and p.get('telegram_id') != user_id:
                        try:
                            context.bot.send_message(chat_id=p['telegram_id'], text=f"{update.effective_user.full_name}: {update.message.text}")
                        except Exception as e:
                            logger.error("Failed to forward message to %s: %s", p.get('telegram_id'), e)
                return

    # Register handlers
    dispatcher.add_handler(CommandHandler('start', send_welcome))
    dispatcher.add_handler(CommandHandler('list', list_cmd))
    dispatcher.add_handler(CommandHandler('create', create_cmd))
    dispatcher.add_handler(CommandHandler('join', join_cmd))
    dispatcher.add_handler(CommandHandler('leave', leave_cmd))
    dispatcher.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), forward_message_to_meeting))
    dispatcher.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info('Starting Telegram bot polling...')
    updater.start_polling()
    updater.idle()
