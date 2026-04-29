"""
scripts/download_cv_welsh.py

Step 1.3 — Download and Extract Mozilla Common Voice Welsh 25.0 (MDC).

What this does:
- Requests a presigned download URL from Mozilla Data Collective
- Downloads the .tar.gz archive
- Extracts it to data/raw/common_voice/

Dataset ID: cmn2g9w1h01m6mm07lq2w14dd
"""

import os
import requests
import tarfile
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# Load secrets from .env file
load_dotenv()

MDC_API_KEY = os.getenv("MDC_API_KEY")
# The exact ID provided by the user
MDC_DATASET_ID = "cmn2g9w1h01m6mm07lq2w14dd"
RAW_DIR = Path("data/raw/common_voice")
ARCHIVE_PATH = RAW_DIR / "cv_welsh_25.tar.gz"

def download_file(url, destination):
    """Download a file with a progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as f, tqdm(
        desc=destination.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            bar.update(size)

def main():
    if not MDC_API_KEY:
        print("❌ Error: MDC_API_KEY not found in .env file.")
        return

    # 1. Create directory
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Get Presigned URL
    print(f"🔗 Requesting download URL for dataset: {MDC_DATASET_ID}...")
    api_url = f"https://mozilladatacollective.com/api/datasets/{MDC_DATASET_ID}/download"
    headers = {
        "Authorization": f"Bearer {MDC_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        download_url = data.get("downloadUrl")
        
        if not download_url:
            print("❌ Error: API response did not contain a downloadUrl.")
            print(f"Response: {data}")
            return

        # 3. Download the archive
        print("🚀 Starting download...")
        download_file(download_url, ARCHIVE_PATH)

        # 4. Extract the archive
        print(f"📦 Extracting {ARCHIVE_PATH.name}...")
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            tar.extractall(path=RAW_DIR)
        
        print(f"\n✅ Success! Dataset extracted to: {RAW_DIR}")
        
        # Cleanup archive to save space
        ARCHIVE_PATH.unlink()
        print(f"🧹 Cleaned up {ARCHIVE_PATH.name}")
        
        print("\n🏁 Step 1.3 complete. Ready for Step 1.4 — Explore the dataset.")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 401:
            print("   Hint: Your API Key might be invalid or expired.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
