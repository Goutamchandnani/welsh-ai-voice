# Llais Cymraeg — Project Plan
> Open Source Welsh Language Voice AI — Developer-First, Agent-Ready

---

## Vision

Build the world's first fully open source, developer-first Welsh language voice AI stack that any developer can plug into any voice agent platform (Vapi, LiveKit, Twilio, n8n, Bland AI) with a single API call.

This is not a consumer app. This is infrastructure — the missing building block for Welsh language AI.

---

## The Problem We Are Solving

- Welsh has ~900,000 speakers but is severely underrepresented in voice AI
- Existing tools (Macsen, ElevenLabs, PiperTTS) are either consumer apps or closed/paid
- No open source, self-hostable, real-time Welsh voice API exists that developers can integrate
- Welsh speakers are second-class citizens in the voice AI era

---

## The Solution

A unified, open source pipeline:

```
Welsh Speech → STT → LLM → TTS → Welsh Speech
```

Packaged as a clean WebSocket + REST API that plugs into any voice agent platform.

---

## Phases

### Phase 1 — Foundation (Weeks 1–2)
- [ ] Set up GitHub repo and project structure
- [ ] Download and explore Mozilla Common Voice Welsh (CV 25.0)
- [ ] Clean and preprocess audio data
- [ ] Baseline Whisper evaluation on Welsh (before fine-tuning)
- [ ] Document findings in README

### Phase 2 — Speech-to-Text (Weeks 3–4)
- [ ] Fine-tune `whisper-small` on validated Welsh CV data (90,884 clips)
- [ ] Evaluate Word Error Rate (WER) on test split
- [ ] Optimise with `faster-whisper` for real-time streaming
- [ ] Add Silero VAD for voice activity detection
- [ ] Push model weights to Hugging Face Hub
- [ ] Document every step in README with explanations

### Phase 3 — Text-to-Speech (Weeks 5–6)
- [ ] Set up Coqui XTTS v2 with Welsh language support
- [ ] Clone Welsh voice from clean speaker sample (BBC Cymru / S4C quality)
- [ ] Fine-tune prosody on Welsh rhythm and stress patterns
- [ ] Add post-processing pipeline (pedalboard — EQ, compression, warmth)
- [ ] Implement multi-speaker support (North + South Welsh voices)
- [ ] Evaluate naturalness and publish audio samples
- [ ] Document every step in README with explanations

### Phase 4 — Language Model (Weeks 7–8)
- [ ] Set up Llama 3.1 8B with Welsh LoRA adapter
- [ ] Connect ChromaDB for conversation memory
- [ ] Test Welsh language understanding and generation quality
- [ ] Document every step in README with explanations

### Phase 5 — API Layer (Weeks 9–10)
- [ ] Build FastAPI gateway with WebSocket streaming
- [ ] Add REST endpoints for batch processing
- [ ] Add Redis queue for concurrent requests
- [ ] Containerise with Docker
- [ ] Deploy free tier on Modal.com
- [ ] Write integration guides for Vapi, LiveKit, n8n, Twilio

### Phase 6 — Launch (Weeks 11–12)
- [ ] Full documentation on README
- [ ] Demo on Hugging Face Spaces
- [ ] Post on Welsh tech communities, GitHub, Reddit
- [ ] Apply for Welsh Government digital grants
- [ ] Open contributions from community

---

## Success Metrics

| Metric | Target |
|---|---|
| Word Error Rate (STT) | < 15% on Welsh test set |
| TTS naturalness | Indistinguishable from human in blind test |
| API latency | < 500ms first token |
| Integration time | < 30 minutes for a developer to plug in |
| GitHub stars | 100+ in first month |

---

## Guiding Principles

1. **Open source everything** — weights, code, data pipelines, docs
2. **Developer first** — API is the product, not the app
3. **Explain everything** — every step documented in plain English AND Welsh
4. **Free to run** — no paid dependencies in the core stack
5. **Community owned** — built with and for Welsh speakers

---

## Team / Roles Needed

| Role | Status |
|---|---|
| ML Engineer (STT/TTS) | Founder |
| Welsh Language Advisor | Needed |
| Backend Engineer (API) | Needed |
| Community Manager | Needed |
| Partnership (Bangor / S4C) | Outreach needed |
