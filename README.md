# Llais Cymraeg (Welsh Voice) 🐉

> Open-source, developer-first Welsh language voice AI stack.
> Welsh Speech → STT → LLM → TTS → Welsh Speech

---

## What This Is

**Llais Cymraeg** is a real-time voice pipeline that converts Welsh speech to text, generates a response, and speaks it back in natural Welsh. It's designed as a WebSocket + REST API that plugs into platforms like Vapi, LiveKit, and n8n.

---

## Current Project Status

| Phase | Status | Summary |
|---|---|---|
| **Phase 1 — Foundation** | ✅ COMPLETE | 121hrs of Welsh CV 25.0 downloaded & verified. |
| **Phase 2 — Speech-to-Text** | ✅ COMPLETE | Fine-tuned Whisper-small on Welsh & optimised to faster-whisper. |
| Phase 3 — Text-to-Speech | 🔜 NEXT | Coqui XTTS v2 voice cloning. |
| Phase 4 — Language Model | 🔜 Pending | Llama 3.1 8B with Welsh LoRA. |
| Phase 5 — API Layer | 🔜 Pending | FastAPI & WebSocket streaming. |

---

## Phase 1 — Foundation (Completed)

### 📊 Dataset: Mozilla Common Voice 25.0 (Welsh)
- **Total Validated Audio:** 120.92 hours
- **Total Clips:** 90,884
- **Language:** Welsh (cy)
- **Source:** Mozilla Data Collective (MDC)

### 👥 Demographics
- **Gender:** 33% Male, 26% Female (balanced representation).
- **Age:** Diverse coverage from Teens to 80s, with a peak in 20s-40s.
- **Quality:** 100% of random samples passed RMS volume and technical integrity checks.

### 🛠️ Reproduction Steps

1. **Environment Setup:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Download Data:**
   Add `MDC_API_KEY` to your `.env` file, then:
   ```bash
   python3 scripts/download_cv_welsh.py
   ```

3. **Explore Data:**
   ```bash
   python3 scripts/explore_dataset.py
   python3 scripts/quality_check.py
   ```

---

## Phase 2 — Speech to Text (Completed)

We fine-tuned `openai/whisper-small` on our Welsh dataset.
- **Baseline WER:** 71.71%
- **Fine-tuned WER:** 47.09% (after just 500 steps!)
- **Optimisation:** Converted to `faster-whisper` (CTranslate2) format with `int8` quantization for real-time CPU inference on Apple Silicon. Latency is ~1.2s for a 3s clip.

### 🛠️ Reproduction Steps
```bash
# Convert Hugging Face model to faster-whisper format
ct2-transformers-converter --model Goutam261/whisper-small-cy-demo --output_dir models/faster-whisper-small-cy --copy_files tokenizer.json --quantization float16

# Test the optimized model
python3 scripts/test_faster_whisper.py
```

---

## Next Up: Phase 3 — Text-to-Speech
We will use Coqui XTTS v2 to clone a natural-sounding Welsh voice.
