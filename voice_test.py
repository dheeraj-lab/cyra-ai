from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import sounddevice as sd
import soundfile as sf
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

test_text = "Aree yaar, kya haal hai! Main bilkul theek hoon. How are you doing today? Chal kuch mast karte hain!"

voices = [
    ("21m00Tcm4TlvDq8ikWAM", "Rachel"),
    ("AZnzlk1XvdvUeBnXmlld", "Domi"),
    ("EXAVITQu4vr4xnSDxMaL", "Bella"),
    ("ErXwobaYiN019PkySvjV", "Antoni"),
    ("MF3mGyEYCl7XYWbV9V6O", "Elli"),
    ("TxGEqnHWrfWFTfGW9XjX", "Josh"),
    ("VR6AewLTigWG4xSOukaG", "Arnold"),
    ("pNInz6obpgDQGcFmaJgB", "Adam"),
    ("yoZ06aMxZJJ28mfd3POQ", "Sam"),
]

for voice_id, name in voices:
    print(f"\nVoice: {name}")
    input("Press Enter to hear...")
    try:
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=test_text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()
        with open(tmp_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        data, sr = sf.read(tmp_path)
        sd.play(data, sr)
        sd.wait()
        os.unlink(tmp_path)
    except Exception as e:
        print(f"Error: {e}")

print("\nKaun si voice best lagi?")