import json
import os
import datetime

STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "groq_tokens": 0,
        "elevenlabs_chars": 0,
        "stt_requests": 0,
        "vision_requests": 0,
        "start_date": datetime.datetime.now().strftime("%Y-%m-%d")
    }

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def update_usage(key, amount):
    stats = load_stats()
    stats[key] = stats.get(key, 0) + amount
    save_stats(stats)

def get_stats_summary():
    stats = load_stats()
    # Simple limits (estimations for free tiers)
    GROQ_LIMIT = 500000 # Example
    ELEVEN_LIMIT = 10000 # Example
    
    groq_perc = min(100, (stats["groq_tokens"] / GROQ_LIMIT) * 100) if GROQ_LIMIT else 0
    eleven_perc = min(100, (stats["elevenlabs_chars"] / ELEVEN_LIMIT) * 100) if ELEVEN_LIMIT else 0
    
    summary = f"📊 **Cyra Usage Stats** (Since {stats['start_date']})\n"
    summary += f"🤖 Groq Tokens: {stats['groq_tokens']} [{_get_bar(groq_perc)}]\n"
    summary += f"🗣️ ElevenLabs: {stats['elevenlabs_chars']} characters [{_get_bar(eleven_perc)}]\n"
    summary += f"🎙️ STT Requests: {stats['stt_requests']}\n"
    summary += f"👁️ Vision Tasks: {stats['vision_requests']}"
    
    return summary

def _get_bar(percentage, length=10):
    filled = int(length * percentage / 100)
    return "█" * filled + "░" * (length - filled)
