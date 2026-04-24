"""
Wake Word Detection — Listens for "Cyra" / "Hey Cyra" using VAD + Whisper.
No Porcupine needed. Works with any custom wake word.
"""

import numpy as np
import sounddevice as sd
import torch
import io
import wave
import time
import os
import groq
from dotenv import load_dotenv

load_dotenv()

client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load Silero VAD (uses cache — fast)
_vad_model, _utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)

SAMPLE_RATE = 16000
CHUNK_SIZE = 512
WAKE_WORDS = ["cyra", "hey cyra", "hi cyra", "okay cyra", "syra", "saira", "sira"]

def wait_for_wake_word():
    """Listen continuously until 'Cyra' is detected."""
    print("Sleeping... say 'Hey Cyra' to wake me up!")
    
    while True:
        try:
            audio = _listen_for_speech()
            if audio is None:
                continue
            
            text = _quick_transcribe(audio)
            if not text:
                continue
            
            text_lower = text.lower().strip()
            
            # Check if any wake word variant is in the transcription
            for wake in WAKE_WORDS:
                if wake in text_lower:
                    print(f"Wake word detected! (heard: '{text}')")
                    return
                    
        except Exception as e:
            time.sleep(0.5)

def _listen_for_speech():
    """Use VAD to detect speech onset and record 1.5s of audio."""
    speech_chunks = []
    speech_detected = False
    silence_start = 0
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        for _ in range(int(SAMPLE_RATE / CHUNK_SIZE * 10)):  # Max 10s listening window
            chunk, _ = stream.read(CHUNK_SIZE)
            chunk = chunk.flatten()
            
            # Check if TTS is playing — skip to avoid self-trigger
            try:
                from modules.tts import is_speaking
                if is_speaking():
                    speech_detected = False
                    speech_chunks = []
                    continue
            except:
                pass
            
            tensor = torch.from_numpy(chunk)
            prob = _vad_model(tensor, SAMPLE_RATE).item()
            rms = np.sqrt(np.mean(chunk**2))
            
            if prob > 0.6 and rms > 0.02:
                speech_chunks.append(chunk)
                speech_detected = True
                silence_start = 0
            elif speech_detected:
                speech_chunks.append(chunk)
                if silence_start == 0:
                    silence_start = time.time()
                elif time.time() - silence_start > 0.4:  # Short silence = end of wake phrase
                    break
    
    if not speech_chunks or len(speech_chunks) < 3:
        return None
    
    return np.concatenate(speech_chunks)

def _quick_transcribe(audio):
    """Fast transcription using Groq Whisper."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    buf.seek(0)
    
    try:
        result = client.audio.transcriptions.create(
            file=("wake.wav", buf),
            model="whisper-large-v3-turbo",
            prompt="Cyra, Hey Cyra",
            response_format="text",
            temperature=0.0
        ).strip()
        return result
    except:
        return ""