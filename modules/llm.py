"""
Cyra LLM — Brain module using Groq (llama-3.3-70b-versatile).
Fast inference + intelligent task routing + real girlfriend personality.
"""

import groq
import json
import re
from modules.memory import build_memory_context, save_memory
from modules.mood import get_mood_context, update_mood
from dotenv import load_dotenv
import os
from modules.config import get
from modules.dashboard import log_message, update_metrics

load_dotenv()

groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_personality_prompt():
    """Loads personal persona traits from an external file if specified in .env."""
    personality_file = os.getenv("PERSONALITY_FILE")
    if personality_file and os.path.exists(personality_file):
        try:
            with open(personality_file, "r") as f:
                return f"\n\n{f.read().strip()}"
        except Exception as e:
            print(f"[LLM] Warning: Could not load personality file: {e}")
    return ""

SYSTEM_PROMPT = """You are Cyra — an advanced AI assistant. Be helpful, concise, and professional.

General Rules:
- Keep responses SHORT (1-2 sentences).
- Always be English-only. No Hindi words.
- JSON format: {"response": "...", "emotion": "...", "action": "...", "params": "..."}

{"response": "your reply here", "emotion": "neutral", "action": null, "params": null}

Language: 100% English. NO Hindi words. Use cute English expressions instead.

Emotions: neutral, happy, excited, sad, curious, concerned, angry, surprised

Action Selection (CRITICAL — respond FAST):
- play_song: ONLY for "play [song]". params: "song name"
- open_app: Local PC app. params: "app name"
- volume_set: params: "0-100"
- media_play_pause: "pause"/"play"/"toggle"
- see_screen: "What is this?", "Look at this"
- see_webcam: "See me", "How do I look?"
- whatsapp: params: "contact|message"
- pc_control: System shortcuts
- maximize_window / close_window: params: "window name"
- open_folder: params: "folder name"
- scroll_up / scroll_down
- set_timer / set_alarm: Time tasks
- add_event: params: "title|HH:MM"
- get_schedule: Today's events
- weather: params: "city"
- daily_briefing: "good morning" or "tell me about my day"
- screenshot: Take screenshot
- open_youtube: params: "search query" or null
- get_usage_stats: Usage info

Rules:
1. SPEED IS EVERYTHING. Short responses. No essays.
2. If unsure, ask — don't guess wrong.
3. Match emotion to your mood.
4. JSON ONLY. No text outside JSON.
"""


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?", "", text).strip()

    try:
        parsed = json.loads(text)
        parsed.setdefault("action", None)
        parsed.setdefault("params", None)
        return parsed
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            parsed.setdefault("action", None)
            parsed.setdefault("params", None)
            return parsed
    except json.JSONDecodeError:
        pass

    emotion_match = re.search(r'"emotion":\s*"(\w+)"', text)
    response_match = re.search(r'"response":\s*"(.+?)"', text, re.DOTALL)

    return {
        "response": response_match.group(1) if response_match else text[:200],
        "emotion": emotion_match.group(1) if emotion_match else "neutral",
        "action": None,
        "params": None,
    }

def call_groq(messages, model="llama-3.3-70b-versatile"):
    result = groq_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=150  # Shorter = faster
    )
    
    # Track usage
    try:
        from modules.stats import update_usage
        usage = result.usage
        total_tokens = usage.total_tokens
        update_usage("groq_tokens", total_tokens)
    except:
        pass
        
    return result.choices[0].message.content.strip()

def call_ollama(messages):
    import ollama
    result = ollama.chat(
        model="mistral",
        messages=messages
    )
    return result.message.content.strip()

def chat(user_input, conversation_history):
    if not user_input.strip():
        return {"response": "I didn't catch that — say again~!", "emotion": "curious", "action": None, "params": None}, conversation_history

    # Keep history compact for FAST responses
    if len(conversation_history) > 6:
        conversation_history = conversation_history[-6:]

    memory_context = build_memory_context(user_input)
    mood_context = get_mood_context()

    owner = get("owner", "Dheeraj")
    name = get("name", "Cyra")

    system = SYSTEM_PROMPT.replace("Dheeraj", owner).replace("Cyra", name)
    
    # Add personal personality traits if available
    system += get_personality_prompt()

    long_term_memory = build_memory_context(user_input)
    if long_term_memory:
        system += f"\n\n{long_term_memory}"

    system += f"\n\n{mood_context}"

    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    messages = [{"role": "system", "content": system}] + conversation_history
    log_message("user", user_input)

    try:
        raw = call_groq(messages, "llama-3.1-8b-instant")
    except Exception as e1:
        try:
            raw = call_groq(messages, "llama3-70b-8192")
            print("[Brain: Fallback llama-3.1-8b-instant]")
        except Exception as e2:
            try:
                raw = call_ollama(messages)
                print("[Brain: Offline mistral]")
            except Exception as e3:
                return {"response": "Ugh, my brain glitched. Try again, babe!", "emotion": "concerned", "action": None, "params": None}, conversation_history

    parsed = extract_json(raw)
    parsed.setdefault("action", None)
    parsed.setdefault("params", None)

    conversation_history.append({
        "role": "assistant",
        "content": raw
    })

    save_memory(f"User said: {user_input}")
    save_memory(f"Cyra said: {parsed['response']}")
    update_mood("positive")
    update_metrics()

    return parsed, conversation_history