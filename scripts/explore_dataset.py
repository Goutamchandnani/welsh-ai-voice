"""
scripts/explore_dataset.py

Step 1.4 — Analyze the Welsh Common Voice 25.0 dataset.

What this does:
- Parses the .tsv metadata files
- Calculates total duration of the dataset
- Summarises speaker demographics (gender, age, accent)
- Visualises the data distribution
"""

import pandas as pd
from pathlib import Path

# Path to the Welsh dataset
BASE_PATH = Path("data/raw/common_voice/cv-corpus-25.0-2026-03-09/cy")

def load_tsv(filename):
    return pd.read_csv(BASE_PATH / filename, sep='\t', quoting=3, low_memory=False)

def main():
    print("📊 Analysing Welsh Common Voice Dataset...")
    
    # 1. Load basic stats
    validated = load_tsv("validated.tsv")
    durations = load_tsv("clip_durations.tsv")
    
    # Merge to get durations for validated clips
    # clip_durations.tsv columns are usually 'clip' and 'duration'
    stats = pd.merge(validated, durations, left_on='path', right_on='clip')
    
    total_clips = len(stats)
    total_seconds = stats['duration[ms]'].sum() / 1000 if 'duration[ms]' in stats.columns else stats['duration'].sum() / 1000
    total_hours = total_seconds / 3600

    print("-" * 40)
    print(f"✅ Validated Clips : {total_clips:,}")
    print(f"⏳ Total Duration  : {total_hours:.2f} hours")
    print("-" * 40)

    # 2. Demographic breakdown
    print("\n👥 Speaker Demographics (where provided):")
    
    for col in ['gender', 'age', 'accent']:
        if col in stats.columns:
            print(f"\n--- {col.capitalize()} ---")
            counts = stats[col].value_counts(dropna=True)
            for val, count in counts.items():
                percentage = (count / total_clips) * 100
                print(f"  {val:<15}: {count:>6,} ({percentage:>4.1f}%)")

    # 3. Data Splits Summary
    print("\n📦 Data Splits Summary:")
    for split in ['train.tsv', 'test.tsv', 'dev.tsv']:
        df = load_tsv(split)
        print(f"  {split:<12}: {len(df):>6,} clips")

    print("\n🏁 Step 1.4 complete. Ready for Step 1.5 — Audio quality check.")

if __name__ == "__main__":
    main()
