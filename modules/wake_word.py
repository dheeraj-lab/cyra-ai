import pvporcupine
import pvrecorder
from dotenv import load_dotenv
import os

load_dotenv()

PICOVOICE_KEY = os.getenv("PICOVOICE_KEY")

def wait_for_wake_word():
    porcupine = pvporcupine.create(
        access_key=PICOVOICE_KEY,
        keywords=["hey siri"],
        sensitivities=[0.7]
    )

    recorder = pvrecorder.PvRecorder(
        frame_length=porcupine.frame_length,
        device_index=-1
    )

    print("Sleeping... say 'Hey Cyra' to wake me up!")
    recorder.start()

    try:
        while True:
            pcm = recorder.read()
            result = porcupine.process(pcm)
            if result >= 0:
                print("Wake word detected!")
                break
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()