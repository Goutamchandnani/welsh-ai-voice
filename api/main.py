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
import os
import hashlib
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Security, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader
from supabase import create_client, Client
from upstash_redis import Redis
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

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("⚠️  Warning: Supabase credentials missing. API Key validation will fail.")

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
    redis = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)
else:
    redis = None
    print("⚠️  Warning: Upstash Redis credentials missing. Rate limiting is disabled.")

RATE_LIMITS = {
    "free": 10,   # requests per minute
    "pro": 100    # requests per minute
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    """Verifies the incoming API key against the Supabase database."""
    if not api_key_header:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Auth database is not configured")

    # Hash the incoming key to compare with the stored hash
    key_hash = hashlib.sha256(api_key_header.encode('utf-8')).hexdigest()

    try:
        response = supabase.table("api_keys").select("id", "status", "tier").eq("key_hash", key_hash).execute()
        data = response.data
        
        if not data:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        key_data = data[0]
        if key_data["status"] != "active":
            raise HTTPException(status_code=401, detail="API Key has been revoked or suspended")
            
        api_key_id = key_data["id"]
        tier = key_data["tier"]
        
        # ── Rate Limiting ─────────────────────────────────────────
        if redis:
            # Fixed window rate limit based on current minute
            current_minute = int(time.time() / 60)
            redis_key = f"rate_limit:{api_key_id}:{current_minute}"
            
            try:
                # Increment the counter for this minute
                requests_this_minute = redis.incr(redis_key)
                
                # If it's the first request, set the key to expire in 60 seconds
                if requests_this_minute == 1:
                    redis.expire(redis_key, 60)
                    
                limit = RATE_LIMITS.get(tier, 10)
                
                if requests_this_minute > limit:
                    # Calculate seconds until the next minute starts
                    retry_after = 60 - (int(time.time()) % 60)
                    raise HTTPException(
                        status_code=429, 
                        detail=f"Rate limit exceeded. Tier '{tier}' is limited to {limit} requests per minute.",
                        headers={"Retry-After": str(retry_after)}
                    )
            except Exception as redis_err:
                if isinstance(redis_err, HTTPException):
                    raise redis_err
                print(f"Redis rate limiting failed (failing open): {redis_err}")
                
        return {"id": api_key_id, "tier": tier}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Auth error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication")

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

# Available Welsh voice profiles from Kokoro
AVAILABLE_VOICES = {
    "af_heart": "Female — warm and natural (default)",
    "af_bella": "Female — clear and articulate",
    "af_sarah": "Female — soft and calm",
    "am_adam":  "Male — deep and steady",
    "am_michael": "Male — bright and energetic",
}
DEFAULT_VOICE = "af_heart"
MAX_TEXT_CHARS = 5000

def text_to_wav(text: str, out_path: str, voice: str = DEFAULT_VOICE, speed: float = 0.9) -> None:
    """Synthesise Welsh text and write to WAV."""
    samples, sr = get_tts().create(text, voice=voice, speed=speed, lang="cy")
    sf.write(out_path, samples, sr)

def log_usage(api_key_id: str, endpoint: str, latency: float, status_code: int = 200, audio_duration: float = None):
    """Logs API usage asynchronously to Supabase."""
    if not supabase:
        return
    try:
        supabase.table("usage_logs").insert({
            "api_key_id": api_key_id,
            "endpoint": endpoint,
            "latency_seconds": latency,
            "status_code": status_code,
            "audio_duration_seconds": audio_duration
        }).execute()
    except Exception as e:
        print(f"Failed to log usage: {e}")


# ── Schemas ────────────────────────────────────────────────
class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    latency_s: float

class VoiceItem(BaseModel):
    id: str
    description: str

class VoiceListResponse(BaseModel):
    voices: list[VoiceItem]
    default_voice: str

# ── Routes ─────────────────────────────────────────────────

@app.get("/v1/health", tags=["System"])
@app.get("/health", tags=["System"])  # Legacy alias — kept for backwards compatibility
def health():
    """Returns the current status of all pipeline components."""
    return {
        "status": "ok",
        "pipeline": "STT → LLM → TTS",
        "models": {
            "stt": "whisper-small-cy (faster-whisper, int8)",
            "llm": "llama3.1:8b (Ollama)",
            "tts": "kokoro-v1.0 (ONNX)",
        },
        "version": "1.0.0",
    }


@app.get("/v1/voices", tags=["TTS"], response_model=VoiceListResponse)
def get_voices():
    """
    Returns the list of available Welsh voice profiles for TTS endpoints.
    """
    voice_list = [VoiceItem(id=v_id, description=desc) for v_id, desc in AVAILABLE_VOICES.items()]
    return VoiceListResponse(voices=voice_list, default_voice=DEFAULT_VOICE)


@app.post("/v1/transcribe", tags=["STT"], response_model=TranscriptionResponse)
async def transcribe(background_tasks: BackgroundTasks, audio: UploadFile = File(...), api_key: dict = Depends(verify_api_key)):
    """
    Upload a Welsh audio file and get the transcribed Welsh text back.

    - Accepts: MP3, WAV, OGG
    - Returns: JSON with transcribed text and metadata
    """
    try:
        audio_path = await save_upload(audio)
        t0 = time.time()
        
        segments, info = get_stt().transcribe(audio_path, language="cy", beam_size=5)
        text = " ".join(s.text for s in segments).strip()
        
        latency = round(time.time() - t0, 3)
        audio_dur = segments[-1].end if segments else 0.0
        
        background_tasks.add_task(log_usage, api_key["id"], "/v1/transcribe", latency, 200, audio_dur)
        
        return TranscriptionResponse(
            text=text,
            language=info.language,
            language_probability=round(info.language_probability, 3),
            latency_s=latency
        )
    except Exception as e:
        background_tasks.add_task(log_usage, api_key["id"], "/v1/transcribe", 0, 500, 0)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/v1/synthesise", tags=["TTS"])
async def synthesise(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    voice: str = Form(DEFAULT_VOICE),
    speed: float = Form(0.9),
    api_key: dict = Depends(verify_api_key)
):
    """
    Convert Welsh text to speech and return the WAV audio file.

    - text:  Welsh text to synthesise (max 5000 characters)
    - voice: Voice profile ID (see GET /v1/voices for options)
    - speed: Speaking speed (0.5 = slow, 1.0 = normal, 1.5 = fast)
    - Returns: WAV audio file
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=400, detail=f"Text exceeds maximum length of {MAX_TEXT_CHARS} characters.")
    if voice not in AVAILABLE_VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice '{voice}'. Use GET /v1/voices to see available options.")
    if not (0.5 <= speed <= 2.0):
        raise HTTPException(status_code=400, detail="Speed must be between 0.5 and 2.0.")
    
    try:
        t0 = time.time()
        out_path = str(OUTPUT_DIR / f"synth_{int(time.time() * 1000)}.wav")
        text_to_wav(text, out_path, voice=voice, speed=speed)
        latency = round(time.time() - t0, 3)
        
        background_tasks.add_task(log_usage, api_key["id"], "/v1/synthesise", latency, 200)
        
        return FileResponse(out_path, media_type="audio/wav", filename="response.wav")
    except Exception as e:
        background_tasks.add_task(log_usage, api_key["id"], "/v1/synthesise", 0, 500)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.post("/v1/chat", tags=["Pipeline"])
async def chat(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    voice: str = Form(DEFAULT_VOICE),
    api_key: dict = Depends(verify_api_key)
):
    """
    Send Welsh text, get a Welsh spoken audio response.

    Pipeline: Welsh text → LLM → TTS → WAV

    - text:  Welsh input text (max 5000 characters)
    - voice: Voice profile ID (see GET /v1/voices for options)
    - Returns: WAV audio file with the AI's Welsh response
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=400, detail=f"Text exceeds maximum length of {MAX_TEXT_CHARS} characters.")
    if voice not in AVAILABLE_VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice '{voice}'. Use GET /v1/voices to see available options.")

    try:
        # LLM
        t_llm = time.time()
        llm_response = respond(text, verbose=False)
        llm_latency = round(time.time() - t_llm, 3)

        # TTS
        t_tts = time.time()
        out_path = str(OUTPUT_DIR / f"chat_{int(time.time() * 1000)}.wav")
        text_to_wav(llm_response, out_path, voice=voice)
        tts_latency = round(time.time() - t_tts, 3)

        total_latency = round(llm_latency + tts_latency, 3)
        background_tasks.add_task(log_usage, api_key["id"], "/v1/chat", total_latency, 200)

        headers = {
            "X-Input-Text":    text,
            "X-LLM-Response":  llm_response,
            "X-LLM-Latency":   str(llm_latency),
            "X-TTS-Latency":   str(tts_latency),
            "X-Total-Latency": str(total_latency),
        }
        return FileResponse(out_path, media_type="audio/wav", filename="response.wav", headers=headers)
    except Exception as e:
        background_tasks.add_task(log_usage, api_key["id"], "/v1/chat", 0, 500)
        raise HTTPException(status_code=500, detail=f"Chat pipeline failed: {str(e)}")


@app.post("/v1/voice", tags=["Pipeline"])
async def voice(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    voice: str = Form(DEFAULT_VOICE),
    api_key: dict = Depends(verify_api_key)
):
    """
    The full pipeline: upload Welsh audio, receive Welsh spoken response.

    Pipeline: Audio → STT → LLM → TTS → WAV

    - audio: Welsh audio file (MP3/WAV/OGG)
    - voice: Voice profile ID (see GET /v1/voices for options)
    - Returns: WAV audio file with the AI's Welsh response
    """
    if voice not in AVAILABLE_VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice '{voice}'. Use GET /v1/voices to see available options.")

    try:
        audio_path = await save_upload(audio)

        # 1. STT
        t_stt = time.time()
        segments, _ = get_stt().transcribe(audio_path, language="cy", beam_size=5)
        transcription = " ".join(s.text for s in segments).strip()
        stt_latency = round(time.time() - t_stt, 3)

        # 2. LLM
        t_llm = time.time()
        llm_response = respond(transcription, verbose=False)
        llm_latency = round(time.time() - t_llm, 3)

        # 3. TTS
        t_tts = time.time()
        out_path = str(OUTPUT_DIR / f"voice_{int(time.time() * 1000)}.wav")
        text_to_wav(llm_response, out_path, voice=voice)
        tts_latency = round(time.time() - t_tts, 3)

        total_latency = round(stt_latency + llm_latency + tts_latency, 3)
        audio_dur = segments[-1].end if segments else 0.0
        background_tasks.add_task(log_usage, api_key["id"], "/v1/voice", total_latency, 200, audio_dur)

        headers = {
            "X-Transcription": transcription,
            "X-LLM-Response":  llm_response,
            "X-STT-Latency":   str(stt_latency),
            "X-LLM-Latency":   str(llm_latency),
            "X-TTS-Latency":   str(tts_latency),
            "X-Total-Latency": str(total_latency),
        }
        return FileResponse(out_path, media_type="audio/wav", filename="response.wav", headers=headers)
    except Exception as e:
        background_tasks.add_task(log_usage, api_key["id"], "/v1/voice", 0, 500)
        raise HTTPException(status_code=500, detail=f"Voice pipeline failed: {str(e)}")

