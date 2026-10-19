"""
Evaluator Module
Synthesizes Fluency, Grammar, and Vocabulary dimensions into an overall interview score,
generates actionable recommendations, and annotates the transcript for visual highlighting.
Utilizes AI Linguistic Assessor (LLM) when available with deterministic NLP fallback.
"""

from typing import Dict, List, Any
from .fluency import analyze_fluency
from .grammar import analyze_grammar
from .vocabulary import analyze_vocabulary
from .ai_evaluator import evaluate_with_llm


def get_performance_tier(overall_score: int) -> Dict[str, str]:
    """
    Categorizes overall score into an actionable hiring readiness bracket.
    """
    if overall_score >= 88:
        return {
            "tier": "Elite / Interview Ready",
            "badge_color": "emerald",
            "summary": "Outstanding communication. Demonstrates high articulacy, grammatical precision, and natural pacing."
        }
    elif overall_score >= 75:
        return {
            "tier": "Strong / Hireable",
            "badge_color": "blue",
            "summary": "Solid verbal delivery. Communicates thoughts clearly with minor opportunities for vocabulary expansion."
        }
    elif overall_score >= 60:
        return {
            "tier": "Competent / Needs Polish",
            "badge_color": "yellow",
            "summary": "Decent baseline communication, but pacing inconsistency or repetitive phrasing diminishes impact."
        }
    else:
        return {
            "tier": "Needs Significant Practice",
            "badge_color": "red",
            "summary": "Communication requires structured practice, especially regarding filler words, pacing, and grammatical coherence."
        }


def generate_coaching_feedback(fluency_data: Dict[str, Any], grammar_data: Dict[str, Any], vocab_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Synthesizes clear strengths and actionable recommendations (Deterministic fallback).
    """
    strengths: List[str] = []
    improvements: List[str] = []

    # 1. Fluency diagnosis
    wpm = fluency_data.get("wpm", 0.0)
    filler_pct = fluency_data.get("filler_percentage", 0.0)
    total_fillers = fluency_data.get("total_fillers", 0)

    if 120 <= wpm <= 160:
        strengths.append(f"Ideal speaking tempo: Your speaking rate of {wpm} WPM is well-controlled and easy for interviewers to follow.")
    elif wpm > 160:
        improvements.append(f"Pacing is rapid ({wpm} WPM): Practice pausing between ideas. Speed can be perceived as nervousness.")
    elif 0 < wpm < 120:
        improvements.append(f"Pacing is slightly slow ({wpm} WPM): Increase vocal dynamism and momentum when narrating accomplishments.")

    if total_fillers == 0:
        strengths.append("Crisp vocal delivery: Zero filler words detected. Exceptional confidence.")
    elif filler_pct <= 2.5:
        strengths.append(f"Clean delivery: Minimal filler words ({total_fillers} total, {filler_pct}% density).")
    else:
        top_fillers = list(fluency_data.get("filler_breakdown", {}).keys())[:2]
        fillers_str = ", ".join([f"'{f}'" for f in top_fillers])
        improvements.append(f"Filler word reduction needed: {filler_pct}% of speech consisted of filler phrases ({fillers_str}). Practice replacing fillers with a silent breath.")

    # 2. Grammar diagnosis
    grammar_errors = grammar_data.get("errors", [])
    if len(grammar_errors) == 0:
        strengths.append("Impeccable syntax: Zero grammatical errors identified.")
    else:
        sample_error = grammar_errors[0]
        improvements.append(f"Grammar correction: Identified {len(grammar_errors)} error(s). E.g., {sample_error.get('explanation')}")

    # 3. Vocabulary diagnosis
    ttr = vocab_data.get("ttr", 0.0)
    prof_words = vocab_data.get("professional_words", [])
    reps = vocab_data.get("repetitive_words", [])

    if ttr >= 0.55:
        strengths.append(f"High lexical diversity (TTR: {ttr}): Demonstrates an expansive and articulate vocabulary.")
    
    if len(prof_words) >= 2:
        strengths.append(f"Professional impact verbs: Effectively used impactful keywords such as {', '.join(prof_words[:3])}.")
    else:
        improvements.append("Use the STAR method verbs: Incorporate action-oriented verbs like 'spearheaded', 'orchestrated', and 'optimized' to highlight your contributions.")

    if reps:
        rep_words_list = [f"'{r['word']}'" for r in reps[:2]]
        improvements.append(f"Word repetition: Frequently repeated {', '.join(rep_words_list)}. Diversify using contextual synonyms.")

    if not strengths:
        strengths.append("Good baseline delivery. Clear acoustic presence.")
    if not improvements:
        improvements.append("Maintain this level of composure under pressure interviews.")

    return {"strengths": strengths, "improvements": improvements}


def generate_annotated_transcript(
    text: str,
    filler_occurrences: List[Dict[str, Any]],
    grammar_errors: List[Dict[str, Any]],
    professional_words: List[str]
) -> List[Dict[str, Any]]:
    """
    Creates marked text segments for HTML visualization.
    """
    if not text:
        return []

    annotations: List[Dict[str, Any]] = []

    for f in filler_occurrences:
        annotations.append({
            "start": f["start"],
            "end": f["end"],
            "tag": "filler",
            "tooltip": f"Filler word: '{f['word']}'",
            "class": "bg-amber-100 text-amber-900 border-b-2 border-amber-400 font-medium px-1 rounded"
        })

    for g in grammar_errors:
        start_idx = g.get("start", text.find(g.get("text", "")))
        end_idx = g.get("end", start_idx + len(g.get("text", ""))) if start_idx != -1 else -1
        if start_idx != -1:
            annotations.append({
                "start": start_idx,
                "end": end_idx,
                "tag": "grammar",
                "tooltip": f"Grammar ({g.get('type')}): {g.get('explanation')} -> Suggestion: {g.get('suggestion', '')}",
                "class": "bg-rose-100 text-rose-900 border-b-2 border-rose-500 font-medium px-1 rounded"
            })

    return annotations


def evaluate_interview_response(
    text: str,
    duration_sec: float,
    pauses: List[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Master analysis function combining all NLP evaluation dimensions.
    """
    # 1. Fluency & Acoustics (Exact WPM, pause intervals, filler words)
    fluency = analyze_fluency(text, duration_sec, pauses)

    # 2. Grammar (Base Rule Engine)
    grammar = analyze_grammar(text)

    # 3. Vocabulary (Base Lexical Engine)
    vocabulary = analyze_vocabulary(text)

    # 4. Attempt State-of-the-art AI Evaluation
    llm_result = evaluate_with_llm(text)
    
    if llm_result:
        # Override with deep AI evaluation
        print("[Evaluator] Integrating contextual AI Linguistic Assessment...")
        grammar["score"] = int(llm_result.get("grammar_score", grammar["score"]))
        ai_errors = llm_result.get("grammar_errors", [])
        if ai_errors:
            grammar["errors"] = ai_errors
            grammar["error_count"] = len(ai_errors)
        grammar["engine_used"] = "AI Linguistic Assessor (GPT-OSS/Llama)"
        grammar["feedback"] = [f"Grammatical accuracy rated at {grammar['score']}%. Contextual syntax evaluated."]

        vocabulary["score"] = int(llm_result.get("vocabulary_score", vocabulary["score"]))
        vocabulary["readability_level"] = llm_result.get("vocabulary_level", vocabulary["readability_level"])
        ai_keywords = llm_result.get("professional_keywords", [])
        if ai_keywords:
            vocabulary["professional_words"] = list(set(vocabulary["professional_words"] + [w.lower() for w in ai_keywords]))
        
        strengths = llm_result.get("strengths", [])
        improvements = llm_result.get("improvements", [])
        summary_text = llm_result.get("executive_summary", "")
    else:
        # Fallback to deterministic NLP feedback
        coaching = generate_coaching_feedback(fluency, grammar, vocabulary)
        strengths = coaching["strengths"]
        improvements = coaching["improvements"]
        summary_text = ""

    # 5. Composite Overall Score (Weighted: 35% Fluency, 35% Grammar, 30% Vocabulary)
    overall_score = round(
        (fluency["score"] * 0.35) +
        (grammar["score"] * 0.35) +
        (vocabulary["score"] * 0.30)
    )
    overall_score = int(max(10, min(100, overall_score)))

    # Performance tier
    tier_info = get_performance_tier(overall_score)
    if summary_text:
        tier_info["summary"] = summary_text

    # Visual Annotations
    annotations = generate_annotated_transcript(
        text,
        fluency["filler_occurrences"],
        grammar["errors"],
        vocabulary["professional_words"]
    )

    return {
        "overall_score": overall_score,
        "performance_tier": tier_info["tier"],
        "badge_color": tier_info["badge_color"],
        "summary": tier_info["summary"],
        "transcript": text,
        "duration_seconds": round(duration_sec, 2),
        "fluency": fluency,
        "grammar": grammar,
        "vocabulary": vocabulary,
        "strengths": strengths,
        "improvements": improvements,
        "annotations": annotations
    }
