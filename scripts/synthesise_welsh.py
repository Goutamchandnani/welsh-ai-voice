"""
scripts/synthesise_welsh.py

Phase 3 — Welsh Text-to-Speech using Kokoro ONNX.

This is our core TTS function that will be called by the API in Phase 5.
It takes Welsh text and returns a WAV file.

Usage:
    python3 scripts/synthesise_welsh.py
"""

import time
import soundfile as sf
from pathlib import Path
from kokoro_onnx import Kokoro

# Output directory
OUTPUT_DIR = Path("data/tts_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def synthesise(text: str, output_path: str, voice: str = "af_heart", speed: float = 0.9) -> float:
    """
    Convert Welsh text to speech using Kokoro ONNX.

    Args:
        text:        The Welsh text to speak.
        output_path: Where to save the output WAV file.
        voice:       Kokoro voice ID. 'af_heart' is a natural, warm female voice.
        speed:       Speaking speed (0.8 = slightly slower, good for Welsh clarity).

    Returns:
        Latency in seconds.
    """
    print(f"🗣️  Initialising Kokoro TTS...")
    kokoro = Kokoro("models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin")

    print(f"📝 Synthesising: '{text}'")
    start = time.time()

    # Generate the audio samples
    samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang="cy")

    # Save the output WAV
    sf.write(output_path, samples, sample_rate)

    latency = time.time() - start
    print(f"✅ Saved to: {output_path}")
    print(f"⚡ Synthesis time: {latency:.2f}s")
    return latency


if __name__ == "__main__":
    # Test with a few real Welsh sentences
    test_sentences = [
        "Bore da. Sut mae pethau heddiw?",          # Good morning. How are things today?
        "Ydych chi eisiau te neu goffi?",            # Do you want tea or coffee?
        "Mae'r tywydd yn braf yng Nghymru heddiw.", # The weather is lovely in Wales today.
    ]

    print("=" * 50)
    print("🐉 Llais Cymraeg — Phase 3 TTS Test")
    print("=" * 50)

    for i, sentence in enumerate(test_sentences):
        output_file = OUTPUT_DIR / f"test_output_{i+1}.wav"
        latency = synthesise(sentence, str(output_file))
        print(f"   Output {i+1}: {output_file} ({latency:.2f}s)\n")

    print("=" * 50)
    print(f"🏁 Phase 3 TTS test complete. Check '{OUTPUT_DIR}/' for the audio files.")
    print("   Open them in QuickTime Player to hear the Welsh voice!")
