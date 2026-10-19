"""
AI Interview Speech Quality Analyzer - FastAPI Application
Provides REST API endpoints for audio speech-to-text conversion,
fluency analysis, grammar assessment, vocabulary richness evaluation,
and serves the web frontend.
"""

import os
import shutil
import time
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .modules.speech_to_text import transcribe_audio_file, get_audio_duration_wave
from .modules.evaluator import evaluate_interview_response

app = FastAPI(
    title="AI Interview Speech Quality Analyzer",
    description="Automated AI and NLP system for analyzing spoken interview performance: Fluency, Grammar, and Vocabulary.",
    version="1.0.0"
)

# Enable CORS for cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


class TextAnalysisRequest(BaseModel):
    text: str
    duration_seconds: Optional[float] = 30.0


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Interview Speech Quality Analyzer",
        "timestamp": time.time()
    }


@app.post("/api/analyze-text")
def analyze_text_endpoint(req: TextAnalysisRequest):
    """
    Analyzes raw interview transcript text directly.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    results = evaluate_interview_response(
        text=req.text.strip(),
        duration_sec=req.duration_seconds or 30.0
    )
    return results


@app.post("/api/analyze-audio")
async def analyze_audio_endpoint(
    audio: Optional[UploadFile] = File(None),
    client_transcript: Optional[str] = Form(None),
    duration_seconds: Optional[float] = Form(None)
):
    """
    Accepts recorded microphone audio or uploaded audio file.
    Performs Speech-to-Text conversion and comprehensive NLP assessment.
    """
    transcript = ""
    duration = duration_seconds or 0.0
    pauses = []

    saved_path = None
    if audio and audio.filename:
        # Save uploaded audio file to uploads/
        file_ext = os.path.splitext(audio.filename)[1] or ".wav"
        filename = f"interview_recording_{int(time.time() * 1000)}{file_ext}"
        saved_path = os.path.join(UPLOADS_DIR, filename)

        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Transcribe audio using STT module
        stt_result = transcribe_audio_file(saved_path)
        transcript = stt_result.get("transcript", "")
        
        # If STT detected duration and none was provided from frontend, use STT duration
        if duration <= 0:
            duration = stt_result.get("duration", 0.0)
            if duration <= 0:
                duration = get_audio_duration_wave(saved_path)
        
        pauses = stt_result.get("pauses", [])

    # If client-side Web Speech API already captured the live transcript, prioritize it if local STT is empty
    if not transcript and client_transcript:
        transcript = client_transcript.strip()

    if not transcript:
        # If both audio STT and client transcript yielded no words
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Could not extract speech from audio. Please check your microphone, speak clearly, or enter text manually.",
                "duration_seconds": duration
            }
        )

    # Perform multi-dimensional NLP evaluation
    evaluation = evaluate_interview_response(
        text=transcript,
        duration_sec=duration if duration > 0 else 30.0,
        pauses=pauses
    )

    # Clean up temp audio file if needed (or keep for audit)
    # if saved_path and os.path.exists(saved_path):
    #     os.remove(saved_path)

    return evaluation


# Serve Frontend Web App
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def serve_home():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
