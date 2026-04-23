import json
import requests
import os
from openai import OpenAI
from dotenv import load_dotenv
from dedup import deduplicate, update_history

# =========================
# LOAD ENV
# =========================
load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("CHANNEL_ID")
MODEL = os.getenv("MODEL", "meta/llama-3.1-70b-instruct")

if not NVIDIA_API_KEY or not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
    raise ValueError("❌ Missing required environment variables")

# =========================
# INIT CLIENT
# =========================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# =========================
# LOAD JSON FILES
# =========================
def load_json_files(paths):
    all_posts = []

    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, list):
                    all_posts.extend(data)
                else:
                    print(f"⚠️ Skipping {path} (not list)")
        except Exception as e:
            print(f"❌ Error loading {path}: {e}")

    return all_posts

# =========================
# NORMALIZE
# =========================
def normalize_posts(posts):
    normalized = []

    for i, p in enumerate(posts):
        try:
            post = p.copy()

            post["id"] = post.get("id") or post.get("post_id") or f"auto_{i}"

            post["content"] = (
                post.get("text")
                or post.get("content")
                or post.get("title", "")
            )

            post["likes"] = int(post.get("likes", post.get("score", 0)))
            post["comments"] = int(post.get("comments", 0))
            post["shares"] = int(post.get("shares", post.get("retweets", 0)))

            post["url"] = post.get("url") or post.get("link") or ""

            normalized.append(post)

        except Exception as e:
            print(f"⚠️ Skipping bad post: {e}")

    return normalized

# =========================
# LLM ANALYZER
# =========================
def analyze_posts(posts):
    prompt = f"""
You are an expert social media analyst.

Analyze ALL posts and select TOP 5.

Rules:
- Use ONLY given posts
- DO NOT invent anything
- Always include URL if present

Criteria:
- Engagement
- Virality
- Content quality

FORMAT:

🔥 Top 5 Posts

1. ID: <id>
Content: <short snippet>
Link: <url>
Stats: Likes X | Comments Y | Shares Z
Reason: <why selected>

Posts:
{json.dumps(posts, indent=2)}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1200
    )

    return response.choices[0].message.content

# =========================
# SPLIT MESSAGE
# =========================
def split_message(text, size=3500):
    return [text[i:i+size] for i in range(0, len(text), size)]

# =========================
# SEND TO SLACK
# =========================
def send_to_slack_bot(message):
    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    for chunk in split_message(message):
        payload = {
            "channel": SLACK_CHANNEL,
            "text": chunk
        }

        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        if not data.get("ok"):
            print("❌ Slack error:", data)
        else:
            print("✅ Sent to Slack")

# =========================
# PIPELINE (UPDATED CORE)
# =========================
def run_pipeline(json_files):
    print("📂 Loading data...")
    posts = load_json_files(json_files)

    if not posts:
        print("❌ No posts")
        return

    print(f"📊 Raw posts: {len(posts)}")

    # =========================
    # NORMALIZE
    # =========================
    posts = normalize_posts(posts)

    # =========================
    # 🔥 DEDUP (CRITICAL)
    # =========================
    print("🧹 Deduplicating...")
    posts = deduplicate(posts)

    print(f"✅ After dedup: {len(posts)}")

    if len(posts) < 5:
        print("⚠️ Not enough unique content")
        return

    # =========================
    # SORT BY ENGAGEMENT
    # =========================
    posts.sort(
        key=lambda x: x["likes"] + x["comments"] + x["shares"],
        reverse=True
    )

    # =========================
    # LIMIT INPUT TO LLM
    # =========================
    posts_for_llm = posts[:30]

    print(f"🧠 Sending {len(posts_for_llm)} posts to LLM...")

    result = analyze_posts(posts_for_llm)

    # =========================
    # SEND OUTPUT
    # =========================
    send_to_slack_bot(result)

    # =========================
    # UPDATE HISTORY (TOP POSTS)
    # =========================
    update_history(posts[:5])

    return result

# =========================
# RUN
# =========================
if __name__ == "__main__":
    FILES = [
        "data/linkedin_data.json",
        "data/reddit_data.json",
        "data/tweets.json"
    ]

    output = run_pipeline(FILES)

    print("\n" + "=" * 60)
    print(output)
    print("=" * 60)