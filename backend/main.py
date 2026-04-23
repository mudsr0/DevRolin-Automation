import time
import subprocess
import sys
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import reminder

load_dotenv()

# =========================
# CONFIG
# =========================
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", 4))

ANALYZE_HOUR = int(os.getenv("ANALYZE_HOUR", 18))
ANALYZE_MIN = int(os.getenv("ANALYZE_MIN", 0))

REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", 19))
REMINDER_MIN = int(os.getenv("REMINDER_MIN", 0))
STATE_FILE = "orchestrator_state.json"


# =========================
# STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = {}

    state.setdefault("last_scrape_time", None)
    state.setdefault("analysis_done", False)
    state.setdefault("reminder_sent", False)
    state.setdefault("start_time", None)
    state.setdefault("date", str(datetime.now().date()))

    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


state = load_state()


# =========================
# HELPERS
# =========================
def now():
    return datetime.now()


def is_time(h, m):
    t = now()
    return t.hour == h and t.minute == m


def reset_daily():
    global state

    today = str(datetime.now().date())

    if state["date"] != today:
        print("🔄 Reset daily state")

        state = {
            "last_scrape_time": None,
            "analysis_done": False,
            "reminder_sent": False,
            "start_time": None,
            "date": today
        }

        save_state(state)


# =========================
# SCRAPERS
# =========================
def run_scrapers():
    print("🚀 Running scrapers...")

    subprocess.run([sys.executable, "x.py"])
    subprocess.run([sys.executable, "reddit.py"])
    subprocess.run([sys.executable, "linkedin.py"])

    print("✅ Scrapers done")


# =========================
# ANALYZER
# =========================
def run_analyzer():
    print("🧠 Running analyzer...")

    subprocess.run([sys.executable, "analyzer.py"])

    print("📤 Analyzer done")


# =========================
# MAIN LOOP
# =========================
def main():
    global state

    print("🚀 ORCHESTRATOR STARTED (SINGLE REMINDER VERSION)")

    while True:
        reset_daily()
        current = now()

        # =========================
        # SCRAPERS (4 HOURS)
        # =========================
        if state["last_scrape_time"] is None:
            run_scrapers()
            state["last_scrape_time"] = str(current)
            save_state(state)

        else:
            last = datetime.fromisoformat(state["last_scrape_time"])
            diff = (current - last).total_seconds() / 3600

            if diff >= SCRAPE_INTERVAL_HOURS:
                run_scrapers()
                state["last_scrape_time"] = str(current)
                save_state(state)

        # =========================
        # ANALYSIS
        # =========================
        if is_time(ANALYZE_HOUR, ANALYZE_MIN) and not state["analysis_done"]:
            run_analyzer()

            state["analysis_done"] = True
            state["start_time"] = str(current)

            save_state(state)

        # =========================
        # SINGLE REMINDER
        # =========================
        if (
            is_time(REMINDER_HOUR, REMINDER_MIN)
            and not state["reminder_sent"]
            and state["start_time"] is not None
        ):
            print("⏰ Triggering reminder...")

            start_time = datetime.fromisoformat(state["start_time"])

            reminder.run_reminder(start_time)

            state["reminder_sent"] = True
            save_state(state)

        # =========================
        # LOOP
        # =========================
        time.sleep(10)


if __name__ == "__main__":
    main()