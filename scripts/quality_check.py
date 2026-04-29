"""
scripts/quality_check.py

Step 1.5 — Audio quality check and filtering.

What this does:
- Picks a random sample of 20 clips
- Loads them and checks sample rate, duration, and volume (RMS)
- Identifies any potentially 'broken' files
"""

import os
import random
import librosa
import numpy as np
import pandas as pd
from pathlib import Path

# Paths
BASE_PATH = Path("data/raw/common_voice/cv-corpus-25.0-2026-03-09/cy")
CLIPS_DIR = BASE_PATH / "clips"

def check_clip(clip_name):
    path = CLIPS_DIR / clip_name
    
    try:
        # Load audio (Whisper prefers 16kHz, but we load at native first)
        y, sr = librosa.load(path, sr=None)
        
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Calculate Root Mean Square (RMS) energy — basically 'loudness'
        rms = np.sqrt(np.mean(y**2))
        
        return {
            "clip": clip_name,
            "sr": sr,
            "duration": duration,
            "rms": rms,
            "status": "✅ OK" if rms > 0.005 else "⚠️ Too Quiet"
        }
    except Exception as e:
        return {"clip": clip_name, "status": f"❌ Error: {e}"}

def main():
    print("🎧 Performing Audio Quality Check on random samples...")
    
    # Load validated list
    validated = pd.read_csv(BASE_PATH / "validated.tsv", sep='\t', quoting=3)
    sample_clips = random.sample(list(validated['path']), 20)
    
    results = []
    for clip in sample_clips:
        res = check_clip(clip)
        results.append(res)
        print(f"  {res['clip']} -> {res['status']} ({res.get('duration', 0):.2f}s, {res.get('sr', 0)}Hz)")

    print("\n📊 Summary:")
    ok_count = sum(1 for r in results if r['status'] == "✅ OK")
    print(f"  Passed: {ok_count}/20")
    
    if ok_count == 20:
        print("\n✨ Audio quality looks great! No major issues found.")
    else:
        print("\n⚠️ Some clips might be too quiet or broken. We will filter these out in Phase 2.")

    print("\n🏁 Step 1.5 complete. Ready for Step 1.6 — Final Phase 1 README.")

if __name__ == "__main__":
    main()
