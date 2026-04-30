"""
scripts/pipeline.py

Phase 4.4 — The Full Welsh Voice AI Pipeline (Walking Skeleton).

This script wires together all three components:
  1. STT: faster-whisper  (Welsh speech → text)
  2. LLM: Ollama Llama 3.2 (Welsh text → Welsh response)
  3. TTS: Kokoro ONNX     (Welsh response → Welsh speech)

Usage:
    python3 scripts/pipeline.py --audio path/to/audio.mp3
    python3 scripts/pipeline.py --text "Bore da, sut wyt ti?"
"""

import argparse
import time
import soundfile as sf
from pathlib import Path
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
from llm_welsh import respond

# Paths
STT_MODEL = "models/faster-whisper-small-cy"
KOKORO_MODEL = "models/kokoro/kokoro-v1.0.onnx"
KOKORO_VOICES = "models/kokoro/voices-v1.0.bin"
OUTPUT_DIR = Path("data/pipeline_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_pipeline(audio_path: str = None, text_input: str = None):
    print("\n" + "=" * 55)
    print("🐉 Llais Cymraeg — Full Pipeline Test")
    print("=" * 55)

    total_start = time.time()

    # ── STEP 1: Speech-to-Text ──────────────────────────────
    if audio_path:
        print(f"\n[1/3] 🎧 STT: Transcribing {audio_path}...")
        t0 = time.time()
        stt_model = WhisperModel(STT_MODEL, device="cpu", compute_type="int8")
        segments, _ = stt_model.transcribe(audio_path, language="cy", beam_size=5)
        transcription = " ".join(s.text for s in segments).strip()
        stt_latency = time.time() - t0
        print(f"   Transcription: \"{transcription}\"")
        print(f"   ⏱  STT latency: {stt_latency:.2f}s")
    else:
        transcription = text_input
        print(f"\n[1/3] 💬 Input text (skipping STT): \"{transcription}\"")
        stt_latency = 0

    # ── STEP 2: Language Model ──────────────────────────────
    print(f"\n[2/3] 🧠 LLM: Generating Welsh response...")
    t0 = time.time()
    llm_response = respond(transcription, verbose=True)
    llm_latency = time.time() - t0
    print(f"   ⏱  LLM latency: {llm_latency:.2f}s")

    # ── STEP 3: Text-to-Speech ──────────────────────────────
    print(f"\n[3/3] 🗣️  TTS: Synthesising Welsh speech...")
    t0 = time.time()
    kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
    samples, sample_rate = kokoro.create(llm_response, voice="af_heart", speed=0.9, lang="cy")
    output_file = OUTPUT_DIR / f"response_{int(time.time())}.wav"
    sf.write(str(output_file), samples, sample_rate)
    tts_latency = time.time() - t0
    print(f"   Saved to: {output_file}")
    print(f"   ⏱  TTS latency: {tts_latency:.2f}s")

    # ── SUMMARY ──────────────────────────────────────────────
    total_latency = time.time() - total_start
    print("\n" + "=" * 55)
    print("📊 Pipeline Summary")
    print("=" * 55)
    print(f"  Input      : \"{transcription}\"")
    print(f"  Response   : \"{llm_response}\"")
    print(f"  Output WAV : {output_file}")
    print(f"  STT        : {stt_latency:.2f}s")
    print(f"  LLM        : {llm_latency:.2f}s")
    print(f"  TTS        : {tts_latency:.2f}s")
    print(f"  ─────────────────────")
    print(f"  TOTAL      : {total_latency:.2f}s")
    print("=" * 55)
    print(f"\n🎧 Open the response: open \"{output_file}\"")

    return str(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Welsh Voice AI Pipeline")
    parser.add_argument("--audio", help="Path to input audio file")
    parser.add_argument("--text",  help="Welsh text input (skips STT)")
    args = parser.parse_args()

    if not args.audio and not args.text:
        # Default test with text input
        run_pipeline(text_input="Bore da! Beth yw dy enw di?")
    elif args.audio:
        run_pipeline(audio_path=args.audio)
    else:
        run_pipeline(text_input=args.text)
