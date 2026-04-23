import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
DESIGNER_ID = os.getenv("DESIGNER_ID")

if not SLACK_BOT_TOKEN or not CHANNEL_ID or not DESIGNER_ID:
    raise ValueError("❌ Missing .env variables")


# =========================
# SEND MESSAGE
# =========================
def send_slack(message):
    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": CHANNEL_ID,
        "text": message
    }

    res = requests.post(url, headers=headers, json=payload)
    data = res.json()

    if not data.get("ok"):
        print("❌ Slack error:", data)
    else:
        print("✅ Reminder sent")


# =========================
# FETCH MESSAGES
# =========================
def fetch_messages():
    url = "https://slack.com/api/conversations.history"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    params = {
        "channel": CHANNEL_ID,
        "limit": 100
    }

    res = requests.get(url, headers=headers, params=params)
    data = res.json()

    if not data.get("ok"):
        print("❌ Fetch error:", data)
        return []

    return data.get("messages", [])


# =========================
# CHECK DONE
# =========================
def check_done(after_time):
    messages = fetch_messages()

    for msg in messages:

        if "bot_id" in msg:
            continue

        if msg.get("user") != DESIGNER_ID:
            continue

        text = msg.get("text", "").lower()
        ts = float(msg.get("ts", 0))
        msg_time = datetime.fromtimestamp(ts)

        # only today
        if msg_time.date() != datetime.now().date():
            continue

        # after workflow start
        if msg_time <= after_time:
            continue

        if "done" in text:
            print("✅ DONE detected")
            return True

    return False


# =========================
# SINGLE REMINDER
# =========================
def run_reminder(start_time):

    if check_done(start_time):
        print("🟢 Already done. No reminder needed.")
        return

    send_slack("⏰ Reminder: Please mark task as DONE.")