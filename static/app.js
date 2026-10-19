/**
 * AI Interview Speech Quality Analyzer - Frontend JavaScript Controller
 * Pure PCM 16-bit WAV Audio Recording, Live Oscilloscope Visualizer,
 * Real-time Speech-to-Text streaming, REST API communication, and Chart.js radar.
 */

// Global State
let audioContext = null;
let micSource = null;
let scriptProcessor = null;
let analyser = null;
let pcmBuffers = [];
let isRecording = false;
let animationFrameId = null;
let recordStartTime = null;
let timerInterval = null;
let recordingDurationSec = 0;
let liveSpeechRecognition = null;
let liveSpokenText = "";
let selectedFile = null;
let radarChartInstance = null;

// Practice Interview Questions
const PRACTICE_QUESTIONS = [
    "Tell me about a challenging technical problem you solved recently, your approach, and the outcome.",
    "Describe a time when you disagreed with a colleague or team lead. How did you handle the situation?",
    "Why are you interested in this position, and how do your skills align with what our team needs?",
    "Can you explain the architecture of your most impactful software engineering project?",
    "How do you prioritize competing deadlines when multiple critical issues arise simultaneously?"
];
let currentQuestionIndex = 0;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    initVisualizerCanvas();
    setupDropZone();
    initSpeechRecognition();
});

// Switch Tabs
function switchTab(tab) {
    const tabs = ['mic', 'upload', 'text'];
    tabs.forEach(t => {
        document.getElementById(`tab-${t}`).classList.add('hidden');
        const btn = document.getElementById(`tab-${t}-btn`);
        btn.classList.remove('border-indigo-500', 'text-indigo-400', 'bg-slate-900/60');
        btn.classList.add('border-transparent', 'text-slate-400');
    });

    document.getElementById(`tab-${tab}`).classList.remove('hidden');
    const activeBtn = document.getElementById(`tab-${tab}-btn`);
    activeBtn.classList.remove('border-transparent', 'text-slate-400');
    activeBtn.classList.add('border-indigo-500', 'text-indigo-400', 'bg-slate-900/60');
}

// Next Practice Question
function nextQuestion() {
    currentQuestionIndex = (currentQuestionIndex + 1) % PRACTICE_QUESTIONS.length;
    document.getElementById('interview-question').innerText = `"${PRACTICE_QUESTIONS[currentQuestionIndex]}"`;
}

// ----------------------------------------------------
// PCM 16-bit WAV Recording via Web Audio API
// ----------------------------------------------------

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        // Initialize AudioContext
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const inputSampleRate = audioContext.sampleRate;
        micSource = audioContext.createMediaStreamSource(stream);

        // Setup Analyser for Waveform
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        micSource.connect(analyser);

        // Setup ScriptProcessor to capture raw PCM Float32 samples
        pcmBuffers = [];
        scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        scriptProcessor.onaudioprocess = (e) => {
            if (!isRecording) return;
            const channel = e.inputBuffer.getChannelData(0);
            pcmBuffers.push(new Float32Array(channel));
        };

        micSource.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        // UI Reset
        isRecording = true;
        document.getElementById('mic-status-overlay').classList.add('hidden');
        document.getElementById('recording-badge').classList.remove('hidden');
        document.getElementById('recording-badge').classList.add('inline-flex');
        document.getElementById('start-record-btn').disabled = true;
        document.getElementById('start-record-btn').classList.add('opacity-50', 'cursor-not-allowed');
        document.getElementById('stop-record-btn').disabled = false;
        document.getElementById('stop-record-btn').className = "flex-1 sm:flex-none px-6 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-rose-600/30";

        recordStartTime = Date.now();
        startTimer();

        // Start Oscilloscope animation
        drawOscilloscope();

        // Start Live Speech Recognition
        startSpeechRecognitionStream();

    } catch (err) {
        console.error("Microphone access error:", err);
        alert("Microphone Access Error: " + err.message + "\nPlease grant microphone permission in your browser or use the 'Direct Text Input' tab.");
    }
}

async function stopRecording() {
    if (!isRecording) return;
    isRecording = false;

    recordingDurationSec = (Date.now() - recordStartTime) / 1000.0;
    stopTimer();

    // Stop Speech Recognition
    stopSpeechRecognitionStream();

    // Stop visualizer animation
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }

    // Reset volume bar
    document.getElementById('volume-level-bar').style.width = '0%';
    document.getElementById('mic-status-text').innerText = "Processing...";

    // Disconnect audio nodes & close context
    const inputSampleRate = audioContext ? audioContext.sampleRate : 16000;
    if (scriptProcessor) {
        scriptProcessor.disconnect();
    }
    if (micSource) {
        micSource.mediaStream.getTracks().forEach(t => t.stop());
        micSource.disconnect();
    }

    // Generate PCM 16-bit WAV Blob
    const wavBlob = buildWavBlob(pcmBuffers, inputSampleRate, 16000);

    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
    }

    // Reset Buttons UI
    document.getElementById('recording-badge').classList.add('hidden');
    document.getElementById('recording-badge').classList.remove('inline-flex');
    document.getElementById('start-record-btn').disabled = false;
    document.getElementById('start-record-btn').classList.remove('opacity-50', 'cursor-not-allowed');
    document.getElementById('stop-record-btn').disabled = true;
    document.getElementById('stop-record-btn').className = "flex-1 sm:flex-none px-6 py-3 rounded-xl bg-slate-800 text-slate-500 font-semibold text-sm flex items-center justify-center gap-2 transition-all cursor-not-allowed";

    // Read current text in live-speech-box
    const userText = document.getElementById('live-speech-box').value.trim();

    // Submit for AI Analysis
    await submitAudioForAnalysis(wavBlob, recordingDurationSec, userText);
}

// ----------------------------------------------------
// PCM WAV Encoder Helper Functions
// ----------------------------------------------------

function buildWavBlob(buffers, inputRate, outputRate) {
    if (!buffers || buffers.length === 0) {
        return new Blob([], { type: 'audio/wav' });
    }

    // Flatten float buffers
    let totalLength = buffers.reduce((acc, b) => acc + b.length, 0);
    let merged = new Float32Array(totalLength);
    let offset = 0;
    for (let b of buffers) {
        merged.set(b, offset);
        offset += b.length;
    }

    // Resample if rates differ
    let samples = (inputRate === outputRate) ? merged : downsampleBuffer(merged, inputRate, outputRate);

    // Encode to 16-bit PCM RIFF WAV
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    function writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    /* RIFF identifier */
    writeString(view, 0, 'RIFF');
    /* file length */
    view.setUint32(4, 36 + samples.length * 2, true);
    /* RIFF type */
    writeString(view, 8, 'WAVE');
    /* format chunk identifier */
    writeString(view, 12, 'fmt ');
    /* format chunk length */
    view.setUint32(16, 16, true);
    /* sample format (raw PCM) */
    view.setUint16(20, 1, true);
    /* channel count (mono) */
    view.setUint16(22, 1, true);
    /* sample rate */
    view.setUint32(24, outputRate, true);
    /* byte rate */
    view.setUint32(28, outputRate * 2, true);
    /* block align */
    view.setUint16(32, 2, true);
    /* bits per sample */
    view.setUint16(34, 16, true);
    /* data chunk identifier */
    writeString(view, 36, 'data');
    /* data chunk length */
    view.setUint32(40, samples.length * 2, true);

    // Float to 16-bit signed integer PCM
    let byteOffset = 44;
    for (let i = 0; i < samples.length; i++, byteOffset += 2) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(byteOffset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([view], { type: 'audio/wav' });
}

function downsampleBuffer(buffer, inputRate, outputRate) {
    if (inputRate === outputRate) return buffer;
    const ratio = inputRate / outputRate;
    const newLength = Math.round(buffer.length / ratio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;
    while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
        let accum = 0, count = 0;
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
            accum += buffer[i];
            count++;
        }
        result[offsetResult] = count > 0 ? (accum / count) : 0;
        offsetResult++;
        offsetBuffer = nextOffsetBuffer;
    }
    return result;
}

// ----------------------------------------------------
// Live Oscilloscope & Audio Volume Monitor
// ----------------------------------------------------

function drawOscilloscope() {
    const canvas = document.getElementById('visualizer-canvas');
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function renderFrame() {
        if (!isRecording) return;
        animationFrameId = requestAnimationFrame(renderFrame);

        analyser.getByteTimeDomainData(dataArray);

        // Compute Volume RMS
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            const normalized = (dataArray[i] - 128) / 128;
            sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / bufferLength);
        const volumePercent = Math.min(100, Math.round(rms * 400));
        
        // Update volume bar in UI
        const volBar = document.getElementById('volume-level-bar');
        const statusText = document.getElementById('mic-status-text');
        if (volBar) volBar.style.width = `${volumePercent}%`;
        if (statusText) {
            statusText.innerText = volumePercent > 5 ? "Speaking..." : "Silent";
            statusText.className = volumePercent > 5 ? "text-[11px] text-emerald-400 font-semibold" : "text-[11px] text-slate-400";
        }

        // Draw Waveform
        ctx.fillStyle = '#020617';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.lineWidth = 2.5;
        ctx.strokeStyle = volumePercent > 5 ? '#818cf8' : '#475569';
        ctx.beginPath();

        const sliceWidth = canvas.width * 1.0 / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = v * (canvas.height / 2);

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            x += sliceWidth;
        }

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
    }

    renderFrame();
}

function initVisualizerCanvas() {
    const canvas = document.getElementById('visualizer-canvas');
    if (canvas) {
        canvas.width = canvas.parentElement.clientWidth || 600;
        canvas.height = canvas.parentElement.clientHeight || 128;
    }
}

// Timer Functions
function startTimer() {
    const display = document.getElementById('timer-display');
    let seconds = 0;
    display.innerText = "00:00";

    timerInterval = setInterval(() => {
        seconds++;
        const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
        const secs = String(seconds % 60).padStart(2, '0');
        display.innerText = `${mins}:${secs}`;
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

// ----------------------------------------------------
// Real-Time Speech Recognition Streaming (Web Speech API)
// ----------------------------------------------------

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        liveSpeechRecognition = new SpeechRecognition();
        liveSpeechRecognition.continuous = true;
        liveSpeechRecognition.interimResults = true;
        liveSpeechRecognition.lang = 'en-US';

        liveSpeechRecognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            if (finalTranscript) {
                liveSpokenText += " " + finalTranscript;
            }

            const current = (liveSpokenText + " " + interimTranscript).trim();
            const box = document.getElementById('live-speech-box');
            if (box && current) {
                box.value = current;
                box.scrollTop = box.scrollHeight;
            }
        };

        liveSpeechRecognition.onerror = (e) => {
            console.warn("[SpeechRecognition] event:", e.error);
        };
    }
}

function startSpeechRecognitionStream() {
    liveSpokenText = "";
    if (liveSpeechRecognition) {
        try {
            liveSpeechRecognition.start();
        } catch (e) {
            console.warn("SpeechRecognition already active or error:", e);
        }
    }
}

function stopSpeechRecognitionStream() {
    if (liveSpeechRecognition) {
        try {
            liveSpeechRecognition.stop();
        } catch (e) {}
    }
}

// ----------------------------------------------------
// File Upload & Direct Text Analysis
// ----------------------------------------------------

function setupDropZone() {
    const dropZone = document.getElementById('drop-zone');
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) handleSelectedFile(files[0]);
    });

    dropZone.addEventListener('click', () => {
        document.getElementById('audio-file-input').click();
    });
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleSelectedFile(e.target.files[0]);
    }
}

function handleSelectedFile(file) {
    selectedFile = file;
    document.getElementById('selected-file-info').classList.remove('hidden');
    document.getElementById('file-name').innerText = file.name;
    document.getElementById('file-size').innerText = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
}

async function analyzeUploadedFile() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('audio', selectedFile);
    formData.append('duration_seconds', 0);

    showLoading("Transcribing uploaded audio file with AI & evaluating metrics...");

    try {
        const response = await fetch('/api/analyze-audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Analysis failed');
        }

        const data = await response.json();
        renderResults(data);
    } catch (err) {
        alert("Audio Analysis Notice: " + err.message);
    } finally {
        hideLoading();
    }
}

async function analyzeDirectText() {
    const text = document.getElementById('direct-text-input').value.trim();
    const duration = parseFloat(document.getElementById('direct-duration-input').value) || 30.0;

    if (!text) {
        alert("Please enter or paste an interview response.");
        return;
    }

    showLoading("Running NLP evaluation on text response...");

    try {
        const response = await fetch('/api/analyze-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                duration_seconds: duration
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Analysis failed');
        }

        const data = await response.json();
        renderResults(data);
    } catch (err) {
        alert("NLP Error: " + err.message);
    } finally {
        hideLoading();
    }
}

// ----------------------------------------------------
// Submit Microphone Recording to Backend
// ----------------------------------------------------

async function submitAudioForAnalysis(audioBlob, durationSec, capturedText) {
    showLoading("Analyzing speech quality: Fluency, Grammar, and Vocabulary...");

    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('duration_seconds', Math.max(1, durationSec));
    if (capturedText) {
        formData.append('client_transcript', capturedText.trim());
    }

    try {
        const response = await fetch('/api/analyze-audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            // If empty speech, prompt user nicely to either speak or type
            if (response.status === 422) {
                alert("Notice: No spoken words were detected in the audio.\n\nPlease check your microphone volume or type your answer directly in the box.");
                document.getElementById('live-speech-box').focus();
                return;
            }
            throw new Error(err.detail || 'Analysis failed');
        }

        const data = await response.json();
        renderResults(data);
    } catch (err) {
        alert("Speech Analysis: " + err.message);
    } finally {
        hideLoading();
    }
}

// Loading UI
function showLoading(msg) {
    document.getElementById('loading-subtext').innerText = msg;
    document.getElementById('loading-state').classList.remove('hidden');
    document.getElementById('results-section').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading-state').classList.add('hidden');
}

// ----------------------------------------------------
// Render Results Dashboard
// ----------------------------------------------------

function renderResults(data) {
    document.getElementById('results-section').classList.remove('hidden');
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });

    // 1. Overall Score Ring & Badge
    const scoreVal = data.overall_score || 0;
    document.getElementById('overall-score-val').innerText = scoreVal;
    
    const ring = document.getElementById('score-ring');
    const offset = 289 - (289 * scoreVal / 100);
    ring.style.strokeDashoffset = offset;

    if (scoreVal >= 80) ring.setAttribute('class', 'text-emerald-500 transition-all duration-1000');
    else if (scoreVal >= 65) ring.setAttribute('class', 'text-indigo-500 transition-all duration-1000');
    else if (scoreVal >= 50) ring.setAttribute('class', 'text-amber-500 transition-all duration-1000');
    else ring.setAttribute('class', 'text-rose-500 transition-all duration-1000');

    document.getElementById('performance-tier-badge').innerText = data.performance_tier;
    document.getElementById('performance-summary').innerText = data.summary;

    // Header Quick Stats
    document.getElementById('stat-duration').innerText = `${data.duration_seconds}s`;
    document.getElementById('stat-words').innerText = data.fluency.word_count;
    document.getElementById('stat-wpm').innerText = `${data.fluency.wpm} WPM`;

    // 2. Fluency Card
    document.getElementById('fluency-score-badge').innerText = `${data.fluency.score}%`;
    document.getElementById('fluency-pace-label').innerText = data.fluency.pace_diagnosis;
    document.getElementById('fluency-fillers').innerText = `${data.fluency.total_fillers} (${data.fluency.filler_percentage}%)`;
    document.getElementById('fluency-pauses').innerText = data.fluency.pause_count;
    document.getElementById('fluency-feedback').innerHTML = data.fluency.feedback.join("<br>");

    // 3. Grammar Card
    document.getElementById('grammar-score-badge').innerText = `${data.grammar.score}%`;
    document.getElementById('grammar-error-count').innerText = data.grammar.error_count;
    document.getElementById('grammar-engine-name').innerText = data.grammar.engine_used;
    document.getElementById('grammar-accuracy-label').innerText = data.grammar.error_count === 0 ? "Flawless" : `${data.grammar.error_count} flagged`;
    document.getElementById('grammar-feedback').innerHTML = data.grammar.feedback.join("<br>");

    // 4. Vocabulary Card
    document.getElementById('vocab-score-badge').innerText = `${data.vocabulary.score}%`;
    document.getElementById('vocab-ttr').innerText = data.vocabulary.ttr;
    document.getElementById('vocab-power-count').innerText = data.vocabulary.professional_words.length;
    document.getElementById('vocab-readability').innerText = `${data.vocabulary.readability_level}`;
    document.getElementById('vocab-feedback').innerHTML = data.vocabulary.feedback.join("<br>");

    // 5. Strengths & Improvements
    const strengthsUl = document.getElementById('strengths-list');
    strengthsUl.innerHTML = "";
    data.strengths.forEach(s => {
        const li = document.createElement('li');
        li.className = "flex items-start gap-2";
        li.innerHTML = `<i class="fa-solid fa-check text-emerald-400 mt-1"></i> <span>${s}</span>`;
        strengthsUl.appendChild(li);
    });

    const improveUl = document.getElementById('improvements-list');
    improveUl.innerHTML = "";
    data.improvements.forEach(imp => {
        const li = document.createElement('li');
        li.className = "flex items-start gap-2";
        li.innerHTML = `<i class="fa-solid fa-arrow-right text-amber-400 mt-1"></i> <span>${imp}</span>`;
        improveUl.appendChild(li);
    });

    // 6. Highlighted Annotated Transcript
    renderAnnotatedTranscript(data.transcript, data.fluency.filler_breakdown, data.grammar.errors, data.vocabulary.professional_words);

    // 7. Grammar Diagnostics Table
    renderGrammarTable(data.grammar.errors);

    // 8. Competency Radar Chart
    renderRadarChart(data);
}

function renderAnnotatedTranscript(rawText, fillerBreakdown, grammarErrors, professionalWords) {
    const box = document.getElementById('annotated-transcript-box');
    if (!rawText) {
        box.innerHTML = "<span class='text-slate-500 italic'>No transcript text available.</span>";
        return;
    }

    let words = rawText.split(/\s+/);
    let htmlWords = words.map(word => {
        const clean = word.toLowerCase().replace(/[^a-z0-9]/g, '');

        if (professionalWords && professionalWords.includes(clean)) {
            return `<span class="hl-power" title="Professional Keyword: '${word}'">${word}</span>`;
        }

        if (fillerBreakdown && fillerBreakdown[clean]) {
            return `<span class="hl-filler" title="Filler Word: '${word}'">${word}</span>`;
        }

        return word;
    });

    box.innerHTML = htmlWords.join(" ");
}

function renderGrammarTable(errors) {
    const container = document.getElementById('grammar-table-container');
    const tbody = document.getElementById('grammar-errors-tbody');
    tbody.innerHTML = "";

    if (!errors || errors.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-slate-500 italic">No grammatical or syntax errors detected. Excellent!</td></tr>`;
        return;
    }

    errors.forEach(err => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-900/40 transition-colors";
        tr.innerHTML = `
            <td class="py-3 px-4 font-semibold text-rose-300">${err.type}</td>
            <td class="py-3 px-4 text-rose-400 font-mono bg-rose-950/20 rounded">${err.text}</td>
            <td class="py-3 px-4 text-slate-400">${err.explanation}</td>
            <td class="py-3 px-4 text-emerald-400 font-semibold">${err.suggestion || 'Rephrase sentence'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderRadarChart(data) {
    const ctx = document.getElementById('competency-radar-chart');
    if (!ctx) return;

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    const fluencyScore = data.fluency.score;
    const grammarScore = data.grammar.score;
    const vocabScore = data.vocabulary.score;
    const paceScore = Math.min(100, Math.max(30, 100 - Math.abs(140 - data.fluency.wpm)));
    const clarityScore = Math.max(30, 100 - (data.fluency.filler_percentage * 10));

    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Fluency', 'Grammar', 'Vocabulary', 'Speaking Pace', 'Vocal Clarity'],
            datasets: [
                {
                    label: 'Candidate Score',
                    data: [fluencyScore, grammarScore, vocabScore, paceScore, clarityScore],
                    backgroundColor: 'rgba(99, 102, 241, 0.25)',
                    borderColor: '#6366f1',
                    borderWidth: 2,
                    pointBackgroundColor: '#818cf8',
                    pointBorderColor: '#fff',
                    pointRadius: 4
                },
                {
                    label: 'Target Benchmark',
                    data: [85, 90, 80, 85, 90],
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: {
                        color: '#94a3b8',
                        font: { size: 10, family: 'Inter', weight: '600' }
                    },
                    ticks: { display: false, stepSize: 20 },
                    suggestedMin: 20,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#cbd5e1', font: { size: 11, family: 'Inter' } }
                }
            }
        }
    });
}

function resetAnalysis() {
    document.getElementById('results-section').classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
