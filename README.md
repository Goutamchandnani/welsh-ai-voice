# Llais Cymraeg 🐉
### Open-Source Welsh Voice AI Stack

> Welsh Speech → STT → LLM → TTS → Welsh Speech

A fully local, developer-first Welsh language voice AI pipeline. No cloud lock-in. No per-minute billing. Just open-source models, running on your machine.

---

## Demo Pipeline

```
🎧 Welsh Audio
      ↓
 [faster-whisper]   ← Fine-tuned on 121hrs of Welsh (CV 25.0)
      ↓
  Welsh Text
      ↓
 [Llama 3.1 8B]    ← Welsh system prompt via Ollama
      ↓
  Welsh Response
      ↓
 [Kokoro ONNX]     ← Welsh TTS, ~1s latency on CPU
      ↓
🔊 Welsh Speech
```

**End-to-end latency (tested on Apple M-series, CPU only): ~5–6 seconds.**

---

## Project Status

| Phase | Status | Summary |
|---|---|---|
| **Phase 1 — Foundation** | ✅ Complete | 121hrs of Welsh CV 25.0 downloaded & verified |
| **Phase 2 — Speech-to-Text** | ✅ Complete | Whisper-small fine-tuned: WER 71.7% → 47.0% |
| **Phase 3 — Text-to-Speech** | ✅ Complete | Kokoro ONNX Welsh TTS (~1s latency) |
| **Phase 4 — Language Model** | ✅ Complete | Llama 3.1 8B via Ollama, Welsh system prompt |
| **Phase 5 — API Layer** | ✅ Complete | FastAPI REST API with 5 endpoints |

---

## Quick Start

### 1. Clone and set up environment
```bash
git clone https://github.com/Goutamchandnani/welsh-ai-voice.git
cd welsh-ai-voice
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Add your Mozilla Data Collective API key to .env
```

### 3. Download the Welsh dataset
```bash
python3 scripts/download_cv_welsh.py
```

### 4. Download model files

**STT — Convert your fine-tuned Whisper model:**
```bash
ct2-transformers-converter \
  --model Goutam261/whisper-small-cy-demo \
  --output_dir models/faster-whisper-small-cy \
  --copy_files tokenizer.json \
  --quantization float16
```

**TTS — Download Kokoro ONNX files:**
```bash
mkdir -p models/kokoro && cd models/kokoro
curl -L -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd ../..
```

**LLM — Install Ollama and pull Llama 3.1 8B:**
```bash
# Install from https://ollama.com
ollama pull llama3.1:8b
```

### 5. Start the API
```bash
# Terminal 1 — start Ollama
ollama serve

# Terminal 2 — start the API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Test the pipeline
```bash
# Health check
curl http://localhost:8000/health

# Text → Welsh speech (TTS only)
curl -X POST http://localhost:8000/synthesise \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "text=Bore da! Sut mae pethau heddiw?" \
  --output response.wav

# Welsh audio → Welsh spoken response (full pipeline)
curl -X POST http://localhost:8000/voice \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "audio=@your_clip.mp3;type=audio/mpeg" \
  --output response.wav
```

---

## API Reference

All endpoints live at `http://localhost:8000`. Full interactive docs at [`/docs`](http://localhost:8000/docs).

| Method | Endpoint | Input | Output |
|---|---|---|---|
| `GET` | `/health` | — | JSON status of all models |
| `POST` | `/v1/transcribe` | Audio file (MP3/WAV) | JSON with Welsh text |
| `POST` | `/synthesise` | Welsh text (form) | WAV audio file |
| `POST` | `/chat` | Welsh text (form) | WAV audio (LLM + TTS) |
| `POST` | `/voice` | Audio file (MP3/WAV) | WAV audio (full pipeline) |

### Response Headers (for `/voice` and `/chat`)
```
X-Transcription: Beth ydy Eisteddfod Genedlaethol Cymru?
X-LLM-Response:  Mae'r Eisteddfod yn ŵyl ddiwylliannol flynyddol...
X-Total-Latency: 5.328
```

---

## Reproduce the Results

### Dataset Exploration (Phase 1)
```bash
python3 scripts/explore_dataset.py   # 120.92 hours, 90,884 clips
python3 scripts/quality_check.py     # 20/20 random clips passed
```

### STT Baseline vs. Fine-tuned (Phase 2)
| Model | WER |
|---|---|
| `openai/whisper-small` (baseline) | 71.71% |
| `Goutam261/whisper-small-cy-demo` (500 steps) | 47.09% |

Training was done on Kaggle (GPU T4 x2) using 2,000 training clips from CV 25.0.

### TTS Test (Phase 3)
```bash
python3 scripts/synthesise_welsh.py
# Generates 3 Welsh audio samples in data/tts_output/
```

### Full Pipeline Test (Phase 4)
```bash
# Make sure Ollama is running first
python3 scripts/pipeline.py --text "Bore da! Beth yw dy enw di?"
```

---

## Tech Stack

| Component | Technology | Notes |
|---|---|---|
| STT | `faster-whisper` + `whisper-small-cy` | CTranslate2, int8 quantisation |
| LLM | `Llama 3.1 8B` via Ollama | Welsh system prompt |
| TTS | `Kokoro ONNX v1.0` | ~1s latency on CPU |
| API | `FastAPI` + `uvicorn` | REST + multipart audio upload |
| Training | Kaggle GPU T4 x2 | Hugging Face Trainer |
| Dataset | Mozilla Common Voice 25.0 (Welsh) | Via Mozilla Data Collective |

---

## Roadmap

- [x] Upgrade LLM to Llama 3.1 8B for better Welsh fluency
- [ ] Replace Kokoro with Coqui XTTS v2 for voice cloning (Python 3.11 venv)
- [ ] Add WebSocket streaming endpoint for real-time conversation
- [ ] Integrate with Vapi / LiveKit
- [ ] Retrain STT on full 121hr dataset for sub-20% WER
- [ ] Add n8n webhook support

---

## Repository Structure

```
welsh-ai-voice/
├── api/
│   └── main.py              # FastAPI app — all 5 endpoints
├── scripts/
│   ├── download_cv_welsh.py # Download CV 25.0 from Mozilla Data Collective
│   ├── explore_dataset.py   # Dataset stats (hours, demographics)
│   ├── quality_check.py     # Audio quality audit
│   ├── synthesise_welsh.py  # Kokoro TTS wrapper
│   ├── llm_welsh.py         # Ollama LLM wrapper (Welsh system prompt)
│   ├── pipeline.py          # End-to-end pipeline test script
│   └── test_faster_whisper.py # faster-whisper model test
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Contributing

This is an open-source project aiming to serve the Welsh-speaking community. Welsh NLP resources are scarce — contributions are very welcome.

**Good first issues:**
- Improve the Welsh system prompt for more natural LLM responses
- Add a `/stream` WebSocket endpoint
- Write a Welsh phoneme guide for better Kokoro pronunciation

---

## Licence

MIT — free to use, modify, and distribute.

---

*Built with ❤️ for the Welsh language. Cymru am byth! 🐉*

---

## Administration

### Generating API Keys
To issue a new API key for a developer, run the generator script:
```bash
python3 scripts/generate_key.py --email user@example.com --tier free --env live
```
This will output a secure `lc_live_xxxxx` key and store its SHA-256 hash in Supabase. We do not store raw keys.

