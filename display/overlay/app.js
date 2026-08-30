/**
 * app.js - WebSocket Client, Procedural Theme Canvas, & Malayalam Voice Engine
 */

// DOM Elements
const hpBarFill = document.getElementById('hp-bar-fill');
const hpValueText = document.getElementById('hp-value-text');
const timerText = document.getElementById('timer-text');
const scoreText = document.getElementById('score-text');
const comboText = document.getElementById('combo-text');

const titleScreen = document.getElementById('title-screen');
const incidentScreen = document.getElementById('incident-screen');
const gameOverScreen = document.getElementById('game-over-screen');

const crisisThemeBadge = document.getElementById('crisis-theme-badge');
const crisisTargetTool = document.getElementById('crisis-target-tool');
const crisisTimerBadge = document.getElementById('crisis-timer-badge');
const crisisTitle = document.getElementById('crisis-title');
const crisisDesc = document.getElementById('crisis-desc');
const malayalamText = document.getElementById('malayalam-text');

const finalScoreVal = document.getElementById('final-score-val');
const rankVal = document.getElementById('rank-val');
const shiftReviewText = document.getElementById('shift-review-text');

// Sensor Gauges
const gaugeMq3Val = document.getElementById('gauge-mq3-val');
const gaugeMq3Fill = document.getElementById('gauge-mq3-fill');
const gaugeLdrVal = document.getElementById('gauge-ldr-val');
const gaugeLdrFill = document.getElementById('gauge-ldr-fill');
const gaugeGateVal = document.getElementById('gauge-gate-val');
const gaugeGateFill = document.getElementById('gauge-gate-fill');
const gaugeMicVal = document.getElementById('gauge-mic-val');
const gaugeMicFill = document.getElementById('gauge-mic-fill');

// Keycaps
const keyB = document.getElementById('key-b');
const keyL = document.getElementById('key-l');
const keyG = document.getElementById('key-g');
const keyS = document.getElementById('key-s');

// Canvas Setup
const canvas = document.getElementById('theme-canvas');
const ctx = canvas.getContext('2d');
let currentTheme = 'FURNACE';
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// Particle System
class Particle {
  constructor(x, y, theme) {
    this.x = x || Math.random() * canvas.width;
    this.y = y || Math.random() * canvas.height;
    this.theme = theme;
    this.size = Math.random() * 4 + 2;
    this.speedX = (Math.random() - 0.5) * 2;
    this.speedY = Math.random() * -3 - 1;
    this.life = 1.0;
    this.decay = Math.random() * 0.015 + 0.005;
  }

  update() {
    this.x += this.speedX;
    this.y += this.speedY;
    this.life -= this.decay;
  }

  draw() {
    ctx.save();
    ctx.globalAlpha = Math.max(0, this.life);
    if (this.theme === 'FURNACE') {
      ctx.fillStyle = '#ff6600';
      ctx.shadowColor = '#ff3300';
      ctx.shadowBlur = 10;
    } else if (this.theme === 'SPIRIT') {
      ctx.fillStyle = '#00e5ff';
      ctx.shadowColor = '#00e5ff';
      ctx.shadowBlur = 8;
    } else if (this.theme === 'FLOOD') {
      ctx.fillStyle = '#00ffaa';
      ctx.shadowColor = '#0088ff';
      ctx.shadowBlur = 8;
    } else { // STORM
      ctx.fillStyle = '#ffd700';
      ctx.shadowColor = '#ffffff';
      ctx.shadowBlur = 12;
    }
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function animateCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Spawn theme particles
  if (particles.length < 90) {
    particles.push(new Particle(Math.random() * canvas.width, canvas.height + 10, currentTheme));
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.update();
    p.draw();
    if (p.life <= 0 || p.y < -20) {
      particles.splice(i, 1);
    }
  }

  requestAnimationFrame(animateCanvas);
}
animateCanvas();

// Malayalam Web Speech API Voice Engine
let lastSpokenText = '';
function speakMalayalam(text) {
  if (!text || text === lastSpokenText || !window.speechSynthesis) return;
  lastSpokenText = text;

  try {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ml-IN';
    utterance.rate = 1.05;
    utterance.pitch = 0.95;

    // Pick Malayalam voice if available
    const voices = window.speechSynthesis.getVoices();
    const mlVoice = voices.find(v => v.lang.includes('ml') || v.lang.includes('IN'));
    if (mlVoice) utterance.voice = mlVoice;

    window.speechSynthesis.speak(utterance);
  } catch (e) {
    console.warn('[WebSpeech Error]', e);
  }
}

// 🎙️ Live Browser-Side Malayalam Speech Recognition (STT)
const liveSttText = document.getElementById('live-stt-text');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
  try {
    recognition = new SpeechRecognition();
    recognition.lang = 'ml-IN';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript && transcript.trim()) {
        const cleanText = transcript.trim();
        liveSttText.textContent = `"${cleanText}"`;
        liveSttText.style.color = '#00ff88';
        keyS.classList.add('active');
        setTimeout(() => keyS.classList.remove('active'), 1200);

        // Send recognized speech to Python game engine
        fetch('/api/voice_action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ transcript: cleanText })
        }).catch(() => {});
      }
    };

    recognition.onerror = (e) => {
      // Fallback or retry
    };

    recognition.onend = () => {
      try { recognition.start(); } catch(e) {}
    };

    // Start recognition on user interaction or load
    window.addEventListener('click', () => {
      try { recognition.start(); } catch(e) {}
    }, { once: true });
    try { recognition.start(); } catch(e) {}
  } catch (err) {
    console.warn('[STT Init Notice]', err);
  }
}

// Native Server-Sent Events (SSE) & REST Telemetry Connection
let eventSource;
function connectLiveStream() {
  if (!!window.EventSource) {
    eventSource = new EventSource('/events');

    eventSource.onopen = () => {
      console.log('[SSE] Live stream connected to Maveli Display Server');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        updateDisplay(data);
      } catch (e) {
        console.warn('[SSE Parse Error]', e);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('[SSE Notice] Connection retry...');
    };
  } else {
    // Fallback: 30 Hz polling via /api/state
    setInterval(async () => {
      try {
        const res = await fetch('/api/state');
        if (res.ok) {
          const data = await res.json();
          updateDisplay(data);
        }
      } catch (e) {}
    }, 33);
  }
}

let previousIncidentTitle = '';

function updateDisplay(state) {
  // 1. Update Header Metrics
  const hp = Math.max(0, Math.min(100, state.stability_hp || 100));
  hpBarFill.style.width = `${hp}%`;
  hpValueText.textContent = `${Math.round(hp)}%`;

  if (hp > 50) {
    hpBarFill.style.background = 'linear-gradient(90deg, #00ff88, #ffd700)';
    hpValueText.style.color = '#00ff88';
  } else if (hp > 25) {
    hpBarFill.style.background = 'linear-gradient(90deg, #ff9900, #ff5500)';
    hpValueText.style.color = '#ff9900';
  } else {
    hpBarFill.style.background = 'linear-gradient(90deg, #ff2255, #cc0033)';
    hpValueText.style.color = '#ff2255';
  }

  timerText.textContent = `${(state.time_left || 0).toFixed(1)}s`;
  scoreText.textContent = String(state.score || 0).padStart(5, '0');
  comboText.textContent = `${state.combo || 1}x`;

  // 2. Manage Screen State Transitions
  if (state.state === 'IDLE') {
    titleScreen.classList.remove('hidden');
    incidentScreen.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
  } else if (state.state === 'GAME_OVER') {
    titleScreen.classList.add('hidden');
    incidentScreen.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');

    finalScoreVal.textContent = String(state.score || 0).padStart(5, '0');
    const rank = (state.score >= 800) ? '👑 Emperor of the Underworld' :
                 (state.score >= 500) ? '⚡ Pātāḷam High Commander' :
                 (state.score >= 250) ? '🛡️ Royal Gate Sentinel' : '🔰 Trainee Guard';
    rankVal.textContent = rank;
    if (state.shift_review) shiftReviewText.textContent = state.shift_review;
  } else { // PLAYING or SUCCESS
    titleScreen.classList.add('hidden');
    incidentScreen.classList.remove('hidden');
    gameOverScreen.classList.add('hidden');

    if (state.active_incident) {
      const inc = state.active_incident;
      currentTheme = inc.visual_theme || 'FURNACE';
      crisisThemeBadge.textContent = `THEME: ${currentTheme}`;
      crisisTargetTool.textContent = `ACTION: ${inc.target_tool}`;
      if (state.reaction_text) {
        malayalamText.textContent = `"${state.reaction_text}"`;
        speakMalayalam(state.reaction_text);
      } else {
        malayalamText.textContent = `"${inc.malayalam_alert}"`;
        // Trigger Malayalam voice when a new crisis arrives
        if (inc.incident_title !== previousIncidentTitle) {
          previousIncidentTitle = inc.incident_title;
          speakMalayalam(inc.malayalam_alert);
        }
      }
    }
  }

  // 3. Update Hardware Sensor Gauges
  const s = state.sensors || {};
  const mq3Val = s.raw_mq3 || (s.is_blowing ? 2500 : 500);
  gaugeMq3Val.textContent = mq3Val;
  gaugeMq3Fill.style.width = `${Math.min(100, (mq3Val / 3500) * 100)}%`;

  const ldrPct = s.light_pct !== undefined ? s.light_pct : 65;
  gaugeLdrVal.textContent = `${Math.round(ldrPct)}%`;
  gaugeLdrFill.style.width = `${ldrPct}%`;

  const gateAngle = s.gate_angle !== undefined ? s.gate_angle : 15;
  gaugeGateVal.textContent = `${gateAngle.toFixed(1)}°`;
  gaugeGateFill.style.width = `${(gateAngle / 180) * 100}%`;

  const micActive = s.is_voice_active;
  gaugeMicVal.textContent = micActive ? 'SHOUT DETECTED!' : 'IDLE';
  gaugeMicFill.style.width = micActive ? '100%' : '15%';

  // 4. Update Keycap Indicators
  keyB.classList.toggle('active', s.is_blowing);
  keyL.classList.toggle('active', ldrPct < 25);
  keyG.classList.toggle('active', gateAngle > 65);
  keyS.classList.toggle('active', micActive);
}

// Keyboard shortcuts for direct interaction & testing
window.addEventListener('keydown', (e) => {
  const key = e.key.toUpperCase();
  if (e.code === 'Space') {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ event: 'START_BUTTON' }));
    }
  }
});

// Initialize on page load
connectLiveStream();
