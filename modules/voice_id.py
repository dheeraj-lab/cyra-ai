import numpy as np
import os
import scipy.io.wavfile as wav
from scipy.fftpack import fft

USER_PROFILE_PATH = "modules/user_voice_profile.npy"

def extract_features(audio_data, sample_rate=16000):
    """Fast feature extraction (Pitch and Spectral features)."""
    # Simple Pitch (F0) estimation using Autocorrelation
    corr = np.correlate(audio_data, audio_data, mode='full')
    corr = corr[len(corr)//2:]
    
    # Find the first peak
    d = np.diff(corr)
    start = np.where(d > 0)[0]
    if len(start) == 0: return None
    peak = np.argmax(corr[start[0]:]) + start[0]
    pitch = sample_rate / peak if peak > 0 else 0
    
    # Spectral Centroid
    spectrum = np.abs(fft(audio_data))
    freqs = np.linspace(0, sample_rate, len(spectrum))
    centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
    
    return np.array([pitch, centroid])

def save_user_profile(audio_data):
    """Save user voice features."""
    features = extract_features(audio_data)
    if features is not None:
        np.save(USER_PROFILE_PATH, features)
        print("[VoiceID] Fast profile saved.")
        return True
    return False

def verify_user(audio_data, threshold=0.3):
    """Verify speaker using fast feature comparison."""
    if not os.path.exists(USER_PROFILE_PATH):
        return True
    
    user_features = np.load(USER_PROFILE_PATH)
    current_features = extract_features(audio_data)
    
    if current_features is None:
        return True

    # Normalize and compare
    diff = np.abs(user_features - current_features) / user_features
    error = np.mean(diff)
    
    print(f"[VoiceID] Voice error: {error:.4f}")
    return error < threshold
