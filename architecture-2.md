# Llais Cymraeg — Architecture
> Technical blueprint for the Welsh Voice AI stack

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                        │
│     Web App / Mobile / Phone / Voice Agent Platform     │
│         (Vapi, LiveKit, Twilio, n8n, Bland AI)          │
└────────────────────────┬────────────────────────────────┘
                         │ WebSocket / REST
┌────────────────────────▼────────────────────────────────┐
│                   FASTAPI GATEWAY                       │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │    Auth     │  │ Rate Limiter │  │  WS Handler  │  │
│   └─────────────┘  └──────────────┘  └──────────────┘  │
└───────────┬─────────────────┬──────────────┬────────────┘
            │                 │              │
┌───────────▼──┐  ┌───────────▼──┐  ┌───────▼──────────┐
│  STT ENGINE  │  │  LLM ENGINE  │  │   TTS ENGINE     │
│              │  │              │  │                  │
│ faster-      │  │ Llama 3.1 8B │  │ Coqui XTTS v2   │
│ whisper (cy) │  │ + Welsh LoRA │  │ + pedalboard     │
│ silero-vad   │  │ + ChromaDB   │  │ post-processing  │
└───────────┬──┘  └───────────┬──┘  └───────┬──────────┘
            │                 │              │
┌───────────▼─────────────────▼──────────────▼────────────┐
│                    INFRASTRUCTURE                        │
│   Hugging Face Hub │ Upstash Redis │ Supabase           │
│   Modal.com        │ Docker        │ GitHub Actions      │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Speech to Text (STT)

### Purpose
Convert incoming Welsh audio to text accurately and in real time.

### Components

| Component | Tool | Version | Why |
|---|---|---|---|
| Base Model | OpenAI Whisper | small / medium | Best open ASR baseline |
| Optimised Runtime | faster-whisper | latest | 4x faster, same accuracy |
| Welsh Fine-tune | CV 25.0 Welsh | 124hrs validated | Domain adaptation |
| Voice Detection | silero-vad | v4 | Detects speech start/end |
| Streaming | whisper-streaming | latest | Real-time chunk output |

### Flow
```
Audio bytes in
     ↓
Silero VAD (is someone speaking?)
     ↓
faster-whisper chunks (streaming)
     ↓
Welsh text out
```

### Key Config
```python
model = WhisperModel(
    "llais-cymraeg/whisper-welsh-small",  # our fine-tuned model on HF
    device="cpu",                          # or "cuda" if GPU available
    compute_type="int8"                    # quantised for speed
)

segments, _ = model.transcribe(
    audio,
    language="cy",          # force Welsh
    beam_size=5,
    vad_filter=True,        # built-in VAD
    word_timestamps=True    # for alignment
)
```

---

## Layer 2 — Language Model (LLM)

### Purpose
Understand the Welsh input and generate a relevant Welsh response.

### Components

| Component | Tool | Why |
|---|---|---|
| Base Model | Llama 3.1 8B | Free, open, strong Welsh base |
| Welsh Adapter | LoRA fine-tune | Welsh language, culture, context |
| Orchestration | LangChain | Agent logic, tools, memory |
| Memory | ChromaDB | Conversation context store |
| Runtime | Ollama | Local inference, free |

### Flow
```
Welsh text in
     ↓
Retrieve conversation memory (ChromaDB)
     ↓
Build prompt with Welsh system context
     ↓
Llama 3.1 8B generates Welsh response
     ↓
Store response in memory
     ↓
Welsh text out
```

### System Prompt Template
```
Ti yw cynorthwyydd llais Cymraeg. Rwyt ti'n siarad Cymraeg yn unig.
Mae dy atebion yn naturiol, cynnes ac yn briodol i'r cyd-destun.
[You are a Welsh language voice assistant. You speak Welsh only.
Your answers are natural, warm and contextually appropriate.]
```

---

## Layer 3 — Text to Speech (TTS)

### Purpose
Convert Welsh text response into natural, near-human Welsh audio.

### Components

| Component | Tool | Why |
|---|---|---|
| Core TTS | Coqui XTTS v2 | Voice cloning, Welsh support |
| Prosody Control | SSML tags + custom rules | Natural Welsh rhythm |
| Post-processing | Spotify pedalboard | EQ, compression, warmth |
| Multi-speaker | 2 voice profiles | North + South Welsh |
| Streaming | Chunk-based | Low latency playback |

### Flow
```
Welsh text in
     ↓
SSML prosody rules applied (pauses, stress, breathing)
     ↓
XTTS v2 generates audio chunks
     ↓
pedalboard post-processing (EQ → compress → reverb)
     ↓
Audio bytes streamed out
```

### Post-processing Chain
```python
from pedalboard import Pedalboard, Reverb, Compressor, HighpassFilter

board = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=80),   # remove rumble
    Compressor(threshold_db=-20, ratio=3),     # even out volume
    Reverb(room_size=0.1, wet_level=0.05),    # subtle warmth
])
```

---

## Layer 4 — API Gateway

### Endpoints

| Endpoint | Type | Purpose |
|---|---|---|
| `GET /health` | REST | Service health check |
| `POST /stt` | REST | Batch audio → text |
| `POST /tts` | REST | Batch text → audio |
| `POST /chat` | REST | Full pipeline, single turn |
| `WS /ws/voice` | WebSocket | Real-time streaming voice |
| `GET /voices` | REST | List available Welsh voices |

### WebSocket Message Protocol
```json
// Client → Server
{
  "type": "audio_chunk",
  "data": "<base64 audio bytes>",
  "sample_rate": 16000
}

// Server → Client
{
  "type": "transcript",
  "text": "Shwmae, sut ydych chi?",
  "is_final": true
}

{
  "type": "audio_response",
  "data": "<base64 audio bytes>",
  "voice": "south-welsh-female"
}
```

---

## Layer 5 — Infrastructure

### Free Tier Stack

| Purpose | Service | Cost |
|---|---|---|
| Model weights | Hugging Face Hub | Free |
| GPU training | Kaggle Notebooks | Free (30hrs/week) |
| API hosting | Modal.com | Free ($30 credit) |
| Cache | Upstash Redis | Free tier |
| Database | Supabase | Free tier |
| CI/CD | GitHub Actions | Free |
| Demo UI | Hugging Face Spaces | Free |
| Monitoring | Grafana Cloud | Free tier |

---

## Voice Agent Integration

### Vapi
```json
{
  "transcriber": {
    "provider": "custom",
    "url": "wss://your-api.modal.run/ws/voice",
    "language": "cy"
  },
  "voice": {
    "provider": "custom",
    "url": "https://your-api.modal.run/tts"
  }
}
```

### LiveKit
```python
from livekit import agents

agent = agents.VoiceAgent(
    stt=CustomSTT(url="wss://your-api.modal.run/ws/stt"),
    tts=CustomTTS(url="https://your-api.modal.run/tts"),
    llm=CustomLLM(url="https://your-api.modal.run/chat")
)
```

### n8n
Use HTTP Request node → POST to `https://your-api.modal.run/chat`

---

## Data Flow — Full Pipeline

```
1. User speaks Welsh         → microphone captures audio
2. Audio chunks sent         → WebSocket to FastAPI
3. VAD detects speech end    → triggers STT
4. faster-whisper transcribes→ Welsh text produced
5. LangChain + Llama         → Welsh response generated
6. XTTS v2 synthesises       → audio chunks produced
7. pedalboard post-processes → broadcast quality audio
8. Audio streamed back        → user hears Welsh response
```

Total target latency: **< 800ms** end to end on CPU, **< 300ms** on GPU.
