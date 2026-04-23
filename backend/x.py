import os
import time
import json
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

load_dotenv()

# ==== CONFIG ====
CONFIG_PATH = "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

x_cfg = CONFIG.get("twitter", {})

X_TARGETS = x_cfg.get("usernames", [])
X_HASHTAGS = x_cfg.get("keywords", [])
STATE_FILE = "x_state.json"
OUTPUT_FILE = "tweets.json"
MAX_PER_SOURCE = 10

try:
    X_COOKIES = json.loads(os.getenv("X_COOKIE_JSON", "[]"))
except:
    X_COOKIES = []


def is_logged_in(page):
    try:
        page.wait_for_selector(
            'a[href="/home"], [data-testid="SideNav_NewTweet_Button"], input[data-testid="SearchBox_Search_Input"]',
            timeout=10000
        )
        return True
    except:
        return False


def clean_count(text):
    if not text:
        return 0
    text = text.lower().replace(',', '').strip()
    match = re.search(r"(\d+[\d,.]*)([km]?)", text)
    if not match:
        return 0
    num, multiplier = match.groups()
    num = float(num)
    if multiplier == 'k':
        num *= 1000
    elif multiplier == 'm':
        num *= 1000000
    return int(num)


def extract_metric(tweet, testid):
    try:
        el = tweet.locator(f'[data-testid="{testid}"]')
        label = el.get_attribute("aria-label")
        if label:
            match = re.search(r'(\d+)', label.replace(',', ''))
            if match:
                return int(match.group(1))
        text = el.locator('span').inner_text()
        return clean_count(text)
    except:
        return 0


# =========================
# 🔥 ONLY CHANGE: ADD URL EXTRACTION
# =========================
def process_x_page(page, label):
    results = []
    processed_texts = set()
    print(f"🔎 DEBUG: Scraping {label}...")

    try:
        page.wait_for_selector("article", timeout=12000)

        for _ in range(3):
            tweets = page.locator("article")

            for i in range(tweets.count()):
                if len(results) >= MAX_PER_SOURCE:
                    break

                tweet = tweets.nth(i)

                try:
                    text_content = tweet.locator("div[lang]").inner_text()

                    if text_content in processed_texts:
                        continue

                    # ======================
                    # 🔗 TWEET LINK FETCH
                    # ======================
                    try:
                        href = tweet.locator('a[href*="/status/"]').first.get_attribute("href")
                        tweet_url = f"https://x.com{href}" if href else None
                    except:
                        tweet_url = None

                    likes = extract_metric(tweet, "like")
                    replies = extract_metric(tweet, "reply")
                    retweets = extract_metric(tweet, "retweet")

                    results.append({
                        "source": label,
                        "text": text_content,
                        "likes": likes,
                        "replies": replies,
                        "engagement": likes + replies + retweets,
                        "url": tweet_url  # ✅ ADDED FIELD
                    })

                    processed_texts.add(text_content)

                    print(f"   📥 Found Tweet: {likes} likes | {tweet_url}")

                except:
                    continue

            page.mouse.wheel(0, 2500)
            time.sleep(2)

    except:
        print(f"⚠️ DEBUG: No content for {label}")

    return results


def run():
    all_raw_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)

        if os.path.exists(STATE_FILE):
            context = browser.new_context(storage_state=STATE_FILE)
            print("✅ Using saved session state")
        else:
            context = browser.new_context()
            print("🍪 First run → Injecting cookies")

        page = context.new_page()
        page.set_default_navigation_timeout(60000)

        page.goto("https://x.com", wait_until="domcontentloaded")

        if not is_logged_in(page):
            if X_COOKIES:
                print("💉 Injecting/Refreshing cookies...")
                context.add_cookies(X_COOKIES)
                page.goto("https://x.com/home")
                time.sleep(5)

            if not is_logged_in(page):
                print("❌ FATAL: Authentication failed. Session/Cookies are invalid.")
                browser.close()
                return

        print("✅ Authenticated.")
        context.storage_state(path=STATE_FILE)

        # Scrape Users
        for user in X_TARGETS:
            try:
                page.goto(f"https://x.com/{user}", wait_until="domcontentloaded")
                all_raw_data.extend(process_x_page(page, f"User: @{user}"))
            except:
                pass

        # Scrape Hashtags
        for tag in X_HASHTAGS:
            try:
                search_url = f"https://x.com/search?q=%23{tag}%20min_faves:50&f=top"
                page.goto(search_url, wait_until="domcontentloaded")
                time.sleep(4)
                all_raw_data.extend(process_x_page(page, f"Hashtag: #{tag}"))
            except:
                pass

        # Save Top 10
        if all_raw_data:
            all_raw_data.sort(key=lambda x: x['engagement'], reverse=True)
            top_10 = all_raw_data[:10]

            os.makedirs("data", exist_ok=True)
            full_path = os.path.join("data", OUTPUT_FILE)

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(top_10, f, indent=4, ensure_ascii=False)

            context.storage_state(path=STATE_FILE)
            print(f"🏆 Data saved to {full_path}")

        browser.close()


if __name__ == "__main__":
    run()