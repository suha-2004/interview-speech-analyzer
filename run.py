"""
Launcher script for AI Interview Speech Quality Analyzer.
Run this file to start the web application.
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print("  AI Interview Speech Quality Analyzer (VerbaIQ)")
    print(f"  Python: {sys.executable}")
    if os.environ.get("GROQ_API_KEY"):
        print("  ASR Engine: OpenAI Whisper-Large-v3 [FLAGSHIP 1.5B]")
        print("  AI Evaluator: Contextual Linguistic Assessor (Active)")
    else:
        print("  ASR Engine: Local Faster-Whisper (small.en) with VAD")
        print("  AI Evaluator: Statistical & Syntactic Rule Engine")
    print("  Server URL: http://localhost:8000")
    print("=" * 65)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
