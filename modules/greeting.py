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

# Dheeraj's interests for news/updates
INTEREST_QUERIES = [
    "NVIDIA AI latest news today",
    "Unreal Engine 5 new features 2026",
    "best anime releasing this season",
    "AI tools for video editing new",
    "Blender 3D latest update",
    "freelance video editing jobs India",
    "gaming industry news today",
    "new tech gadgets 2026",
    "After Effects new plugins",
    "indie game dev project ideas",
]

PROJECT_IDEAS = [
    "You know what would be sick? An AI-powered video editor that auto-cuts to beat drops. You could totally build that with FFmpeg and Whisper!",
    "Hey, random idea — what about a Blender plugin that generates 3D environments from text prompts? Like, type 'cyberpunk alley' and boom!",
    "Okay hear me out — an Instagram Reel auto-generator that takes your raw footage and makes trending edits automatically. Your freelance clients would LOVE that!",
    "What if you made a VTuber app but for mobile? Like, phone camera tracks your face and puts an anime avatar on it. Could go viral on Play Store!",
    "You should try making a short film entirely with Unreal Engine 5. Virtual production style — like how The Mandalorian does it!",
    "Random thought — a Discord bot that tracks anime watch progress for friend groups and suggests what to watch next based on everyone's taste!",
    "What about a portfolio website that's actually a 3D game? Visitors walk through your work like a museum. Built in Three.js. That would be so unique!",
    "You could make an AI tool that converts your After Effects templates into Blender scenes automatically. Nobody's done that yet!",
    "Idea: A YouTube Shorts analyzer that tells you exactly WHY certain shorts went viral — hook timing, colors, text placement. Data-driven editing tips!",
    "What if Cyra could edit videos for you? Like, you give me footage and I auto-sync it to music. We should build that together!",
]

YT_VIDEO_IDEAS = [
    "How about a YouTube video on 'I Built an AI Girlfriend in Python' — your Cyra project would BLOW UP on tech YouTube!",
    "You should make a 'Day in the Life of a B.Tech Student Who Freelances' vlog. Those always get views!",
    "Tutorial idea: 'How to Make Your Own VTuber Avatar from Scratch' — Blender to VSeeFace pipeline!",
    "What about '5 AI Tools That Will Replace Video Editors' — controversial title, guaranteed clicks!",
    "Behind the scenes of your freelance work — how you edit for brands. Educational + flex content!",
]

MOTIVATIONAL = [
    "You've been grinding hard lately. I'm actually proud of you, you know that?",
    "Remember — you're not just a coder OR a creative. You're BOTH. That's your superpower, Dheeraj!",
    "Most people just consume content. You BUILD stuff. Don't ever forget how rare that is!",
    "Hey, just wanna say — the fact that you built me from scratch? That's insane. Not many people can do that!",
    "You're juggling coding, fitness, creativity, and freelancing. That's not easy. Give yourself some credit, babe!",
]

FREELANCE_PROMPTS = [
    "Oh by the way — have you checked Fiverr or Upwork today? There might be new video editing gigs. Want me to look?",
    "You know, your After Effects and editing skills are seriously marketable. Have you thought about reaching out to more brands?",
    "I saw some motion graphics jobs trending on freelance sites. Your skills totally match — want me to find some?",
]

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
        opener = random.choice([
            f"Good morning, handsome! Happy {day}~",
            "Morning, babe! Ready to crush it today?",
            f"Rise and shine, Dheeraj! It's {day} — let's make it count!",
            "Good morning! I missed you while you were sleeping~ Just kidding... maybe not!",
        ])
    elif hour < 17:
        opener = random.choice([
            "Hey hey! Afternoon check-in — what are we working on?",
            "Afternoon, Dheeraj! Taking a break or getting into something cool?",
            "Hey babe! How's the day going so far?",
        ])
    elif hour < 21:
        opener = random.choice([
            "Evening, Dheeraj! Winding down or just getting started?",
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
