"""
AI Evaluator Module
Provides high-precision contextual evaluation of spoken interview responses
using state-of-the-art LLMs (via Groq API) with graceful fallback to local NLP.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def evaluate_with_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates interview response using Groq LLM (openai/gpt-oss-120b or 20b).
    Returns accurate grammar diagnosis, vocabulary scoring, and personalized coaching.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert Executive Interview Coach and Senior Linguistic Assessor. "
        "Analyze the candidate's spoken interview answer thoroughly and accurately. "
        "Distinguish between natural conversational flow and actual grammatical mistakes. "
        "Output ONLY valid JSON without markdown wrapping or code blocks."
    )

    user_prompt = f"""Evaluate this spoken interview answer:
\"{text}\"

Respond strictly with a JSON object in this format:
{{
  "grammar_score": 88,
  "grammar_errors": [
    {{
      "type": "Error Category (e.g. Subject-Verb Agreement, Run-on Sentence, Tense Consistency)",
      "text": "the exact wrong phrase",
      "explanation": "why it is grammatically incorrect in professional English",
      "suggestion": "how to rephrase it professionally"
    }}
  ],
  "vocabulary_score": 85,
  "vocabulary_level": "Professional / Upper-Intermediate",
  "professional_keywords": ["dedication", "continuous effort", "knowledge"],
  "repetitive_words": ["mistakes (2x)", "success (3x)"],
  "strengths": [
    "Clear, logical narrative flow with an inspiring opening and strong conclusion.",
    "Effective use of a relatable analogy (the student example) to illustrate consistency."
  ],
  "improvements": [
    "Ground the answer in a specific personal technical or work project instead of general philosophy.",
    "Incorporate quantifiable results to demonstrate measurable impact (STAR method)."
  ],
  "coherence_score": 90,
  "executive_summary": "Strong, articulate response demonstrating maturity and resilience, though could be elevated by citing concrete professional achievements."
}}"""

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            # Strip markdown if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            data = json.loads(content.strip())
            return data
        else:
            print(f"[AI Evaluator] Groq LLM API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[AI Evaluator] LLM evaluation exception: {e}")

    return None
