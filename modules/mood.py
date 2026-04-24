import json
import os
from datetime import datetime

MOOD_FILE = "mood.json"

MOODS = {
    "happy": {"score": 80, "expressions": ["Ehehe~!", "Yay~!", "Aree waah~!"]},
    "neutral": {"score": 50, "expressions": ["Hmm~", "Accha accha~", "Theek hai~"]},
    "sad": {"score": 20, "expressions": ["Haww~", "Aree yaar~", "Kya baat hai~"]},
    "bored": {"score": 30, "expressions": ["Hmmmm~", "Kuch karo yaar~", "Boring hai~"]},
    "excited": {"score": 90, "expressions": ["KYAA~!", "OMG yaar~!", "Aree waah waah~!"]},
}

def load_mood():
    try:
        if os.path.exists(MOOD_FILE):
            with open(MOOD_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"mood": "happy", "score": 80, "last_interaction": None, "interaction_count": 0}

def save_mood(mood_data):
    with open(MOOD_FILE, "w") as f:
        json.dump(mood_data, f, indent=2)

def get_current_mood():
    mood_data = load_mood()
    return mood_data["mood"]

def update_mood(interaction_type="positive"):
    mood_data = load_mood()
    score = mood_data["score"]

    if interaction_type == "positive":
        score = min(100, score + 10)
    elif interaction_type == "negative":
        score = max(0, score - 10)
    elif interaction_type == "ignored":
        score = max(0, score - 5)

    mood_data["interaction_count"] += 1
    mood_data["last_interaction"] = datetime.now().isoformat()

    if score >= 80:
        mood_data["mood"] = "excited" if score >= 90 else "happy"
    elif score >= 50:
        mood_data["mood"] = "neutral"
    elif score >= 30:
        mood_data["mood"] = "bored"
    else:
        mood_data["mood"] = "sad"

    mood_data["score"] = score
    save_mood(mood_data)
    return mood_data["mood"]

def get_mood_expression():
    mood = get_current_mood()
    import random
    expressions = MOODS[mood]["expressions"]
    return random.choice(expressions)

def get_mood_context():
    mood_data = load_mood()
    mood = mood_data["mood"]
    score = mood_data["score"]
    count = mood_data["interaction_count"]
    
    context = f"Tera current mood: {mood} (score: {score}/100). "
    
    if mood == "sad":
        from modules.config import get
        owner = get("owner", "User")
        context += f"Tu thodi sad hai kyunki {owner} ne zyada baat nahi ki. "

    elif mood == "bored":
        context += "Tu thodi bored hai — kuch interesting karna chahti hai. "
    elif mood == "excited":
        context += "Tu bahut excited hai aaj! "
    elif mood == "happy":
        context += "Tu khush hai aaj! "
    
    return context