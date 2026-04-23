from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = "config.json"


# =========================
# UTILITIES
# =========================
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# =========================
# MODELS (SEPARATE PER PLATFORM = CLEAN UI MATCH)
# =========================
class RedditModel(BaseModel):
    subreddits: List[str]
    keywords: Optional[List[str]] = []


class LinkedInModel(BaseModel):
    profiles: List[str]
    keywords: Optional[List[str]] = []


class TwitterModel(BaseModel):
    usernames: List[str]
    keywords: Optional[List[str]] = []


# =========================
# REDDIT
# =========================
@app.post("/config/reddit")
def update_reddit(data: RedditModel):
    config = load_config()
    config.setdefault("reddit", {})

    config["reddit"]["subreddits"] = data.subreddits
    config["reddit"]["keywords"] = data.keywords

    save_config(config)
    return {"success": True, "reddit": config["reddit"]}


# =========================
# LINKEDIN
# =========================
@app.post("/config/linkedin")
def update_linkedin(data: LinkedInModel):
    config = load_config()
    config.setdefault("linkedin", {})

    config["linkedin"]["profiles"] = data.profiles
    config["linkedin"]["keywords"] = data.keywords

    save_config(config)
    return {"success": True, "linkedin": config["linkedin"]}


# =========================
# TWITTER / X
# =========================
@app.post("/config/twitter")
def update_twitter(data: TwitterModel):
    config = load_config()
    config.setdefault("twitter", {})

    config["twitter"]["usernames"] = data.usernames
    config["twitter"]["keywords"] = data.keywords

    save_config(config)
    return {"success": True, "twitter": config["twitter"]}


# =========================
# GET FULL CONFIG (dashboard load)
# =========================
@app.get("/config")
def get_config():
    return load_config()