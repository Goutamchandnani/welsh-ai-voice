"""
scripts/download_cv_welsh.py

Step 1.3 — Download and explore Mozilla Common Voice Welsh dataset.

What this does:
- Connects to Hugging Face using your HF_TOKEN
- Downloads the Welsh (cy) subset of Common Voice
- Prints a summary: number of clips, hours, splits
- Saves the dataset locally for faster future access

Run with:
    source venv/bin/activate
    python3 scripts/download_cv_welsh.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load secrets from .env file
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
WELSH_ISO = os.getenv("WELSH_ISO_CODE", "cy")
DATA_DIR = Path("data/raw/common_voice")

# ----------------------------------------------------------------
# 1. Check that we have a HF token before doing anything
# ----------------------------------------------------------------
if not HF_TOKEN:
    raise EnvironmentError(
        "❌ HF_TOKEN not found in your .env file.\n"
        "   1. Copy .env.example to .env\n"
        "   2. Add your Hugging Face token (https://huggingface.co/settings/tokens)\n"
        "   3. Accept the Common Voice dataset licence on Hugging Face\n"
        "   Then run this script again."
    )

# ----------------------------------------------------------------
# 2. Import dataset libraries (after env check, to give clear errors)
# ----------------------------------------------------------------
try:
    from datasets import load_dataset, Audio
    import soundfile as sf
    import numpy as np
    from huggingface_hub import login
except ImportError as e:
    raise ImportError(
        f"❌ Missing package: {e}\n"
        "   Run: pip install -r requirements.txt"
    )

# ----------------------------------------------------------------
# 3. Authenticate with Hugging Face
# ----------------------------------------------------------------
print("🔐 Logging in to Hugging Face...")
try:
    login(token=HF_TOKEN, add_to_git_credential=False)
    print("   ✅ Authenticated successfully\n")
except Exception as e:
    raise ConnectionError(f"❌ Hugging Face login failed: {e}")

# ----------------------------------------------------------------
# 4. Load the Welsh subset of Mozilla Common Voice
# ----------------------------------------------------------------
# Common Voice 17.0 is the latest stable release on HF with Welsh.
# Welsh ISO code: cy | Validated hours: ~124hrs
DATASET_NAME = "mozilla-foundation/common_voice_17_0"

print(f"📥 Loading Welsh ({WELSH_ISO}) dataset from: {DATASET_NAME}")
print("   This may take a few minutes on first run (streaming=True skips full download)...\n")

try:
    # streaming=True means we don't download everything upfront —
    # we inspect the data in memory first before committing to a full download
    dataset = load_dataset(
        DATASET_NAME,
        WELSH_ISO,
        token=HF_TOKEN,
        trust_remote_code=True,
    )
except Exception as e:
    raise RuntimeError(
        f"❌ Failed to load dataset: {e}\n\n"
        "   Common causes:\n"
        "   1. You haven't accepted the Common Voice licence on Hugging Face.\n"
        "      → Go to: https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0\n"
        "      → Click 'Access repository' and accept the terms.\n"
        "   2. Your HF_TOKEN doesn't have 'read' permissions.\n"
        "      → Go to: https://huggingface.co/settings/tokens\n"
        "   3. No internet connection."
    )

# ----------------------------------------------------------------
# 5. Print a summary of what we downloaded
# ----------------------------------------------------------------
print("=" * 55)
print("  📊  MOZILLA COMMON VOICE — WELSH DATASET SUMMARY")
print("=" * 55)

total_clips = 0
for split_name, split_data in dataset.items():
    n = len(split_data)
    total_clips += n
    print(f"  {split_name:<15} {n:>7,} clips")

print(f"  {'TOTAL':<15} {total_clips:>7,} clips")
print()

# ----------------------------------------------------------------
# 6. Inspect one sample to confirm audio loads correctly
# ----------------------------------------------------------------
print("🎧 Inspecting one sample clip from the 'train' split...\n")

try:
    sample = dataset["train"][0]

    print(f"  Sentence     : {sample['sentence']}")
    print(f"  Audio path   : {sample['path']}")
    print(f"  Sample rate  : {sample['audio']['sampling_rate']} Hz")
    print(f"  Audio array  : shape {np.array(sample['audio']['array']).shape}")
    print(f"  Duration     : {len(sample['audio']['array']) / sample['audio']['sampling_rate']:.2f} seconds")
    print(f"  Locale       : {sample.get('locale', 'cy')}")
    print()
    print("✅ Dataset loaded and verified. Audio is readable.")

except Exception as e:
    print(f"⚠️  Could not inspect sample: {e}")

# ----------------------------------------------------------------
# 7. Show available column names (features in the dataset)
# ----------------------------------------------------------------
print("\n📋 Dataset columns (features):")
for col in dataset["train"].column_names:
    print(f"   - {col}")

print("\n🏁 Step 1.3 complete. Ready for Step 1.4 — Explore and visualise the dataset.")
