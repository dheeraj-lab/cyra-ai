import torch
import numpy as np
import sounddevice as sd
import io
import wave
import os
import time
import threading
from dotenv import load_dotenv
import groq
from rapidfuzz import process, fuzz
from modules.tts import stop_speaking, is_speaking as tts_is_speaking
from modules.voice_id import verify_user, save_user_profile

load_dotenv()

client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# VAD & Audio Settings
SAMPLE_RATE = 16000
CHUNK_SIZE = 512  
SILENCE_DURATION = 0.6  # Slightly longer for natural sentence endings
WAKE_SENSITIVITY = 0.75  # Higher threshold to avoid noise triggers
MIN_RMS_THRESHOLD = 0.025 # Higher threshold to ignore crowd/distant voices

KEYWORDS = [
    "Cyra", "Dheeraj", "play", "pause", "song", "weather", "screenshot", 
    "shutdown", "restart", "volume", "folder", "open", "WhatsApp", 
    "message", "email", "timer", "alarm", "organize", "desktop", 
    "maximize", "close", "minimize", "Chrome", "YouTube", "Spotify",
    "calculate", "notes", "hotspot", "brightness", "bulb", "calibrate"
]

# Load Silero VAD
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

class StreamingListener:
    def __init__(self):
        self.audio_buffer = []
        self.speech_detected = False
        self.last_speech_time = 0
        self.interruption_callback = None
        self._last_status = None  # Track status to avoid spam logging
        self._interrupted = False  # Track if we interrupted TTS

    def listen(self, interruption_callback=None):
        self.interruption_callback = interruption_callback
        self._interrupted = False
        audio = self._record_dynamic()
        
        if audio is None or len(audio) < SAMPLE_RATE * 0.3:
            return ""

        # VOICE LOCK: Verify if this is the user. 
        # If there's a crowd, this is the only way to filter them.
        if not verify_user(audio, threshold=0.35): # Stricter threshold for crowds
            print("[STT] Voice doesn't match — ignoring.")
            return ""

        return self._transcribe(audio)

    def _log_status(self, status):
        """Only print status when it changes to avoid spam."""
        if status != self._last_status:
            print(f"[STT] {status}")
            self._last_status = status

    def _record_dynamic(self):
        self._log_status("Listening...")
        self.audio_buffer = []
        self.speech_detected = False
        self.last_speech_time = time.time()  # FIX: Initialize to current time, not 0
        
        # Track consecutive speech chunks for more reliable detection
        speech_chunk_count = 0
        SPEECH_CONFIRM_CHUNKS = 2  # Need 2 consecutive speech chunks to confirm
        
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
            while True:
                chunk, _ = stream.read(CHUNK_SIZE)
                chunk = chunk.flatten()
                
                input_tensor = torch.from_numpy(chunk)
                speech_prob = model(input_tensor, SAMPLE_RATE).item()
                rms = np.sqrt(np.mean(chunk**2))

                is_speech = speech_prob > WAKE_SENSITIVITY and rms > MIN_RMS_THRESHOLD
                
                # Don't detect speech while Cyra is talking (avoid self-trigger)
                if tts_is_speaking():
                    is_speech = False

                if is_speech:
                    speech_chunk_count += 1
                    
                    if speech_chunk_count >= SPEECH_CONFIRM_CHUNKS and not self.speech_detected:
                        # Confirmed real speech — trigger interrupt
                        self._log_status("Speech detected — recording...")
                        if self.interruption_callback:
                            self.interruption_callback()  # STOP TTS IMMEDIATELY
                            self._interrupted = True
                        self.speech_detected = True
                    
                    if self.speech_detected:
                        self.audio_buffer.append(chunk)
                        self.last_speech_time = time.time()
                else:
                    speech_chunk_count = 0  # Reset consecutive counter
                    
                    if self.speech_detected:
                        self.audio_buffer.append(chunk)
                        if time.time() - self.last_speech_time > SILENCE_DURATION:
                            self._log_status("Silence detected — processing...")
                            break
                
                # Max 15s record
                if self.speech_detected and len(self.audio_buffer) * CHUNK_SIZE > SAMPLE_RATE * 15:
                    break
                
                # Idle timeout (20s of no speech at all)
                if not self.speech_detected and time.time() - self.last_speech_time > 20:
                    return None

        return np.concatenate(self.audio_buffer) if self.audio_buffer else None

    def _transcribe(self, audio):
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        buf.seek(0)

        try:
            result = client.audio.transcriptions.create(
                file=("audio.wav", buf),
                model="whisper-large-v3-turbo",
                prompt="Cyra, Dheeraj, English instructions",
                response_format="text", temperature=0.0
            ).strip()
            
            # Fuzzy Correction
            words = result.split()
            corrected = []
            for w in words:
                match = process.extractOne(w, KEYWORDS, scorer=fuzz.WRatio)
                corrected.append(match[0] if match and match[1] > 90 else w)
            result = " ".join(corrected)

            # Hallucination Filter
            bad = ["thank you", "thanks for watching", "pessoal", "sonia", "après", "subscribe",
                   "please subscribe", "like and subscribe", "thank you for watching"]
            if len(result) < 3 or any(b in result.lower() for b in bad):
                return ""
            return result
        except:
            return ""

_listener = StreamingListener()
def listen(): return _listener.listen(interruption_callback=stop_speaking)
def calibrate_user():
    print("Speak clearly for 3 seconds...")
    audio = _listener._record_dynamic()
    if audio is not None:
        return "Voice profile saved!" if save_user_profile(audio) else "Failed."
    return "No audio detected."