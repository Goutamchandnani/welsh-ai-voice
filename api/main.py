"""
api/main.py

Phase 5 — Llais Cymraeg REST API

Endpoints:
  GET  /health      — Health check
  POST /transcribe  — Audio file → Welsh text (STT)
  POST /synthesise  — Welsh text → WAV audio (TTS)
  POST /chat        — Welsh text → WAV audio (LLM + TTS)
  POST /voice       — Audio file → WAV audio (Full pipeline)
"""

import sys
import time
import tempfile
from pathlib import Path

import soundfile as sf
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

# Add scripts directory to path for LLM module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from llm_welsh import respond

# ── Configuration ─────────────────────────────────────────
STT_MODEL_PATH = "models/faster-whisper-small-cy"
KOKORO_MODEL   = "models/kokoro/kokoro-v1.0.onnx"
KOKORO_VOICES  = "models/kokoro/voices-v1.0.bin"
OUTPUT_DIR     = Path("data/api_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── App Setup ─────────────────────────────────────────────
app = FastAPI(
    title="Llais Cymraeg — Welsh Voice AI API",
    description="Open-source Welsh STT → LLM → TTS pipeline. Speak Welsh, get Welsh back.",
    version="0.1.0",
)

# ── Lazy-loaded models (loaded once on first request) ──────
_stt_model  = None
_tts_engine = None

def get_stt():
    global _stt_model
    if _stt_model is None:
        _stt_model = WhisperModel(STT_MODEL_PATH, device="cpu", compute_type="int8")
    return _stt_model

def get_tts():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
    return _tts_engine


# ── Helper ─────────────────────────────────────────────────
async def save_upload(upload: UploadFile) -> str:
    """Save an uploaded file to a temp location and return the path."""
    suffix = Path(upload.filename).suffix or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await upload.read())
        return tmp.name

def text_to_wav(text: str, out_path: str, speed: float = 0.9) -> None:
    """Synthesise Welsh text and write to WAV."""
    samples, sr = get_tts().create(text, voice="af_heart", speed=speed, lang="cy")
    sf.write(out_path, samples, sr)


# ── Routes ─────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Returns the current status of all pipeline components."""
    return {
        "status": "ok",
        "pipeline": "STT → LLM → TTS",
        "models": {
            "stt": "whisper-small-cy (faster-whisper)",
            "llm": "llama3.2:3b (Ollama)",
            "tts": "kokoro-v1.0 (ONNX)",
        },
        "version": "0.1.0",
    }


@app.post("/transcribe", tags=["STT"])
async def transcribe(audio: UploadFile = File(...)):
    """
    Upload a Welsh audio file and get the transcribed Welsh text back.

    - Accepts: MP3, WAV, OGG
    - Returns: JSON with 'text' and 'latency_s'
    """
    audio_path = await save_upload(audio)
    t0 = time.time()
    segments, info = get_stt().transcribe(audio_path, language="cy", beam_size=5)
    text = " ".join(s.text for s in segments).strip()
    return {
        "text": text,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "latency_s": round(time.time() - t0, 3),
    }


@app.post("/synthesise", tags=["TTS"])
async def synthesise(text: str = Form(...), speed: float = Form(0.9)):
    """
    Convert Welsh text to speech and return the WAV audio file.

    - text:  Welsh text to synthesise
    - speed: Speaking speed (0.8 = slower, 1.0 = normal)
    - Returns: WAV audio file
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    out_path = str(OUTPUT_DIR / f"synth_{int(time.time() * 1000)}.wav")
    text_to_wav(text, out_path, speed=speed)
    return FileResponse(out_path, media_type="audio/wav", filename="response.wav")


@app.post("/chat", tags=["Pipeline"])
async def chat(text: str = Form(...)):
    """
    Send Welsh text, get a Welsh spoken audio response.

    Pipeline: Welsh text → LLM → TTS → WAV

    - text: Welsh input text
    - Returns: WAV audio file with the AI's Welsh response
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    t0 = time.time()
    llm_response = respond(text, verbose=False)
    out_path = str(OUTPUT_DIR / f"chat_{int(time.time() * 1000)}.wav")
    text_to_wav(llm_response, out_path)

    # Return audio + metadata in headers so callers know what was said
    headers = {
        "X-Input-Text":    text,
        "X-LLM-Response":  llm_response,
        "X-Total-Latency": str(round(time.time() - t0, 3)),
    }
    return FileResponse(out_path, media_type="audio/wav", filename="response.wav", headers=headers)


@app.post("/voice", tags=["Pipeline"])
async def voice(audio: UploadFile = File(...)):
    """
    The full pipeline: upload Welsh audio, receive Welsh spoken response.

    Pipeline: Audio → STT → LLM → TTS → WAV

    - audio: Welsh audio file (MP3/WAV/OGG)
    - Returns: WAV audio file with the AI's Welsh response
    """
    audio_path = await save_upload(audio)
    t0 = time.time()

    # 1. STT
    segments, _ = get_stt().transcribe(audio_path, language="cy", beam_size=5)
    transcription = " ".join(s.text for s in segments).strip()

    # 2. LLM
    llm_response = respond(transcription, verbose=False)

    # 3. TTS
    out_path = str(OUTPUT_DIR / f"voice_{int(time.time() * 1000)}.wav")
    text_to_wav(llm_response, out_path)

    headers = {
        "X-Transcription": transcription,
        "X-LLM-Response":  llm_response,
        "X-Total-Latency": str(round(time.time() - t0, 3)),
    }
    return FileResponse(out_path, media_type="audio/wav", filename="response.wav", headers=headers)
