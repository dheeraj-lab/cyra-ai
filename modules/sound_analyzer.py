import numpy as np
import sounddevice as sd
import threading
import time

class SoundAnalyzer:
    def __init__(self, speak_func):
        self.speak_func = speak_func
        self.running = False
        self.last_loud_time = 0
        self.last_alert_time = 0
        self._enabled = True
        
    def start(self):
        self.running = True
        threading.Thread(target=self._monitor, daemon=True).start()

    def pause(self):
        """Pause monitoring (e.g., while Cyra is speaking)."""
        self._enabled = False

    def resume(self):
        """Resume monitoring after speaking."""
        self._enabled = True

    def _monitor(self):
        # Track a rolling history of volume levels to detect REAL loud events
        volume_history = []
        HISTORY_SIZE = 30  # ~3 seconds of baseline
        
        def audio_callback(indata, frames, time_info, status):
            if not self._enabled:
                return
                
            # Check if TTS is currently playing — ignore those sounds
            try:
                from modules.tts import is_speaking
                if is_speaking():
                    return
            except:
                pass
            
            volume_norm = np.linalg.norm(indata) * 10
            
            # Build baseline of normal ambient noise
            volume_history.append(volume_norm)
            if len(volume_history) > HISTORY_SIZE:
                volume_history.pop(0)
            
            # Need enough history before we can judge
            if len(volume_history) < 10:
                return
            
            # Calculate dynamic threshold based on ambient noise
            baseline = np.mean(volume_history[:-1])  # Exclude current reading
            dynamic_threshold = max(25, baseline * 3.0)  # At least 25, or 3x ambient
            
            current_time = time.time()
            
            # Only alert for TRULY loud, sustained events
            if volume_norm > dynamic_threshold and volume_norm > 30:
                if current_time - self.last_alert_time > 60:  # Max once per minute
                    self.last_alert_time = current_time
                    # Use a thread to avoid blocking the audio callback
                    threading.Thread(
                        target=self.speak_func, 
                        args=("Whoa! That was loud! Is everything okay, honey?", "surprised"),
                        daemon=True
                    ).start()

        with sd.InputStream(callback=audio_callback):
            while self.running:
                time.sleep(1)

_analyzer = None
def start_sound_monitoring(speak_func):
    global _analyzer
    if _analyzer is None:
        _analyzer = SoundAnalyzer(speak_func)
        _analyzer.start()
        print("[Sound] Monitoring started.")
