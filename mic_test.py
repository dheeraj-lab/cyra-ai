import sounddevice as sd
import numpy as np

print("Bol 'Kya haal hai Cyra' — 5 seconds...")
recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()
volume = np.abs(recording).mean()
max_vol = np.abs(recording).max()
print(f"Average volume: {volume:.4f}")
print(f"Max volume: {max_vol:.4f}")

if volume < 0.01:
    print("Microphone bahut quiet hai — paas jaake bolo ya mic check karo!")
elif volume > 0.3:
    print("Microphone bahut loud hai!")
else:
    print("Microphone theek hai!")