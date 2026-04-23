import asyncio
import json
import os
import random
import pathlib
from scrapling import StealthyFetcher
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
CONFIG_PATH = "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
# ==== CONFIG FROM ENV ====
# Using REDDIT_TARGETS for subreddits and SEARCH_HASHTAGS for keywords
reddit_cfg = CONFIG.get("reddit", {})

SUBREDDITS = reddit_cfg.get("subreddits", ["technology"])
KEYWORDS = [k.lower() for k in reddit_cfg.get("keywords", [])]
MAX_DB_SIZE = 10

# Robust Pathing
# 1. Robust Pathing (Update this at the top)
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR / "data"
DB_FILE = DATA_DIR / "reddit_data.json" # Saves inside the data folder

async def run():
    print(f"🚀 Initializing Reddit Scrapling Engine...")

    # Ensure directory exists
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load existing Database
    db = []
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    db = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Warning: Could not parse database, starting fresh. Error: {e}")
            db = []

    seen_urls = {post['url'] for post in db}

    # 2. Define Asynchronous Fetcher
    async def fetch(sub):
        # The .json trick is excellent for Reddit's internal API
        url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=25&cb={random.randint(1, 999)}"
        try:
            # Scrapling StealthyFetcher for anti-bot bypass
            resp = await StealthyFetcher.async_fetch(url, headless=True)
            return resp.json().get('data', {}).get('children', [])
        except Exception as e:
            print(f"❌ Error fetching r/{sub}: {e}")
            return []

    print(f"🔎 Checking {len(SUBREDDITS)} subreddits for keywords: {KEYWORDS}")
    tasks = [fetch(s) for s in SUBREDDITS]
    results = await asyncio.gather(*tasks)

    # 3. Process candidates
    new_entries_found = 0
    for sub_result in results:
        for item in sub_result:
            p = item['data']
            url = f"https://www.reddit.com{p.get('permalink')}"
            score = p.get('score', 0)

            if url in seen_urls:
                continue

            title = p.get('title', '')
            body = p.get('selftext', '')
            full_content = f"{title} {body}".lower()

            # Filter by your env keywords
            if any(k in full_content for k in KEYWORDS):
                new_post = {
                    "source": f"r/{p.get('subreddit')}",
                    "title": title,
                    "score": score,
                    "comments": p.get("num_comments", 0),
                    "url": url,
                    "content": body[:800],
                    "engagement": score + p.get("num_comments", 0)
                }

                # Maintain DB size by replacing lowest scores
                if len(db) < MAX_DB_SIZE:
                    db.append(new_post)
                    seen_urls.add(url)
                    new_entries_found += 1
                else:
                    db.sort(key=lambda x: x['score'])
                    if score > db[0]['score']:
                        print(f"♻️ Replacing lower post with viral trend: {title[:40]}...")
                        db[0] = new_post
                        seen_urls.add(url)
                        new_entries_found += 1

    # 4. Final Save (Sorted by score descending)
        # 4. Final Save (Update this at the end of the run function)
        if db:
            # Ensure the data directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            db.sort(key=lambda x: x['score'], reverse=True)
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=4, ensure_ascii=False)

            print(f"✅ Reddit Update Complete. Data saved to {DB_FILE}")

if __name__ == "__main__":
    asyncio.run(run())