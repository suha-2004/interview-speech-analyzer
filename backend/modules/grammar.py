"""
Grammar and Syntax Analyzer Module
Detects grammatical errors, structural mistakes, spoken agreement issues,
and provides actionable corrections.
"""

import re
from typing import Dict, List, Any, Tuple

# Common grammatical error patterns in spoken English / interviews
GRAMMAR_RULES = [
    # Subject-verb agreement
    {
        "pattern": r"\b(he|she|it)\s+(have|do|are|were)\b",
        "type": "Subject-Verb Agreement",
        "message": "Singular third-person subject should be paired with singular verb.",
        "replacement_map": {
            "have": "has",
            "do": "does",
            "are": "is",
            "were": "was"
        }
    },
    {
        "pattern": r"\b(they|we|you)\s+(is|was|has|does)\b",
        "type": "Subject-Verb Agreement",
        "message": "Plural subject requires a plural verb form.",
        "replacement_map": {
            "is": "are",
            "was": "were",
            "has": "have",
            "does": "do"
        }
    },
    {
        "pattern": r"\b(i)\s+(is|are|has|were)\b",
        "type": "Subject-Verb Agreement",
        "message": "First-person singular 'I' should use 'am', 'have', or 'was'.",
        "replacement_map": {
            "is": "am",
            "are": "am",
            "has": "have",
            "were": "was"
        }
    },
    # Common spoken verb tense mistakes
    {
        "pattern": r"\b(could|should|would|must)\s+of\b",
        "type": "Incorrect Modal Verb Preposition",
        "message": "Spoken 'could of' / 'should of' is grammatically 'could have' / 'should have'.",
        "replacement_func": lambda m: m.group(1) + " have"
    },
    {
        "pattern": r"\b(did|didn't|did not)\s+(went|saw|came|took|spoke|wrote|done)\b",
        "type": "Double Past Tense / Auxiliary Error",
        "message": "Auxiliary 'did' must be followed by base form of verb.",
        "replacement_map": {
            "went": "go",
            "saw": "see",
            "came": "come",
            "took": "take",
            "spoke": "speak",
            "wrote": "write",
            "done": "do"
        }
    },
    {
        "pattern": r"\b(i|we|they|he|she)\s+(seen)\b",
        "type": "Past Participle Misuse",
        "message": "Use past tense 'saw' or perfect tense 'have seen'.",
        "replacement_func": lambda m: m.group(1) + " saw"
    },
    # Double negatives
    {
        "pattern": r"\b(don't|doesn't|didn't|cannot|can't|won't)\s+have\s+no\b",
        "type": "Double Negative",
        "message": "Double negative creates ambiguity in professional interviews. Use 'any' instead of 'no'.",
        "replacement_func": lambda m: m.group(1) + " have any"
    },
    {
        "pattern": r"\b(don't|doesn't|didn't|can't)\s+(know|see|find)\s+nothing\b",
        "type": "Double Negative",
        "message": "Double negative detected. Replace 'nothing' with 'anything'.",
        "replacement_func": lambda m: m.group(1) + " " + m.group(2) + " anything"
    },
    # Spoken stutter / Repeated adjacent words
    {
        "pattern": r"\b(\w+)\s+\1\b",
        "type": "Repeated Word / Hesitation",
        "message": "Consecutive repeated word detected.",
        "replacement_func": lambda m: m.group(1)
    }
]


def check_rule_based_grammar(text: str) -> List[Dict[str, Any]]:
    """
    Evaluates transcript against rule-based syntactic and grammatical patterns.
    """
    errors: List[Dict[str, Any]] = []
    
    for rule in GRAMMAR_RULES:
        for match in re.finditer(rule["pattern"], text, re.IGNORECASE):
            matched_str = match.group(0)
            
            # Determine suggestion
            suggestion = ""
            if "replacement_func" in rule:
                suggestion = rule["replacement_func"](match)
            elif "replacement_map" in rule:
                verb_part = match.group(2).lower() if len(match.groups()) >= 2 else ""
                repl = rule["replacement_map"].get(verb_part, "")
                if repl:
                    suggestion = match.group(1) + " " + repl
                else:
                    suggestion = matched_str
            
            errors.append({
                "type": rule["type"],
                "text": matched_str,
                "start": match.start(),
                "end": match.end(),
                "explanation": rule["message"],
                "suggestion": suggestion
            })
            
    # Check for run-on sentences (sentences with > 38 words without a comma or period)
    sentences = re.split(r"[.!?]+", text)
    for s in sentences:
        s_clean = s.strip()
        word_count = len(s_clean.split())
        if word_count > 38:
            errors.append({
                "type": "Run-on Sentence",
                "text": s_clean[:60] + "...",
                "start": text.find(s_clean),
                "end": text.find(s_clean) + len(s_clean),
                "explanation": f"Sentence is {word_count} words long without clear sentence boundaries. Break long thoughts into shorter, punchy sentences.",
                "suggestion": "Split into 2-3 focused sentences using transition words (e.g. 'Furthermore', 'Consequently')."
            })

    return errors


def compute_grammar_score(error_count: int, total_words: int) -> Tuple[int, List[str]]:
    """
    Computes a 0-100 grammar score based on error frequency per 100 words.
    """
    if total_words == 0:
        return 50, ["No text to evaluate grammar."]
    
    # Calculate error rate per 100 words
    error_rate = (error_count / total_words) * 100
    
    # Base score
    score = 100.0 - (error_rate * 12.0)
    feedback = []

    if error_count == 0:
        feedback.append("Flawless grammar! No grammatical errors or syntax violations detected.")
    elif error_count <= 2:
        feedback.append("Strong grammatical accuracy. Minor phrasing improvements recommended.")
    elif error_count <= 5:
        feedback.append("Moderate grammar issues detected. Review subject-verb agreement and sentence structure.")
    else:
        feedback.append("Significant grammar errors found. Frequent syntax mistakes undermine professional credibility.")

    final_score = int(max(20.0, min(100.0, round(score))))
    return final_score, feedback


def analyze_grammar(text: str) -> Dict[str, Any]:
    """
    Analyzes grammatical correctness of the transcript.
    Optionally attempts LanguageTool if available, otherwise uses internal NLP engine.
    """
    words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
    total_words = len(words)
    
    errors: List[Dict[str, Any]] = []

    # Attempt language_tool_python if installed
    lt_used = False
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(text)
        for m in matches:
            errors.append({
                "type": m.category,
                "text": text[m.offset:m.offset + m.errorLength],
                "start": m.offset,
                "end": m.offset + m.errorLength,
                "explanation": m.message,
                "suggestion": m.replacements[0] if m.replacements else ""
            })
        lt_used = True
    except Exception:
        # Fall back to custom high-precision rule engine
        errors = check_rule_based_grammar(text)

    # Calculate grammar score
    score, feedback = compute_grammar_score(len(errors), total_words)

    return {
        "score": score,
        "error_count": len(errors),
        "errors": errors,
        "feedback": feedback,
        "engine_used": "LanguageTool" if lt_used else "NLP Rule Engine"
    }
