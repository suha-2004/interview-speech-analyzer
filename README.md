# AI Interview Speech Quality Analyzer (VerbaIQ)

An end-to-end AI & NLP Capstone / Final Year Project that records and analyzes spoken interview answers in real-time, converting speech to text and evaluating **Fluency**, **Grammar**, **Vocabulary Richness**, and providing **Actionable Coaching Feedback**.

---

## 🌟 Key Features

1. **Live Microphone Recording & Oscilloscope Waveform**:
   - Captures live microphone audio using browser **Web Audio API** and `MediaRecorder`.
   - Real-time animated canvas waveform visualizer and interview timer.
   - Live speech streaming preview box using Web Speech API.

2. **Automated Speech-to-Text (STT)**:
   - Integration with OpenAI **Whisper** (Local ASR model) with timestamp-level segmentation and pause detection.
   - Built-in graceful fallbacks for zero-latency execution.

3. **Speech Fluency & Pacing Engine**:
   - Calculates **Words Per Minute (WPM)** and diagnoses speaking rate against optimal interview pacing ($120 - 160\text{ WPM}$).
   - Detects single-word and multi-word filler phrases (*"um"*, *"uh"*, *"you know"*, *"like"*, *"basically"*, *"sort of"*, etc.).
   - Computes silent pause ratios and hesitation metrics.

4. **Grammar & Syntax Verification Engine**:
   - Detects spoken grammatical mistakes: Subject-Verb agreement, double negatives, tense discrepancies, modal errors (*"could of"*), and run-on sentences.
   - Generates exact error locations, linguistic explanations, and suggested replacements.

5. **Vocabulary & Lexical Richness Engine**:
   - Computes **Lexical Diversity (Type-Token Ratio - TTR)**.
   - Detects high-impact professional interview action verbs (*"spearheaded"*, *"orchestrated"*, *"optimized"*, *"implemented"*).
   - Identifies overused, repetitive non-stop words.
   - Estimates **Flesch-Kincaid Grade Level** readability.

6. **Interactive Visual Dashboard**:
   - Animated Circular Overall Score Gauge (0 - 100).
   - **Chart.js Radar Chart** benchmarking candidate vs. target interview standard.
   - Color-coded Annotated Transcript (Yellow: Fillers, Red: Grammar, Green: Power verbs).
   - Structured diagnostic table for grammar corrections.
   - Bulleted list of Key Strengths and High-Priority Improvements.

---

## 🏗️ System Architecture

```text
[ Browser / Microphone ]
         │ (Web Audio API / MediaRecorder)
         ▼
[ FastAPI Backend: POST /api/analyze-audio ]
         │
         ├───► [ Speech-to-Text (ASR) Module ] ───► Transcribed Text & Pauses
         │
         ├───► [ Fluency Analyzer ] ─────────────► WPM, Filler Ratio, Pause Metrics
         │
         ├───► [ Grammar Analyzer ] ─────────────► Syntax Errors, Explanations & Fixes
         │
         ├───► [ Vocabulary Analyzer ] ──────────► TTR, Action Verbs, Readability
         │
         └───► [ Master Evaluator ] ─────────────► Composite 0-100 Score, Tier, Radar Data
                     │
                     ▼
       [ Interactive Modern Dashboard UI ]
```

---

## 📐 Mathematical & NLP Formulations

### 1. Speaking Rate (Words Per Minute)
$$\text{WPM} = \frac{\text{Total Spoken Words}}{\text{Duration in Minutes}}$$
- *Ideal Interview Pace:* $120 \le \text{WPM} \le 160$

### 2. Filler Word Density
$$\text{Filler Percentage} = \left(\frac{\text{Total Filler Words}}{\text{Total Spoken Words}}\right) \times 100\%$$

### 3. Lexical Diversity (Type-Token Ratio)
$$\text{TTR} = \frac{V}{N}$$
Where:
- $V = \text{Count of unique vocabulary words}$
- $N = \text{Total word tokens}$

### 4. Readability (Flesch-Kincaid Grade Level)
$$\text{FKGL} = 0.39 \left(\frac{\text{Total Words}}{\text{Total Sentences}}\right) + 11.8 \left(\frac{\text{Total Syllables}}{\text{Total Words}}\right) - 15.59$$

### 5. Composite Interview Readiness Score
$$\text{Overall Score} = 0.35 \times \text{Fluency} + 0.35 \times \text{Grammar} + 0.30 \times \text{Vocabulary}$$

---

## 🚀 Step-by-Step Setup in VS Code

### Step 1: Open VS Code
1. Open **Visual Studio Code**.
2. Go to **File -> Open Folder...** and select this project directory:
   ```text
   interview-speech-analyzer
   ```

### Step 2: Open VS Code Integrated Terminal
- Press ``Ctrl + ` `` (Backtick) or go to **Terminal -> New Terminal**.

### Step 3: Create & Activate a Python Virtual Environment
In the terminal, run:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment on Windows
.\venv\Scripts\Activate.ps1
```
*(If PowerShell shows execution policy restrictions, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Run the Application
Execute:
```powershell
python run.py
```
Or double-click `run.bat` in File Explorer.

### Step 6: Open the Web Application
Open your browser (Chrome, Edge, or Firefox) and navigate to:
```text
http://localhost:8000
```
- Click **"Allow"** when prompted for microphone access.
- Click **"Start Recording"**, answer the practice question, and click **"Stop & Analyze"**!

---

## 📂 Project Directory Structure

```text
interview-speech-analyzer/
├── backend/
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── speech_to_text.py   # Audio transcription and pause detection
│   │   ├── fluency.py          # WPM, pause analysis, filler word metrics
│   │   ├── grammar.py          # Grammar error detection, explanations, fixes
│   │   ├── vocabulary.py       # TTR, advanced vocab, repetitive words, readability
│   │   └── evaluator.py        # Aggregate scoring & detailed feedback report
│   ├── app.py                  # FastAPI backend server & API routes
├── static/
│   ├── index.html              # Modern glassmorphism dashboard UI
│   ├── app.js                  # Web Audio API recording, visualizer, API calls, charts
│   └── style.css               # Custom styles, badges, and animations
├── uploads/                    # Directory for temporary audio recordings
├── requirements.txt            # Python package dependencies
├── run.py                      # One-click Python server launcher
├── run.bat                     # Windows batch launcher
└── README.md                   # Complete documentation
```

---

## 🎓 Viva / Project Defense Questions

1. **Q: Why is Whisper chosen over traditional HMM-based speech recognition?**
   - **A:** Whisper is an end-to-end encoder-decoder Transformer trained on 680,000 hours of multilingual, diverse audio data, providing exceptional robustness against accents, background noise, and colloquial speech.

2. **Q: How does the system compute pauses without video?**
   - **A:** By analyzing the timestamps of the transcribed word segments from Whisper and identifying silent intervals exceeding 1.0 second, or analyzing acoustic energy silence thresholds via the Web Audio API.

3. **Q: Why is Type-Token Ratio (TTR) significant in speech evaluation?**
   - **A:** TTR measures lexical diversity. A candidate with higher TTR uses varied, descriptive vocabulary, which correlates strongly with cognitive clarity and domain competence.
