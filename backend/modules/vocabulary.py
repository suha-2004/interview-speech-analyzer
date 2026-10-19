"""
Vocabulary & Lexical Richness Analyzer Module
Measures Lexical Diversity (TTR), Professional Action Verbs,
Repetitive Words, Readability Grade, and Vocabulary Score.
"""

import re
import math
from typing import Dict, List, Any, Tuple
from collections import Counter

# Standard English stopwords to filter out when checking for word repetition
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did",
    "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each",
    "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's",
    "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of",
    "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their",
    "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves"
}

# High-impact professional interview action verbs and vocabulary
PROFESSIONAL_KEYWORDS = {
    # Engineering & Technical
    "architected", "engineered", "developed", "deployed", "implemented", "optimized",
    "automated", "integrated", "refactored", "debugged", "designed", "benchmarked",
    # Leadership & Collaboration
    "spearheaded", "orchestrated", "collaborated", "facilitated", "mentored",
    "coordinated", "delegated", "aligned", "negotiated", "championed",
    # Problem Solving & Analysis
    "analyzed", "diagnosed", "synthesized", "formulated", "evaluated", "identified",
    "streamlined", "pioneered", "enhanced", "resolved", "mitigated", "quantified",
    # Results & Impact
    "achieved", "delivered", "executed", "accelerated", "exceeded", "generated",
    "maximized", "transformed", "boosted", "scaled", "strengthened", "standardized"
}


def count_syllables(word: str) -> int:
    """
    Estimates syllable count using vowel grouping heuristics.
    """
    word = word.lower()
    if len(word) <= 3:
        return 1
    # Remove trailing 'e'
    if word.endswith('e') and not word.endswith('le'):
        word = word[:-1]
    vowels = re.findall(r'[aeiouy]+', word)
    return max(1, len(vowels))


def calculate_readability(text: str, total_words: int) -> Tuple[float, str]:
    """
    Computes Flesch-Kincaid Grade Level score for the transcript.
    """
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    num_sentences = max(1, len(sentences))

    words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
    if not words:
        return 0.0, "N/A"

    total_syllables = sum(count_syllables(w) for w in words)
    
    # Flesch-Kincaid Grade Level formula
    fkgl = (0.39 * (total_words / num_sentences)) + (11.8 * (total_syllables / total_words)) - 15.59
    fkgl = round(max(1.0, min(18.0, fkgl)), 1)

    if fkgl <= 6:
        level = "Elementary (Basic vocabulary)"
    elif 7 <= fkgl <= 9:
        level = "Conversational (Easy to follow)"
    elif 10 <= fkgl <= 13:
        level = "Professional (Ideal for interviews)"
    else:
        level = "Advanced / Academic (High complexity)"

    return fkgl, level


def analyze_vocabulary(text: str) -> Dict[str, Any]:
    """
    Evaluates lexical diversity, repetition, and professional language usage.
    """
    raw_words = re.findall(r"\b[A-Za-z'-]+\b", text.lower())
    total_words = len(raw_words)

    if total_words == 0:
        return {
            "score": 50,
            "total_words": 0,
            "unique_words": 0,
            "ttr": 0.0,
            "professional_words": [],
            "repetitive_words": [],
            "readability_grade": 0,
            "readability_level": "No speech",
            "feedback": ["No words available to analyze vocabulary."]
        }

    unique_words = len(set(raw_words))
    # Type-Token Ratio (Lexical Diversity)
    ttr = round(unique_words / total_words, 3)

    # Detect high-impact professional words
    professional_found = [w for w in set(raw_words) if w in PROFESSIONAL_KEYWORDS]

    # Detect overused non-stop words
    content_words = [w for w in raw_words if w not in STOPWORDS and len(w) > 2]
    word_freq = Counter(content_words)
    
    # Flag words used more than 3 times and representing > 3% of content
    repetitive_words = []
    for word, count in word_freq.most_common(5):
        if count >= 3 and (count / len(content_words)) >= 0.04:
            repetitive_words.append({"word": word, "count": count})

    # Readability
    readability_grade, readability_level = calculate_readability(text, total_words)

    # Compute Vocabulary Score (0 - 100)
    score = 100.0
    feedback = []

    # 1. Diversity assessment
    if ttr >= 0.60:
        feedback.append("Excellent lexical diversity! You express ideas with a varied, non-repetitive vocabulary.")
    elif ttr >= 0.45:
        score -= 5
        feedback.append("Good vocabulary variety. Try incorporating more descriptive technical synonyms.")
    else:
        score -= 20
        feedback.append("Low lexical diversity. You tend to repeat similar basic phrases.")

    # 2. Professional keyword presence
    if len(professional_found) >= 3:
        feedback.append(f"Great use of {len(professional_found)} high-impact action verbs ({', '.join(professional_found[:4])}).")
    elif len(professional_found) >= 1:
        feedback.append(f"Included professional terminology: {', '.join(professional_found)}.")
    else:
        score -= 10
        feedback.append("Tip: Use more strong action verbs (e.g., 'implemented', 'optimized', 'collaborated') to showcase impact.")

    # 3. Repetition penalty
    if repetitive_words:
        score -= min(15, len(repetitive_words) * 5)
        top_reps = [f"'{r['word']}' ({r['count']}x)" for r in repetitive_words[:3]]
        feedback.append(f"Overused non-filler words: {', '.join(top_reps)}. Consider using synonyms.")

    final_score = int(max(20.0, min(100.0, round(score))))

    return {
        "score": final_score,
        "total_words": total_words,
        "unique_words": unique_words,
        "ttr": ttr,
        "professional_words": professional_found,
        "repetitive_words": repetitive_words,
        "readability_grade": readability_grade,
        "readability_level": readability_level,
        "feedback": feedback
    }
