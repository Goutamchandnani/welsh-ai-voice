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
| **Phase 2 — Speech-to-Text** | 🔜 NEXT | Fine-tuning Whisper-small on Welsh. |
| Phase 3 — Text-to-Speech | 🔜 Pending | Coqui XTTS v2 voice cloning. |
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

## Next Up: Phase 2 — Speech to Text
We will move our work to a **Kaggle Notebook** with GPU access to fine-tune `whisper-small` on this 121-hour dataset.
