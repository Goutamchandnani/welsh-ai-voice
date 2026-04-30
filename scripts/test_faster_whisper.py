"""
scripts/test_faster_whisper.py

Step 2.6 — Test the optimized faster-whisper model.
"""

from faster_whisper import WhisperModel
import time
import os

# Path to the converted model
MODEL_PATH = "models/faster-whisper-small-cy"

# Find a Welsh audio clip from the dataset to test
CLIPS_DIR = "data/raw/common_voice/cv-corpus-25.0-2026-03-09/cy/clips"
try:
    test_audio = next(f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp3"))
    test_audio_path = os.path.join(CLIPS_DIR, test_audio)
except (FileNotFoundError, StopIteration):
    print(f"❌ Could not find an audio file in {CLIPS_DIR}. Make sure the dataset is extracted.")
    exit(1)

print(f"🤖 Loading optimized model from {MODEL_PATH}...")
# CPU is standard for Macs, compute_type="float16" uses less memory, "int8" is faster
model = WhisperModel(MODEL_PATH, device="cpu", compute_type="int8")

print(f"🎧 Transcribing {test_audio}...")
start_time = time.time()

# Transcribe
segments, info = model.transcribe(test_audio_path, language="cy", beam_size=5)

print(f"\n✅ Language detected: {info.language} (probability: {info.language_probability:.2f})")

print("\n📝 Transcription:")
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

latency = time.time() - start_time
print(f"\n⚡ Total processing time: {latency:.2f} seconds")
print("🏁 Step 2.6 complete.")
