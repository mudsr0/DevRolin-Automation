import time
import json
import os
import hashlib
from difflib import SequenceMatcher

HISTORY_FILE = "data/history.json"
DAYS_LIMIT = 15
SECONDS_LIMIT = DAYS_LIMIT * 24 * 60 * 60


# =========================
# TEXT CLEANING
# =========================
def clean_text(text):
    return " ".join(text.lower().strip().split())


# =========================
# HASH FUNCTION
# =========================
def get_hash(text):
    return hashlib.md5(clean_text(text).encode()).hexdigest()


# =========================
# SIMILARITY CHECK
# =========================
def is_similar(a, b, threshold=0.88):
    return SequenceMatcher(None, a, b).ratio() > threshold


# =========================
# LOAD + AUTO CLEAN HISTORY
# =========================
def load_history():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = []

    # 🔥 REMOVE OLD (15+ DAYS)
    now = time.time()
    cleaned = [
        h for h in history
        if now - h.get("timestamp", 0) <= SECONDS_LIMIT
    ]

    # rewrite cleaned file
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    return cleaned


# =========================
# SAVE HISTORY
# =========================
def update_history(posts):
    history = load_history()
    now = time.time()

    for p in posts:
        history.append({
            "hash": p.get("hash"),
            "content": p.get("content", ""),
            "timestamp": now
        })

    history = history[-300:]  # safety cap

    os.makedirs("data", exist_ok=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


# =========================
# DEDUP PIPELINE
# =========================
def deduplicate(posts):
    history = load_history()

    unique_posts = []
    seen_hashes = set()
    seen_urls = set()

    for post in posts:
        content = clean_text(post.get("content", ""))
        url = post.get("url", "")

        if not content:
            continue

        h = get_hash(content)

        # 🔴 HARD DUPLICATES
        if h in seen_hashes:
            continue

        if url and url in seen_urls:
            continue

        # 🔴 SOFT DUPLICATES (same batch)
        duplicate = False
        for p in unique_posts:
            if is_similar(content, p.get("content", "")):
                duplicate = True
                break

        if duplicate:
            continue

        # 🔴 HISTORY DUPLICATES (15 days)
        for old in history:
            if is_similar(content, old.get("content", "")):
                duplicate = True
                break

        if duplicate:
            continue

        post["content"] = content
        post["hash"] = h

        unique_posts.append(post)
        seen_hashes.add(h)

        if url:
            seen_urls.add(url)

    return unique_posts