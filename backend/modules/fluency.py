"""
Fluency Analyzer Module
Computes Speech Rate (WPM), Filler Words Density, Silent Pauses, and Fluency Score.
"""

import re
from typing import Dict, List, Any, Tuple

# Comprehensive list of conversational and interview filler words/phrases
FILLER_PATTERNS = [
    # Multi-word phrases (checked first)
    (r"\b(you know)\b", "you know"),
    (r"\b(i mean)\b", "i mean"),
    (r"\b(sort of)\b", "sort of"),
    (r"\b(kind of)\b", "kind of"),
    (r"\b(so yeah)\b", "so yeah"),
    (r"\b(at the end of the day)\b", "at the end of the day"),
    (r"\b(to be honest)\b", "to be honest"),
    # Single-word fillers
    (r"\b(um+)\b", "um"),
    (r"\b(uh+)\b", "uh"),
    (r"\b(er+)\b", "er"),
    (r"\b(ah+)\b", "ah"),
    (r"\b(like)\b", "like"),
    (r"\b(basically)\b", "basically"),
    (r"\b(actually)\b", "actually"),
    (r"\b(literally)\b", "literally"),
    (r"\b(honestly)\b", "honestly"),
]


def detect_filler_words(text: str) -> Tuple[int, Dict[str, int], List[Dict[str, Any]]]:
    """
    Identifies filler words and discourse markers in the transcript.
    Returns:
        total_fillers: Total count of filler words
        filler_breakdown: Dictionary of {filler: count}
        filler_occurrences: List of {word, start_char, end_char} for highlighting
    """
    lower_text = text.lower()
    total_fillers = 0
    filler_breakdown: Dict[str, int] = {}
    filler_occurrences: List[Dict[str, Any]] = []

    # Track matched spans to avoid double counting nested phrases
    matched_spans = set()

    for pattern, label in FILLER_PATTERNS:
        for match in re.finditer(pattern, lower_text):
            span = (match.start(), match.end())
            # Check overlap with existing spans
            if any(s[0] <= span[0] and span[1] <= s[1] for s in matched_spans):
                continue
            
            matched_spans.add(span)
            total_fillers += 1
            filler_breakdown[label] = filler_breakdown.get(label, 0) + 1
            filler_occurrences.append({
                "word": match.group(0),
                "label": label,
                "start": match.start(),
                "end": match.end()
            })

    # Sort occurrences by character position
    filler_occurrences.sort(key=lambda x: x["start"])
    return total_fillers, filler_breakdown, filler_occurrences


def calculate_speaking_rate(word_count: int, duration_sec: float) -> Tuple[float, str]:
    """
    Computes Words Per Minute (WPM) and pacing diagnosis.
    Optimal interview pace is generally between 120 and 160 WPM.
    """
    if duration_sec <= 0 or word_count == 0:
        return 0.0, "No speech detected"
    
    minutes = duration_sec / 60.0
    wpm = round(word_count / minutes, 1)

    if wpm < 100:
        pace_label = "Too Slow (Hesitant)"
    elif 100 <= wpm < 120:
        pace_label = "Slightly Slow"
    elif 120 <= wpm <= 160:
        pace_label = "Ideal Interview Pace"
    elif 161 <= wpm <= 180:
        pace_label = "Slightly Fast"
    else:
        pace_label = "Too Fast (Rushing / Nervous)"

    return wpm, pace_label


def compute_fluency_score(
    wpm: float,
    filler_percentage: float,
    pause_count: int,
    pause_ratio: float
) -> Tuple[int, List[str]]:
    """
    Calculates a 0-100 fluency score based on WPM balance, filler word usage, and pause patterns.
    """
    score = 100.0
    feedback = []

    # 1. Pacing penalty (Ideal: 120 - 160 WPM)
    if wpm == 0:
        score -= 50
        feedback.append("No words detected in audio.")
    elif 120 <= wpm <= 160:
        feedback.append("Excellent pacing! You are within the ideal interview range of 120-160 WPM.")
    elif 100 <= wpm < 120:
        score -= 10
        feedback.append("Your speaking speed is slightly slow. Try answering with slightly more momentum.")
    elif wpm < 100:
        score -= 25
        feedback.append("Speaking rate is too slow (<100 WPM). This can sound hesitant or uncertain.")
    elif 160 < wpm <= 180:
        score -= 10
        feedback.append("Your speaking speed is slightly fast. Take deliberate breaths between key points.")
    else:  # > 180
        score -= 25
        feedback.append("Speaking rate is too fast (>180 WPM). Slow down so the interviewer can absorb your answers.")

    # 2. Filler words penalty
    if filler_percentage == 0:
        feedback.append("Outstanding! Zero filler words detected.")
    elif filler_percentage <= 2.0:
        score -= 5
        feedback.append(f"Minimal filler word usage ({filler_percentage}%). Very clean delivery.")
    elif filler_percentage <= 5.0:
        score -= 15
        feedback.append(f"Moderate filler word usage ({filler_percentage}%). Try replacing filler words with short silent pauses.")
    else:
        score -= 30
        feedback.append(f"High filler word density ({filler_percentage}%). Practice conscious pause technique instead of saying fillers.")

    # 3. Pause & silence penalty
    if pause_ratio > 0.35:
        score -= 15
        feedback.append("Excessive long pauses detected (>35% of total time). Structure your thoughts before answering.")
    elif pause_ratio > 0.20:
        score -= 5

    # Clamp score between 10 and 100
    final_score = int(max(10.0, min(100.0, round(score))))
    return final_score, feedback


def analyze_fluency(text: str, duration_sec: float, pauses: List[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Main entry point for Fluency Analysis.
    """
    words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
    word_count = len(words)

    # Filler words
    total_fillers, breakdown, occurrences = detect_filler_words(text)
    filler_pct = round((total_fillers / word_count * 100), 1) if word_count > 0 else 0.0

    # WPM
    wpm, pace_diagnosis = calculate_speaking_rate(word_count, duration_sec)

    # Pauses
    if pauses is None:
        pauses = []
    
    total_pause_duration = sum(p.get("duration", 0.0) for p in pauses)
    pause_ratio = (total_pause_duration / duration_sec) if duration_sec > 0 else 0.0

    # Score & feedback
    score, feedback_points = compute_fluency_score(wpm, filler_pct, len(pauses), pause_ratio)

    return {
        "score": score,
        "word_count": word_count,
        "duration_seconds": round(duration_sec, 2),
        "wpm": wpm,
        "pace_diagnosis": pace_diagnosis,
        "total_fillers": total_fillers,
        "filler_percentage": filler_pct,
        "filler_breakdown": breakdown,
        "filler_occurrences": occurrences,
        "pause_count": len(pauses),
        "total_pause_seconds": round(total_pause_duration, 2),
        "pause_ratio": round(pause_ratio, 3),
        "feedback": feedback_points
    }
