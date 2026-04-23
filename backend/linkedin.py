import time
import json
import re
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
# ==== LOAD CONFIG ====
CONFIG_FILE = "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TARGET_USERS = CONFIG["linkedin"]["profiles"]
HASHTAGS = CONFIG["linkedin"]["keywords"]
# ==== CONFIG ====
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

STATE_FILE = "linkedin_state.json"
POSTS_PER_SOURCE = 10


def clean_count(text):
    if not text: return 0
    text = text.lower().replace(',', '').strip()
    match = re.search(r"(\d+[\d,.]*)([km]?)", text)
    if not match: return 0
    num, multiplier = match.groups()
    num = float(num)
    if multiplier == 'k':
        num *= 1000
    elif multiplier == 'm':
        num *= 1000000
    return int(num)


def scrape_post_data(element):
    """Parses a single post container."""
    try:
        html = element.inner_html()
        soup = BeautifulSoup(html, 'html.parser')

        author = soup.select_one('.update-components-actor__title, [class*="actor__name"]')
        name = author.get_text(strip=True) if author else "Unknown"

        likes = clean_count(
            soup.select_one('.social-details-social-counts__reactions-count').get_text()) if soup.select_one(
            '.social-details-social-counts__reactions-count') else 0
        comments = clean_count(
            soup.select_one('.social-details-social-counts__comments').get_text()) if soup.select_one(
            '.social-details-social-counts__comments') else 0

        link_tag = soup.select_one('a[href*="activity"], a[href*="ugcPost"]')
        link = link_tag['href'].split('?')[0] if link_tag else "N/A"
        if link != "N/A" and not link.startswith('http'): link = "https://www.linkedin.com" + link

        return {
            "author": name,
            "likes": likes,
            "comments": comments,
            "engagement": likes + comments,
            "link": link
        }
    except Exception as e:
        print(f"   ⚠️ DEBUG: Error parsing a post container: {e}")
        return None


def process_page(page, source_label):
    """Scrolls and scrapes posts from the current page."""
    results = []
    processed_ids = set()

    print(f"🔎 DEBUG: Scraping {source_label}...")

    for _ in range(3):  # 3 scroll batches
        posts = page.query_selector_all('.feed-shared-update-v2, div[role="listitem"]')
        for box in posts:
            if len(results) >= POSTS_PER_SOURCE: break

            p_id = box.get_attribute("data-urn") or box.inner_text()[:30]
            if p_id in processed_ids: continue

            try:
                box.scroll_into_view_if_needed(timeout=5000)
                time.sleep(1)

                data = scrape_post_data(box)
                if data:
                    data["source"] = source_label
                    results.append(data)
                    processed_ids.add(p_id)
                    print(f"   📥 Found Post: {data['likes']} likes ({data['author']})")
            except Exception:
                continue

        if len(results) >= POSTS_PER_SOURCE: break
        page.mouse.wheel(0, 2000)
        time.sleep(2)
    return results


def main():
    all_raw_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        if os.path.exists(STATE_FILE):
            print("🍪 DEBUG: Loading session from state file...")
            context = browser.new_context(storage_state=STATE_FILE)
        else:
            context = browser.new_context()

        page = context.new_page()
        page.set_default_navigation_timeout(45000)

        # 2. Login Logic
        try:
            page.goto("https://www.linkedin.com/feed/")
            time.sleep(3)
            if "login" in page.url:
                print("🔐 DEBUG: Logging in...")
                page.goto("https://www.linkedin.com/login")
                page.fill("#username", LINKEDIN_EMAIL)
                page.fill("#password", LINKEDIN_PASSWORD)
                page.click("button[type='submit']")
                page.wait_for_url("**/feed/**")
                context.storage_state(path=STATE_FILE)
        except Exception as e:
            print(f"❌ CRITICAL: Login navigation failed: {e}")
            browser.close()
            return

        # 3. Scrape TARGET USERS
        for user in TARGET_USERS:
            try:
                print(f"\n👤 DEBUG: Navigating to {user}...")
                page.goto(f"https://www.linkedin.com/in/{user}/recent-activity/all/", wait_until="domcontentloaded")
                time.sleep(5)
                all_raw_data.extend(process_page(page, f"User: {user}"))
            except Exception as e:
                print(f"⚠️ ERROR: Problem with user {user}: {e}")

        # 4. Scrape HASHTAGS
        for tag in HASHTAGS:
            try:
                print(f"\n#️⃣ DEBUG: Navigating to #{tag}...")
                page.goto(f"https://www.linkedin.com/search/results/content/?keywords=%23{tag}&sortBy=%22date%22",
                          wait_until="domcontentloaded")
                time.sleep(5)
                all_raw_data.extend(process_page(page, f"Hashtag: #{tag}"))
            except Exception as e:
                print(f"⚠️ ERROR: Problem with hashtag #{tag}: {e}")

        # --- SECTION 5: GLOBAL VIRALITY FILTER (OUTSIDE ALL LOOPS) ---
        if not all_raw_data:
            print("\n❌ DEBUG: No data collected from any source.")
        else:
            print(f"\n📊 DEBUG: Total scraped: {len(all_raw_data)}")
            all_raw_data.sort(key=lambda x: x['engagement'], reverse=True)
            top_10 = all_raw_data[:10]

            # 1. Create the 'data' folder
            os.makedirs("data", exist_ok=True)

            # 2. Define the full path
            file_path = os.path.join("data", "linkedin_data.json")

            # 3. Save
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(top_10, f, indent=4, ensure_ascii=False)

            print(f"\n🏁 Successfully saved {len(top_10)} posts to: {file_path}")

        browser.close()

if __name__ == "__main__":
    main()