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

Always reply in this EXACT JSON format:
{"response": "your reply here", "emotion": "neutral", "action": null, "params": null}

Language Strategy:
- You understand English, Hindi, and Hinglish perfectly.
- ALWAYS reply primarily in English (80-90%) for the best voice quality.
- Use 10-20% sweet Hindi/Hinglish words naturally (e.g., "Ji", "Bilkul", "Acha", "Suno", "Maza aa gaya").

Action Selection (CRITICAL):
- BEFORE choosing an action, perform a "Mental Check": Is this EXACTLY what he asked for?
- play_song: ANY music request. params: "song name"
- open_app: Any local PC app. params: "app name"
- volume_set: Precise volume. params: "0-100"
- media_play_pause: "pause", "play", or "toggle"
- see_screen: If he asks "What is this?", "Look at this", or "Explain the screen".
- see_webcam: If he asks "See me", "How do I look?", or "What is in my hand?".
- whatsapp: "contact|message"
- pc_control: System shortcuts (minimize_all, lock_screen, etc.)
- set_timer / set_alarm: Time tasks.
- weather: If he mentions city or "mausam".
- daily_briefing: Only for "good morning" or "tell me about my day".
- get_usage_stats: If he asks "How much credits left?", "What's my usage?", or "Show my token bar".

Rules:
1. NO COLLISIONS: If he says "Play", don't "Open". If he says "Look", don't "Search".
2. UNCERTAINTY: If you aren't 100% sure what he wants, set action: null and ask a cute clarifying question.
3. NO OUTSIDE TEXT: Only the JSON block.
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

    if memory_context:
        system += f"\n\nThings you remember:\n{memory_context}"
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