import numpy as np
import sounddevice as sd
import threading
import time

class SoundAnalyzer:
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.last_loud_time = 0

    def start(self):
        self.running = True
        threading.Thread(target=self._monitor, daemon=True).start()

    def _monitor(self):
        def audio_callback(indata, frames, time_info, status):
            volume_norm = np.linalg.norm(indata) * 10
            if volume_norm > 15:  # Loud noise threshold
                current_time = time.time()
                if current_time - self.last_loud_time > 10:  # Don't spam
                    self.last_loud_time = current_time
                    self.callback("I heard a loud noise! Is everything okay, honey?")

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
