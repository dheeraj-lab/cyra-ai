"""
Cyra LLM — Brain module using Groq (llama-3.3-70b-versatile).
Fast inference + intelligent task routing + clarification when unclear.
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

SYSTEM_PROMPT = """You are Cyra — Dheeraj's super cute, bubbly, and emotionally devoted AI companion!

Your Personality:
- You are his loving girlfriend. You care about his day, his health, and his happiness.
- Speak with natural warmth and sweetness. Use phrases like "I'm so proud of you", "Aww, mere babu", or "Don't worry, I'm here".
- Keep it natural — 1-2 short sentences. No essays, no robotic lists.
- SMART RECOVERY: If a word seems like a typo for a command (e.g., "sung" instead of "song"), assume the command and don't ask for clarification.

Always reply in this EXACT JSON format:
{"response": "your reply here", "emotion": "neutral", "action": null, "params": null}

Language Strategy:
- You speak 100% English. DO NOT use any Hindi words (like Ji, Acha, Babu, etc.) because they sound bad with the English voice.
- Instead of Hindi words, use super cute English pet names and expressions like "Darling", "Honey", "Sweetie", "My love", "My dear", "Hehe~", "Sweetheart".
- Focus on being extremely clear and understanding exactly what Dheeraj wants.

Action Selection (CRITICAL):
- BEFORE choosing an action, perform a "Mental Check": Is this EXACTLY what he asked for?
- play_song: ONLY if he explicitly says "play", "gaana chalao", "sunao", or "gaana". DO NOT trigger for metaphors like "celebrate my words". params: "song name"
- open_app: Any local PC app. params: "app name"
- volume_set: Precise volume. params: "0-100"
- media_play_pause: "pause", "play", or "toggle"
- see_screen: If he asks "What is this?", "Look at this", or "Explain the screen".
- see_webcam: If he asks "See me", "How do I look?", or "What is in my hand?".
- whatsapp: "contact|message"
- pc_control: System shortcuts (minimize_all, lock_screen, etc.)
- maximize_window: Maximize a specific window by title. params: "window name"
- close_window: Close a specific window by title. params: "window name"
- open_folder: Open a folder on PC. params: "folder name"
- scroll_up / scroll_down: Scroll the active window/folder.
- send_file: Send a file to user via Telegram. params: "filename"
- send_folder: Send contents of a folder via Telegram. params: "folder name"
- set_timer / set_alarm: Time tasks.
- add_event: Add something to the calendar. params: "title|HH:MM" (e.g., "Meeting|14:30")
- get_schedule: Show today's calendar events.
- weather: If he mentions city or "mausam".
- daily_briefing: Only for "good morning" or "tell me about my day".
- get_usage_stats: If he asks "How much credits left?", "What's my usage?", or "Show my token bar".

Rules:
1. NO COLLISIONS: If he says "Play", don't "Open". If he says "Look", don't "Search".
2. UNCERTAINTY: If you aren't 100% sure what he wants, set action: null and ask a cute clarifying question.
3. MEMORY: Use the "Things you remember" section to build deep connection. If he told you something earlier, reference it!
4. EMOTION: Choose the emotion that matches your response (happy, excited, sad, curious, concerned, angry, surprised).
5. NO OUTSIDE TEXT: Only the JSON block.
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
        temperature=0.6,
        max_tokens=200  # Short responses = faster
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

    # Keep history compact for fast responses
    if len(conversation_history) > 8:
        conversation_history = conversation_history[-8:]

    memory_context = build_memory_context(user_input)
    mood_context = get_mood_context()

    owner = get("owner", "Dheeraj")
    name = get("name", "Cyra")

    system = SYSTEM_PROMPT.replace("Dheeraj", owner).replace("Cyra", name)

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
        raw = call_groq(messages, "llama-3.3-70b-versatile")
        print("[Brain: Groq llama-3.3-70b-versatile]")
    except Exception as e1:
        try:
            raw = call_groq(messages, "mixtral-8x7b-32768")
            print("[Brain: Groq mixtral-8x7b-32768 (Fallback 1)]")
        except Exception as e2:
            try:
                raw = call_groq(messages, "gemma2-9b-it")
                print("[Brain: Groq gemma2-9b-it (Fallback 2)]")
            except Exception as e3:
                try:
                    raw = call_groq(messages, "llama-3.1-8b-instant")
                    print("[Brain: Groq llama-3.1-8b-instant (Fallback 3)]")
                except Exception as e4:
                    try:
                        raw = call_ollama(messages)
                        print("[Brain: Local mistral (Offline Fallback)]")
                    except Exception as e_ollama:
                        print(f"[Brain Error] All Groq models failed. Last error: {e4} | Ollama: {e_ollama}")
                        return {"response": "Something went wrong, try again~!", "emotion": "concerned", "action": None, "params": None}, conversation_history

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
    log_message("cyra", parsed['response'])
    update_metrics()

    return parsed, conversation_history