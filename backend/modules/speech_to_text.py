"""
Speech-to-Text (STT) Module
State-of-the-art ASR pipeline:
1. Groq OpenAI Whisper-Large-v3 (Sub-second, 1.5B parameter flagship model)
2. Local Faster-Whisper (small.en with Silero VAD)
3. SpeechRecognition Fallback
"""

import os
import wave
import requests
import numpy as np
from typing import Dict, List, Any

_FASTER_WHISPER_MODEL = None


def transcribe_via_groq_whisper(file_path: str) -> Dict[str, Any]:
    """
    Transcribes audio using OpenAI Whisper Large v3 on Groq LPUs.
    Fastest and highest accuracy speech recognition model available.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {}

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/wav")}
            data = {
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
                "temperature": "0.0",
                "prompt": "Interview answer discussing professional career goals, technical problem solving, hard work, and leadership."
            }
            res = requests.post(url, headers=headers, files=files, data=data, timeout=15)

        if res.status_code == 200:
            result = res.json()
            transcript = result.get("text", "").strip()
            duration = float(result.get("duration", 0.0))
            segments = result.get("segments", [])

            # Detect acoustic pauses (> 0.7s)
            pauses = []
            prev_end = 0.0
            for seg in segments:
                gap = seg["start"] - prev_end
                if gap >= 0.7 and prev_end > 0.0:
                    pauses.append({
                        "start": round(float(prev_end), 2),
                        "end": round(float(seg["start"]), 2),
                        "duration": round(float(gap), 2)
                    })
                prev_end = seg["end"]

            print(f"[STT] Groq Whisper-Large-v3 Transcribed ({len(transcript.split())} words): '{transcript}'")
            return {
                "transcript": transcript,
                "duration": round(duration, 2),
                "pauses": pauses,
                "engine": "OpenAI Whisper-Large-v3 (Groq)"
            }
        else:
            print(f"[STT] Groq Whisper returned HTTP {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[STT] Groq Whisper error: {e}")

    return {}


def get_whisper_model(model_size: str = "small.en"):
    """
    Loads local Faster-Whisper transformer model with INT8 quantization.
    """
    global _FASTER_WHISPER_MODEL
    if _FASTER_WHISPER_MODEL is None:
        try:
            from faster_whisper import WhisperModel
            print(f"[STT] Loading local Faster-Whisper ({model_size})...")
            _FASTER_WHISPER_MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
            print("[STT] Local Faster-Whisper loaded successfully.")
        except Exception as e:
            print(f"[STT] Local Whisper load error: {e}")
            _FASTER_WHISPER_MODEL = False
    return _FASTER_WHISPER_MODEL


def read_wav_float32(file_path: str):
    """
    Reads 16-bit PCM WAV into float32 array normalized to [-1.0, 1.0].
    """
    try:
        with wave.open(file_path, "rb") as wf:
            n_channels = wf.getnchannels()
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = round(n_frames / float(frame_rate), 2)
            raw = wf.readframes(n_frames)
            audio_int16 = np.frombuffer(raw, dtype=np.int16)
            if n_channels > 1:
                audio_int16 = audio_int16.reshape(-1, n_channels).mean(axis=1).astype(np.int16)
            return audio_int16.astype(np.float32) / 32768.0, duration, frame_rate
    except Exception as e:
        print(f"[STT] WAV read error {file_path}: {e}")
        return None, 0.0, 16000


def get_audio_duration_wave(file_path: str) -> float:
    _, duration, _ = read_wav_float32(file_path)
    return duration


def transcribe_audio_file(file_path: str) -> Dict[str, Any]:
    """
    Master speech-to-text pipeline:
    1. Try OpenAI Whisper-Large-v3 on Groq (Ultra-accurate & fast)
    2. Fallback to Local Faster-Whisper small.en with VAD
    3. Fallback to Google SpeechRecognition
    """
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    print(f"[STT] Processing audio file: {file_path} ({file_size} bytes)")

    if file_size < 1000:
        return {"transcript": "", "duration": 0.0, "pauses": [], "engine": "None"}

    # 1. Tier 1: Groq Whisper-Large-v3
    groq_result = transcribe_via_groq_whisper(file_path)
    if groq_result and groq_result.get("transcript"):
        return groq_result

    # Read audio samples for local engines
    audio_data, duration, sample_rate = read_wav_float32(file_path)

    # 2. Tier 2: Local Faster-Whisper small.en with VAD
    model = get_whisper_model("small.en")
    if model and audio_data is not None and len(audio_data) > 0:
        try:
            print("[STT] Running local Faster-Whisper with VAD...")
            segments, info = model.transcribe(
                audio_data,
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
                initial_prompt="Candidate answering an interview question about achievements, hard work, projects, and career experience."
            )
            segment_texts = []
            pauses = []
            prev_end = 0.0

            for seg in segments:
                clean = seg.text.strip()
                if clean:
                    segment_texts.append(clean)
                gap = float(seg.start - prev_end)
                if gap >= 0.7 and prev_end > 0.0:
                    pauses.append({
                        "start": round(float(prev_end), 2),
                        "end": round(float(seg.start), 2),
                        "duration": round(gap, 2)
                    })
                prev_end = float(seg.end)

            transcript = " ".join(segment_texts).strip()
            if transcript:
                print(f"[STT] Local Whisper Transcribed: '{transcript}'")
                return {
                    "transcript": transcript,
                    "duration": duration,
                    "pauses": pauses,
                    "engine": "Local Faster-Whisper (small.en)"
                }
        except Exception as e:
            print(f"[STT] Local Whisper error: {e}")

    # 3. Tier 3: SpeechRecognition Fallback
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            data = r.record(source)
            text = r.recognize_google(data)
            return {
                "transcript": text,
                "duration": duration,
                "pauses": [],
                "engine": "Google Speech Recognition"
            }
    except Exception as e:
        print(f"[STT] SpeechRecognition fallback error: {e}")

    return {"transcript": "", "duration": duration, "pauses": [], "engine": "None"}
