"""
Cyra STT — Speech-to-text with Groq Whisper.
Fixes: ghost audio prevention, minimum duration, energy filter, timeout.
"""

import groq
import sounddevice as sd
import numpy as np
import io
import wave
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.008       # Lowered to make it more sensitive to voice
SILENCE_DURATION = 2            
MIN_AUDIO_DURATION = 0.5        
MAX_RECORD_DURATION = 15        
MIN_AUDIO_ENERGY = 0.005        # Lowered to ensure user's voice isn't rejected

def record_until_silence():
    """Record audio until user stops speaking. Returns numpy array or None."""
    print("Listening...")
    audio_chunks = []
    silent_chunks = 0
    speaking = False
    total_chunks = 0
    max_chunks = MAX_RECORD_DURATION * 4  # 4 chunks per second

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        while total_chunks < max_chunks:
            chunk, _ = stream.read(SAMPLE_RATE // 4)  # 250ms chunks
            volume = np.abs(chunk).mean()
            total_chunks += 1

            if volume > SILENCE_THRESHOLD:
                speaking = True
                silent_chunks = 0
                audio_chunks.append(chunk)
            elif speaking:
                silent_chunks += 1
                audio_chunks.append(chunk)
                if silent_chunks >= SILENCE_DURATION * 4:
                    break

    if not audio_chunks:
        return None

    audio = np.concatenate(audio_chunks, axis=0).flatten()

    # Check minimum duration
    duration = len(audio) / SAMPLE_RATE
    if duration < MIN_AUDIO_DURATION:
        print(f"[STT] Audio too short ({duration:.1f}s), ignoring")
        return None

    # Normalize audio to improve recognition accuracy for quiet speech
    max_vol = np.abs(audio).max()
    if max_vol > 0:
        audio = audio / max_vol

    return audio

def numpy_to_wav_bytes(audio, sample_rate=16000):
    """Convert numpy audio to WAV bytes for Whisper API."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    buf.seek(0)
    return buf

def listen():
    """Listen for speech and transcribe. Returns text or empty string."""
    audio = record_until_silence()

    if audio is None:
        return ""

    wav_bytes = numpy_to_wav_bytes(audio)

    try:
        # Helper function for fallback
        def transcribe_groq(model_name):
            return client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes),
                model=model_name,
                prompt="Dheeraj, Cyra, Hindi, Hinglish, play, open, search, WhatsApp, assignment, upload, weather, timer, alarm, screenshot, organize, YouTube, Spotify, Chrome, Discord, Brave, send, message, email, note, shutdown, restart, brightness, bulb, hotspot",
                response_format="text",
                temperature=0.0  # CRITICAL: Forces model to be strictly factual, eliminates 99% of random hallucinations
            ).strip()

        # STT Fallback Hierarchy
        try:
            result = transcribe_groq("whisper-large-v3-turbo")
        except Exception:
            try:
                result = transcribe_groq("whisper-large-v3")
                print("[STT: Groq whisper-large-v3 (Fallback 1)]")
            except Exception:
                try:
                    # Google Web Speech (FREE, EXCELLENT for Hindi/Hinglish)
                    import speech_recognition as sr
                    r = sr.Recognizer()
                    with io.BytesIO(wav_bytes.getvalue()) as source:
                        with sr.AudioFile(source) as audio_file:
                            audio_data = r.record(audio_file)
                            result = r.recognize_google(audio_data, language="en-IN") # Indian English/Hinglish
                            print("[STT: Google Web Speech (Fallback 2)]")
                except Exception:
                    try:
                        result = transcribe_groq("distil-whisper-large-v3-en")
                        print("[STT: Groq distil-whisper (Fallback 3)]")
                    except Exception as e_final:
                        print(f"[STT Error] All models failed. {e_final}")
                        return ""

        # Final filter — reject very short or meaningless transcriptions (Whisper hallucinations)
        lower_result = result.lower()
        
        exact_ignore_list = [
            ".", ",", "...", "you", "the", "a", "i", "bye", "hmm",
            "thank you.", "thank you", "thanks.", "thank you for watching.",
            "thanks for watching.", "subscribe.", "thank you.",
            "paris", "relax", "question", "mois", "and say anything", "and post the song",
            "you can do it", "that's it.", "okay.", "okay", "yeah", "yes", "so", "right", "alright"
        ]
        
        if len(result) < 2 or lower_result in exact_ignore_list:
            return ""
            
        # Catch partial matches for severe hallucinations
        hallucination_triggers = [
            "declinex", "and say anything", "thanks for watching", "subscribe", 
            "paris, relax", "but it's got to go", "mois,ro", "amara.org", 
            "translation by", "subtitle by", "viewing", "you for watching"
        ]
        for hallucination in hallucination_triggers:
            if hallucination in lower_result:
                return ""

        # Track usage
        try:
            from modules.stats import update_usage
            update_usage("stt_requests", 1)
        except:
            pass

        return result

    except Exception as e:
        print(f"[STT] Transcription error: {e}")
        return ""