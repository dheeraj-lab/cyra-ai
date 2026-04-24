"""
Cyra TTS — Ultra-fast text-to-speech with edge-tts (free, natural).
Priority: edge-tts (fast + free) → kokoro (offline fallback)
"""

import sounddevice as sd
import soundfile as sf
import tempfile
import os
import asyncio
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# ==================== Edge TTS (Primary — Free, Fast, Natural) ====================

EDGE_VOICES = {
    "hindi": "en-IN-NeerjaNeural",      # Indian English reads Hinglish perfectly naturally
    "english": "en-US-AnaNeural",       # Female English — young, cute
}

EDGE_EMOTION_STYLES = {
    "neutral":   {"rate": "+0%", "pitch": "+0Hz"},
    "happy":     {"rate": "+8%", "pitch": "+15Hz"},
    "excited":   {"rate": "+15%", "pitch": "+25Hz"},
    "sad":       {"rate": "-10%", "pitch": "-10Hz"},
    "curious":   {"rate": "+5%", "pitch": "+10Hz"},
    "concerned": {"rate": "-5%", "pitch": "-5Hz"},
    "angry":     {"rate": "+10%", "pitch": "-15Hz"},
    "surprised": {"rate": "+12%", "pitch": "+30Hz"},
}

def _detect_language(text):
    """Detect if text is Hindi or English based on script."""
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total = len(text.strip())
    if total == 0:
        return "english"
    if hindi_chars / total > 0.3:
        return "hindi"
    return "english"

async def _edge_tts_generate(text, emotion="neutral"):
    """Generate speech using edge-tts — fast and free."""
    import edge_tts

    lang = _detect_language(text)
    voice = EDGE_VOICES.get(lang, EDGE_VOICES["english"])
    
    # If language is Hindi (which now uses the Indian English voice Neerja),
    # we can safely speed it up slightly so it doesn't sound like slow motion.
    if lang == "hindi":
        style = {"rate": "+15%", "pitch": "+0Hz"}
    else:
        style = EDGE_EMOTION_STYLES.get(emotion, EDGE_EMOTION_STYLES["neutral"])

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=style["rate"],
        pitch=style["pitch"]
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = tmp.name
    tmp.close()

    await communicate.save(tmp_path)
    return tmp_path

# Lazy-load kokoro to reduce startup time
_kokoro_pipeline = None
_kokoro_loaded = False

def _get_kokoro():
    global _kokoro_pipeline, _kokoro_loaded
    if not _kokoro_loaded:
        try:
            import kokoro as kokoro_lib
            _kokoro_pipeline = kokoro_lib.KPipeline(lang_code="a")
            print("[TTS] Kokoro loaded (offline fallback ready).")
        except:
            _kokoro_pipeline = None
        _kokoro_loaded = True
    return _kokoro_pipeline

KOKORO_VOICE_MAP = {
    "neutral":   ("af_bella", 1.0),
    "happy":     ("af_bella", 1.15),
    "excited":   ("af_bella", 1.2),
    "sad":       ("af_bella", 0.85),
    "curious":   ("af_bella", 1.1),
    "concerned": ("af_bella", 0.95),
    "angry":     ("af_bella", 1.1),
    "surprised": ("af_bella", 1.2),
}

# ==================== Audio Playback ====================

import threading as _tts_threading

_speaking = False
_speaking_lock = _tts_threading.Lock()
_interrupted = False

def is_speaking():
    """Check if Cyra is currently speaking (used by STT to avoid self-trigger)."""
    return _speaking

def get_cable_device():
    """Find VB-Cable virtual audio device for avatar lip sync."""
    try:
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if "CABLE Input" in d['name'] and d['max_output_channels'] > 0:
                return i
    except:
        pass
    return None

def stop_speaking():
    """Immediately stop any current audio playback."""
    global _speaking, _interrupted
    try:
        _interrupted = True
        sd.stop()
        _speaking = False
        print("[TTS] Interrupted!")
    except:
        pass

def play_audio(data, samplerate, on_playback_start=None):
    """Play audio — routes to CABLE if available for VSeeFace. Uses polling for instant interrupt."""
    global _speaking, _interrupted
    _interrupted = False
    cable = get_cable_device()
    try:
        with _speaking_lock:
            _speaking = True
            
        if on_playback_start:
            try:
                on_playback_start()
            except Exception as e:
                print(f"[TTS] Callback error: {e}")
                
        if cable is not None:
            sd.play(data, samplerate, device=cable)
        else:
            sd.play(data, samplerate)
        # Poll instead of sd.wait() so we can be interrupted instantly
        import time as _time
        # Calculate expected duration as safety timeout
        max_wait = len(data) / samplerate + 2.0  # audio length + 2s buffer
        start_t = _time.time()
        while (_time.time() - start_t) < max_wait:
            if _interrupted:
                sd.stop()
                break
            try:
                stream = sd.get_stream()
                if stream is None or not stream.active:
                    break
            except Exception:
                break
            _time.sleep(0.05)  # 50ms polling = near-instant interrupt
    except Exception as e:
        if not _interrupted:
            print(f"[TTS] Playback error: {e}")
    finally:
        _speaking = False
        _interrupted = False

# ==================== Main Speak Function ====================

def speak_elevenlabs(text, emotion, on_playback_start=None):
    """Speak using ElevenLabs — highest quality."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return False
        
    # Default to Rachel voice, or allow custom via env
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # Important for Hindi support
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            # Silencing terminal errors as requested by user
            return False
            
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()
        
        with open(tmp_path, "wb") as f:
            f.write(response.content)
            
        # Track usage
        try:
            from modules.stats import update_usage
            update_usage("elevenlabs_chars", len(text))
        except:
            pass

        data, samplerate = sf.read(tmp_path)
        play_audio(data, samplerate, on_playback_start)
        os.unlink(tmp_path)
        return True
    except Exception:
        # Silencing terminal errors as requested by user
        return False

def speak_edge(text, emotion, on_playback_start=None):
    """Speak using edge-tts — fast and free."""
    try:
        # Run async edge-tts from sync context
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(lambda: asyncio.run(_edge_tts_generate(text, emotion)))
                tmp_path = future.result(timeout=30)
        else:
            tmp_path = asyncio.run(_edge_tts_generate(text, emotion))

        data, samplerate = sf.read(tmp_path)
        play_audio(data, samplerate, on_playback_start)
        os.unlink(tmp_path)
        return True
    except Exception as e:
        print(f"[TTS] Edge-TTS failed: {e}")
        return False

def speak_kokoro(text, emotion, on_playback_start=None):
    """Speak using kokoro — offline fallback (lazy loaded)."""
    try:
        pipeline = _get_kokoro()
        if not pipeline:
            return False
        voice, speed = KOKORO_VOICE_MAP.get(emotion, ("af_bella", 1.0))
        generator = pipeline(
            text,
            voice=f"kokoro_model/voices/{voice}.pt",
            speed=speed
        )
        for _, _, audio in generator:
            play_audio(audio, 24000, on_playback_start)
            on_playback_start = None  # Only call it on the first chunk
        return True
    except Exception as e:
        print(f"[TTS] Kokoro failed: {e}")
        return False

def speak(text, emotion="neutral", on_playback_start=None):
    """Main speak function — tries ElevenLabs -> edge-tts -> kokoro."""
    if not text or not text.strip():
        return

    # Call the playback start callback immediately if it's the only way to show the message
    # if TTS fails later, the user at least sees the text.
    playback_triggered = False
    def trigger_callback():
        nonlocal playback_triggered
        if on_playback_start and not playback_triggered:
            on_playback_start()
            playback_triggered = True

    # 1. Try ElevenLabs first
    if os.getenv("ELEVENLABS_API_KEY"):
        success = speak_elevenlabs(text, emotion, on_playback_start=trigger_callback)
        if success:
            return

    # 2. Try edge-tts
    success = speak_edge(text, emotion, on_playback_start=trigger_callback)
    if success:
        return

    # 3. Fallback to kokoro
    speak_kokoro(text, emotion, on_playback_start=trigger_callback)
    
    # If all failed, still trigger the callback so text is shown
    trigger_callback()