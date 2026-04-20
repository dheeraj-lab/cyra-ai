import torch
print("CUDA available:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")

import ollama
models = ollama.list()
print("Ollama models:", [m.model for m in models.models])

import chromadb
print("ChromaDB OK")

from faster_whisper import WhisperModel
print("Faster-Whisper OK")

import kokoro_onnx
print("Kokoro TTS OK")

import sounddevice
print("Sounddevice OK")

print("\nAll good! Ready to build Cyra!")