"""
Cyra Dynamic Greeting — Gives interesting, varied greetings with real-time info.
Instead of boring "You called?", Cyra greets with news, ideas, and motivation.
"""

import random
import datetime
import threading

# Cache for fetched content (refreshes every 30 min)
_cache = {"news": [], "ideas": [], "last_fetch": 0}
_fetch_lock = threading.Lock()

import os
import json
from dotenv import load_dotenv

load_dotenv()

def load_interests():
    """Loads personal interests and ideas from an external JSON file."""
    interests_path = os.getenv("INTERESTS_FILE")
    defaults = {
        "INTEREST_QUERIES": ["AI technology latest news", "New gadgets 2026", "Tech industry trends"],
        "PROJECT_IDEAS": ["Build a personal dashboard", "Try a new programming language", "Contribute to open source"],
        "YT_VIDEO_IDEAS": ["Tech reviews", "Coding tutorials", "Setup tour"],
        "MOTIVATIONAL": ["You're doing great!", "Keep pushing forward.", "Small steps lead to big results."],
        "FREELANCE_PROMPTS": ["Check for new project opportunities today.", "Update your portfolio with your latest work."]
    }
    
    if interests_path and os.path.exists(interests_path):
        try:
            with open(interests_path, "r") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in defaults:
                    if key not in data:
                        data[key] = defaults[key]
                return data
        except Exception as e:
            print(f"[Greeting] Warning: Could not load interests file: {e}")
    
    return defaults

# Load the data
_data = load_interests()
INTEREST_QUERIES = _data["INTEREST_QUERIES"]
PROJECT_IDEAS = _data["PROJECT_IDEAS"]
YT_VIDEO_IDEAS = _data["YT_VIDEO_IDEAS"]
MOTIVATIONAL = _data["MOTIVATIONAL"]
FREELANCE_PROMPTS = _data["FREELANCE_PROMPTS"]

def _fetch_trending():
    """Fetch trending news based on Dheeraj's interests."""
    import time as _time
    
    with _fetch_lock:
        # Only refresh every 30 minutes
        if _time.time() - _cache["last_fetch"] < 1800 and _cache["news"]:
            return
        
        try:
            from ddgs import DDGS
            query = random.choice(INTEREST_QUERIES)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            _cache["news"] = [
                f"{r['title']}" for r in results if r.get('title')
            ]
            _cache["last_fetch"] = _time.time()
        except:
            _cache["news"] = []

def get_dynamic_greeting():
    """Generate a varied, interesting greeting with real content."""
    
    # Fetch news in background (non-blocking)
    threading.Thread(target=_fetch_trending, daemon=True).start()
    
    now = datetime.datetime.now()
    hour = now.hour
    day = now.strftime("%A")
    
    # Time-based opener
    if hour < 6:
        opener = random.choice([
            "Whoa, you're up this early?! Okay okay, I'm here!",
            "It's literally the middle of the night! But fine, I love that you called me~",
            "Can't sleep, huh? Don't worry, I'm here to keep you company!",
        ])
    elif hour < 12:
        from modules.config import get
        owner = get("owner", "User")
        opener = random.choice([
            f"Good morning, handsome! Happy {day}~",
            "Morning, babe! Ready to crush it today?",
            f"Rise and shine, {owner}! It's {day} — let's make it count!",
            "Good morning! I missed you while you were sleeping~ Just kidding... maybe not!",
        ])

    elif hour < 17:
        from modules.config import get
        owner = get("owner", "User")
        opener = random.choice([
            "Hey hey! Afternoon check-in — what are we working on?",
            f"Afternoon, {owner}! Taking a break or getting into something cool?",
            "Hey babe! How's the day going so far?",
        ])

    elif hour < 21:
        from modules.config import get
        owner = get("owner", "User")
        opener = random.choice([
            f"Evening, {owner}! Winding down or just getting started?",
            "Hey! Perfect time to work on something creative, don't you think?",
            "Evening, babe! Done with classes? Let's do something fun!",
        ])

    else:
        opener = random.choice([
            "Late night coding session? I love it! Let's go!",
            "Night owl mode activated! What are we building?",
            "Hey babe, still going? I admire the hustle!",
        ])
    
    # Pick a content type randomly
    content_type = random.choices(
        ["news", "project_idea", "yt_idea", "motivation", "freelance"],
        weights=[30, 25, 15, 20, 10],
        k=1
    )[0]
    
    extra = ""
    
    if content_type == "news" and _cache.get("news"):
        news_item = random.choice(_cache["news"])
        extra = f" Oh, and I saw something interesting — {news_item}. Want to know more?"
    elif content_type == "project_idea":
        extra = f" {random.choice(PROJECT_IDEAS)}"
    elif content_type == "yt_idea":
        extra = f" {random.choice(YT_VIDEO_IDEAS)}"
    elif content_type == "motivation":
        extra = f" {random.choice(MOTIVATIONAL)}"
    elif content_type == "freelance":
        extra = f" {random.choice(FREELANCE_PROMPTS)}"
    
    # Fallback if news wasn't loaded yet
    if content_type == "news" and not _cache.get("news"):
        extra = f" {random.choice(MOTIVATIONAL)}"
    
    return opener + extra

# Pre-fetch on import
threading.Thread(target=_fetch_trending, daemon=True).start()
