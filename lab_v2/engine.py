import sys
import os

# Add parent directory to path ONLY for importing original data/logic
# But we will aim to make this engine autonomous.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.stt import listen as cyra_listen
from modules.llm import chat as cyra_chat
from modules.tts import speak as cyra_speak

class LabEngine:
    """Autonomous engine for Lab V2 experiments."""
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.history = []

    def process_input(self):
        """Listen and respond using Cyra's logic but within the Lab context."""
        self.log_callback("Listening...")
        user_input = cyra_listen()
        
        if not user_input:
            return None, None

        self.log_callback(f"User: {user_input}")
        
        # Get response using original LLM logic
        response, self.history = cyra_chat(user_input, self.history)
        
        self.log_callback(f"Cyra AI: {response['response']}")
        
        # We can add Lab-Specific logic here
        # E.g., intercepting actions to do something else in the Lab App
        
        return response, user_input

    def speak_response(self, text, emotion):
        cyra_speak(text, emotion)
