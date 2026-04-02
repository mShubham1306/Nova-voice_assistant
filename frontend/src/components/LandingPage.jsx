import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';

/* ═══════════════════════════════════════════
   Scroll-triggered reveal
   ═══════════════════════════════════════════ */
function useScrollReveal(opts = {}) {
  const ref = useRef(null);
  const [vis, setVis] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVis(true); },
      { threshold: opts.threshold || 0.12 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, vis];
}

/* ═══════════════════════════════════════════
   PROFESSIONAL AI ORBS  — canvas-based
   ═══════════════════════════════════════════ */
function AIOrb({ state }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);
  const t = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const SIZE = 300;
    canvas.width = SIZE;
    canvas.height = SIZE;
    const cx = SIZE / 2, cy = SIZE / 2;

    const isActive = state !== 'idle';
    const isListening = state === 'listening';
    const isSpeaking  = state === 'speaking';
    const isProc      = state === 'processing';

    function draw() {
      t.current += 0.018;
      ctx.clearRect(0, 0, SIZE, SIZE);

      // ── Outer corona glow ──
      const numRings = 4;
      for (let i = numRings; i >= 1; i--) {
        const r = 120 + i * 12 + Math.sin(t.current * 0.7 + i) * (isActive ? 8 : 3);
        const alpha = 0.03 + (numRings - i) * 0.01;
        const grad = ctx.createRadialGradient(cx, cy, r - 4, cx, cy, r);
        grad.addColorStop(0, `rgba(180,0,0,${alpha})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      }

      // ── Rotating ring ──
      const ringSeg = 60;
      for (let i = 0; i < ringSeg; i++) {
        const angle = (Math.PI * 2 / ringSeg) * i + t.current * (isListening ? 1.5 : 0.6);
        const rx = cx + Math.cos(angle) * 108;
        const ry = cy + Math.sin(angle) * 108;
        const sz = isActive ? 2.5 + Math.sin(t.current * 3 + i * 0.3) * 1.5 : 1.2;
        const alpha = isActive ? 0.6 + Math.sin(t.current + i * 0.2) * 0.4 : 0.25;
        ctx.beginPath();
        ctx.arc(rx, ry, sz, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(220,30,30,${alpha})`;
        ctx.fill();
      }

      // ── Counter-rotating inner ring ──
      for (let i = 0; i < 30; i++) {
        const angle = (Math.PI * 2 / 30) * i - t.current * (isProc ? 2 : 0.9);
        const rx = cx + Math.cos(angle) * 80;
        const ry = cy + Math.sin(angle) * 80;
        const sz = 1.5 + Math.sin(t.current * 4 + i * 0.5) * (isActive ? 1 : 0.3);
        const alpha = isActive ? 0.8 : 0.3;
        ctx.beginPath();
        ctx.arc(rx, ry, sz, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,80,80,${alpha})`;
        ctx.fill();
      }

      // ── Core sphere ──
      const coreGrad = ctx.createRadialGradient(cx - 18, cy - 18, 5, cx, cy, 60);
      coreGrad.addColorStop(0, isListening ? '#ff6666' : (isSpeaking ? '#ff3333' : '#cc1111'));
      coreGrad.addColorStop(0.4, '#880000');
      coreGrad.addColorStop(1, '#330000');
      ctx.beginPath();
      ctx.arc(cx, cy, 60, 0, Math.PI * 2);
      ctx.fillStyle = coreGrad;
      ctx.fill();

      // ── Specular highlight ──
      const hiGrad = ctx.createRadialGradient(cx - 20, cy - 20, 1, cx - 15, cy - 15, 28);
      hiGrad.addColorStop(0, 'rgba(255,255,255,0.35)');
      hiGrad.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.beginPath();
      ctx.arc(cx, cy, 60, 0, Math.PI * 2);
      ctx.fillStyle = hiGrad;
      ctx.fill();

      // ── Processing arc ──
      if (isProc) {
        ctx.beginPath();
        ctx.arc(cx, cy, 68, t.current * 3, t.current * 3 + Math.PI * 1.2);
        ctx.strokeStyle = 'rgba(255,100,100,0.8)';
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.stroke();
      }

      // ── Listening wave bars ──
      if (isListening || isSpeaking) {
        for (let i = 0; i < 16; i++) {
          const angle = (Math.PI * 2 / 16) * i;
          const base = 70, h = 12 + Math.abs(Math.sin(t.current * 4 + i * 0.8)) * 20;
          const x1 = cx + Math.cos(angle) * base;
          const y1 = cy + Math.sin(angle) * base;
          const x2 = cx + Math.cos(angle) * (base + h);
          const y2 = cy + Math.sin(angle) * (base + h);
          ctx.beginPath();
          ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
          ctx.strokeStyle = `rgba(255,80,80,0.7)`;
          ctx.lineWidth = 2.5;
          ctx.lineCap = 'round';
          ctx.stroke();
        }
      }

      animRef.current = requestAnimationFrame(draw);
    }
    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [state]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: 300, height: 300, display: 'block', borderRadius: '50%' }}
    />
  );
}

/* ═══════════════════════════════════════════
   Typewriter text
   ═══════════════════════════════════════════ */
function Typewriter({ phrases }) {
  const [idx, setIdx] = useState(0);
  const [text, setText] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const phrase = phrases[idx];
    let timeout;
    if (!deleting && text === phrase) {
      timeout = setTimeout(() => setDeleting(true), 2200);
    } else if (deleting && text === '') {
      setDeleting(false);
      setIdx(i => (i + 1) % phrases.length);
    } else {
      const speed = deleting ? 35 : 65;
      timeout = setTimeout(() => {
        setText(prev => deleting ? prev.slice(0, -1) : phrase.slice(0, prev.length + 1));
      }, speed);
    }
    return () => clearTimeout(timeout);
  }, [text, deleting, idx, phrases]);

  return <span className="tw-text">{text}<span className="tw-cursor">|</span></span>;
}

/* ═══════════════════════════════════════════
   Stats counter
   ═══════════════════════════════════════════ */
function CountUp({ end, suffix = '', duration = 1800 }) {
  const [val, setVal] = useState(0);
  const [started, setStarted] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !started) setStarted(true);
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  useEffect(() => {
    if (!started) return;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(ease * end));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [started]);
  return <span ref={ref}>{val}{suffix}</span>;
}

/* ═══════════════════════════════════════════
   MAIN LANDING PAGE
   ═══════════════════════════════════════════ */
export default function LandingPage({ voiceState, isRunning, backendOnline, onToggleAssistant, onSendCommand, onOpenAssistant }) {
  const [scrollY, setScrollY] = useState(0);
  const [headerSolid, setHeaderSolid] = useState(false);
  const [progress, setProgress] = useState(0);
  const [cmdInput, setCmdInput] = useState('');
  const [cmdHistory, setCmdHistory] = useState([
    { role: 'nova', text: 'Hello! I\'m Nova. How can I assist you today?' }
  ]);
  const [typing, setTyping] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      const el = document.documentElement;
      const st = el.scrollTop;
      const sh = el.scrollHeight - el.clientHeight;
      setScrollY(st);
      setHeaderSolid(st > 60);
      setProgress(sh > 0 ? (st / sh) * 100 : 0);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const [heroRef, heroVis]     = useScrollReveal({ threshold: 0.05 });
  const [featRef, featVis]     = useScrollReveal();
  const [statsRef, statsVis]   = useScrollReveal();
  const [demoRef, demoVis]     = useScrollReveal();
  const [howRef, howVis]       = useScrollReveal();
  const [ctaRef, ctaVis]       = useScrollReveal({ threshold: 0.3 });

  const typewriterPhrases = useMemo(() => [
    '"Open Chrome and search for weather"',
    '"बैटरी कितनी बची है?" (Hindi)',
    '"Play lo-fi music on Spotify"',
    '"Screenshot and save as PNG"',
    '"Nova, what is quantum entanglement?"',
    '"Search YouTube for React tutorials"',
    '"Mute my microphone"',
    '"Set a timer for 25 minutes"',
  ], []);

  const features = useMemo(() => [
    { icon: '🧠', label: 'AI', title: 'Gemini-Powered Intelligence', desc: 'Deep reasoning, creative answers, code generation, drafting emails — Nova doesn\'t just execute, it understands context the way a human would and reasons through complex multi-step requests.' },
    { icon: '🤫', label: 'PRIVATE', title: 'Always-On, Zero Latency', desc: 'Nova runs locally on your machine. No cloud roundtrips, no subscription fees. Your voice data never leaves your device, ensuring complete privacy and ultra-fast sub-200ms responses.' },
    { icon: '🌐', label: 'MULTILINGUAL', title: '40+ Languages Natively', desc: 'Speak in Hindi, Gujarati, Tamil, French, German, or any of 40+ languages. Nova auto-detects the language and responds in the same tongue — even switching mid-command.' },
    { icon: '⚙️', label: 'SYSTEM', title: 'Deep OS Integration', desc: 'Launch any app, adjust volume levels, capture screenshots, query battery status, retrieve your IP address, toggle dark mode, and lock your workstation — all voice-driven.' },
    { icon: '🌐', label: 'WEB', title: 'Instant Web Intelligence', desc: 'Skip slow browser searches. Nova fetches live Wikipedia data, Google results, and site content directly, parsing the exact answer you need in seconds without leaving your flow.' },
    { icon: '🎵', label: 'MEDIA', title: 'Universal Media Control', desc: 'Pause Spotify, skip YouTube tracks, lower system volume, or launch playlists — all through natural voice. Media control spans across all audio sources simultaneously.' },
  ], []);

  const steps = useMemo(() => [
    { num: '01', icon: '💬', title: 'Activate Nova', desc: 'Click the orb on this page or say a trigger phrase. The assistant wakes within milliseconds and signals readiness through visual feedback.' },
    { num: '02', icon: '🎙️', title: 'Give a Command', desc: 'Speak or type naturally. Nova understands intent, handles ambiguity, and can ask clarifying questions intelligently to ensure the right action is taken.' },
    { num: '03', icon: '⚡', title: 'Instant Execution', desc: 'Actions are executed in real time — apps launch, searches complete, and AI responses materialize — all within milliseconds of your command finishing.' },
  ], []);

  const handleDemoSubmit = useCallback((e) => {
    e.preventDefault();
    if (!cmdInput.trim()) return;
    const q = cmdInput.trim();
    setCmdInput('');
    setCmdHistory(prev => [...prev, { role: 'user', text: q }]);
    setTyping(true);
    setTimeout(() => {
      const responses = {
        default: 'Understood. Let me process that for you right away...',
        chrome: '✅ Opening Google Chrome now.',
        spotify: '✅ Launching Spotify and resuming your last playlist.',
        screenshot: '✅ Screenshot saved to your Desktop.',
        time: `✅ Current time is ${new Date().toLocaleTimeString()}.`,
        battery: '✅ Fetching battery status... 82% remaining, plugged in.',
        volume: '✅ Volume set to 50%.',
      };
      const key = Object.keys(responses).find(k => q.toLowerCase().includes(k)) || 'default';
      setTyping(false);
      setCmdHistory(prev => [...prev, { role: 'nova', text: responses[key] }]);
    }, 1200);
  }, [cmdInput]);

  return (
    <div className="lp-root">
      {/* ── SCROLL PROGRESS ── */}
      <div className="lp-progress-track">
        <div className="lp-progress-bar" style={{ width: `${progress}%` }} />
      </div>

      {/* ═══════════ HEADER ═══════════ */}
      <header className={`lp-header ${headerSolid ? 'solid' : ''}`}>
        <div className="lp-header-inner">
          <div className="lp-brand">
            <div className="lp-logo-wrap">
              <div className="lp-logo-core">N</div>
              <div className="lp-logo-ring" />
              <div className="lp-logo-pulse" />
            </div>
            <div className="lp-brand-text">
              <span className="lp-brand-name">NOVA</span>
              <span className="lp-brand-tag">AI Assistant</span>
            </div>
          </div>
          <nav className="lp-nav">
            {['Features', 'How It Works', 'Demo', 'Languages'].map(n => (
              <a key={n} href={`#${n.toLowerCase().replace(' ', '-')}`} className="lp-nav-link">{n}</a>
            ))}
          </nav>
          <div className="lp-header-actions">
            <div className={`lp-badge-status ${backendOnline ? 'on' : 'off'}`}>
              <span className="lp-badge-dot" />
              {backendOnline ? 'Live' : 'Offline'}
            </div>
            <button className="lp-btn-primary pulse-on-hover" onClick={onOpenAssistant}>
              <span className="btn-text">Launch Nova</span>
              <span className="btn-glow" />
            </button>
          </div>
        </div>
      </header>

      {/* ═══════════ HERO ═══════════ */}
      <section ref={heroRef} className={`lp-section lp-hero ${heroVis ? 'revealed' : ''}`} id="hero">
        <div className="hero-grid-mesh" />
        <div className="hero-nebula-a" />
        <div className="hero-nebula-b" />

        <div className="hero-inner">
          {/* Left — Text */}
          <div className="hero-text-col">
            <div className="hero-eyebrow">
              <span className="herb-badge">v2.0 — Gemini Powered</span>
              <span className="herb-badge accent">40+ Languages</span>
            </div>

            <h1 className="hero-headline">
              Your Desktop,<br/>
              <span className="hero-hl-red">Command&shy;ed</span><br/>
              by Voice
            </h1>

            <p className="hero-sub">
              Nova is an intelligent voice assistant that controls your OS, searches the web,
              plays media, and answers anything — in 40+ languages, powered by Gemini AI.
            </p>

            <div className="hero-typewriter-row">
              <span className="hero-prompt">›</span>
              <Typewriter phrases={typewriterPhrases} />
            </div>

            <div className="hero-cta-row">
              <button className="lp-btn-primary lp-btn-lg" onClick={onOpenAssistant} id="hero-launch-btn">
                <span>🚀</span> Launch Assistant
                <span className="btn-glow" />
              </button>
              <a href="#how-it-works" className="lp-btn-ghost lp-btn-lg">
                <span>▶</span> See How It Works
              </a>
            </div>

            <div className="hero-trust-row">
              <div className="hero-trust-item">
                <span className="ht-dot" />
                Real-time processing
              </div>
              <div className="hero-trust-item">
                <span className="ht-dot" />
                Privacy-first
              </div>
              <div className="hero-trust-item">
                <span className="ht-dot" />
                100% Free
              </div>
            </div>
          </div>

          {/* Right — AI Orb Visualization */}
          <div className="hero-orb-col">
            <div className="hero-orb-halo-outer" />
            <div className="hero-orb-halo-mid" />
            <div className="hero-orb-wrap" onClick={onToggleAssistant} title="Click to activate Nova">
              <AIOrb state={voiceState} />
            </div>

            {/* Status overlay */}
            <div className={`hero-orb-status ${voiceState !== 'idle' ? 'active' : ''}`}>
              {voiceState === 'idle' && <><span className="hos-dot" />Tap to Activate</>}
              {voiceState === 'listening' && <><span className="hos-dot listening" />Listening…</>}
              {voiceState === 'processing' && <><span className="hos-dot proc" />Processing…</>}
              {voiceState === 'speaking' && <><span className="hos-dot speaking" />Nova Speaking…</>}
            </div>

            {/* Floating command chips */}
            <div className="chip-system chip-1">
              <span>⚙️</span> Open Chrome
            </div>
            <div className="chip-system chip-2">
              <span>🧠</span> Explain AI
            </div>
            <div className="chip-system chip-3">
              <span>🌍</span> हिन्दी में बोलो
            </div>
            <div className="chip-system chip-4">
              <span>🎵</span> Play Spotify
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="hero-scroll-cue">
          <div className="hsc-mouse"><div className="hsc-wheel" /></div>
          <span>Scroll to explore</span>
        </div>
      </section>

      {/* ═══════════ STATS ═══════════ */}
      <section ref={statsRef} className={`lp-section lp-stats ${statsVis ? 'revealed' : ''}`}>
        <div className="stats-grid">
          {[
            { val: 50, suf: '+', label: 'Voice Commands' },
            { val: 40, suf: '+', label: 'Languages' },
            { val: 200, suf: 'ms', label: 'Avg Response' },
            { val: 6, suf: '', label: 'Command Categories' },
          ].map((s, i) => (
            <div className="stat-card" key={i}>
              <div className="stat-val">
                {statsVis ? <CountUp end={s.val} suffix={s.suf} /> : `0${s.suf}`}
              </div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════ FEATURES ═══════════ */}
      <section ref={featRef} className={`lp-section lp-features ${featVis ? 'revealed' : ''}`} id="features">
        <div className="lp-section-header">
          <div className="lp-section-eyebrow">Capabilities</div>
          <h2 className="lp-section-title">Everything You Need,<br/>Nothing You Don't</h2>
          <p className="lp-section-sub">Six core pillars that make Nova the most capable desktop assistant.</p>
        </div>
        <div className="feat-grid">
          {features.map((f, i) => (
            <div className="feat-card" key={i} style={{ '--delay': `${i * 0.07}s` }}>
              <div className="feat-card-glow" />
              <div className="feat-card-top">
                <div className="feat-icon-wrap">
                  <span className="feat-icon">{f.icon}</span>
                </div>
                <span className="feat-label">{f.label}</span>
              </div>
              <h3 className="feat-title">{f.title}</h3>
              <p className="feat-desc">{f.desc}</p>
              <div className="feat-arrow">→</div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════ HOW IT WORKS ═══════════ */}
      <section ref={howRef} className={`lp-section lp-how ${howVis ? 'revealed' : ''}`} id="how-it-works">
        <div className="lp-section-header">
          <div className="lp-section-eyebrow">Process</div>
          <h2 className="lp-section-title">Three Steps to<br/>Full Control</h2>
        </div>
        <div className="how-timeline">
          {steps.map((s, i) => (
            <div className="how-step" key={i} style={{ '--delay': `${i * 0.12}s` }}>
              <div className="how-step-num">{s.num}</div>
              <div className="how-step-icon">{s.icon}</div>
              <h3 className="how-step-title">{s.title}</h3>
              <p className="how-step-desc">{s.desc}</p>
              {i < steps.length - 1 && <div className="how-connector" />}
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════ DEMO TERMINAL ═══════════ */}
      <section ref={demoRef} className={`lp-section lp-demo ${demoVis ? 'revealed' : ''}`} id="demo">
        <div className="lp-section-header">
          <div className="lp-section-eyebrow">Live Demo</div>
          <h2 className="lp-section-title">Try It Right Here</h2>
          <p className="lp-section-sub">Type any command below to see how Nova responds in real-time.</p>
        </div>

        <div className="demo-terminal">
          {/* Window chrome */}
          <div className="dt-chrome">
            <div className="dt-dot dt-red" />
            <div className="dt-dot dt-yellow" />
            <div className="dt-dot dt-green" />
            <span className="dt-title">Nova — AI Voice Assistant</span>
            <span className={`dt-indicator ${backendOnline ? 'on' : 'off'}`}>
              <span className="dt-ind-dot" />
              {backendOnline ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Chat body */}
          <div className="dt-body">
            {cmdHistory.map((msg, i) => (
              <div key={i} className={`dt-msg ${msg.role}`}>
                <div className="dt-msg-avatar">
                  {msg.role === 'nova' ? '⬡' : '›'}
                </div>
                <div className="dt-msg-text">{msg.text}</div>
              </div>
            ))}
            {typing && (
              <div className="dt-msg nova">
                <div className="dt-msg-avatar">⬡</div>
                <div className="dt-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
          </div>

          {/* Input bar */}
          <form className="dt-input-row" onSubmit={handleDemoSubmit}>
            <div className="dt-mic-icon">🎙</div>
            <input
              className="dt-input"
              value={cmdInput}
              onChange={e => setCmdInput(e.target.value)}
              placeholder='Try: "Open Chrome", "What time is it?", "Play Spotify"...'
            />
            <button type="submit" className="dt-send-btn" disabled={!cmdInput.trim()}>
              Send <span className="dt-send-arrow">→</span>
            </button>
          </form>
        </div>
      </section>

      {/* ═══════════ LANGUAGES ═══════════ */}
      <section className="lp-section lp-langs" id="languages">
        <div className="lp-section-header">
          <div className="lp-section-eyebrow">Global</div>
          <h2 className="lp-section-title">Speak Your Language</h2>
        </div>
        <div className="langs-marquee-wrap">
          <div className="langs-marquee">
            {['🇮🇳 Hindi', '🇮🇳 Gujarati', '🇫🇷 French', '🇩🇪 German', '🇪🇸 Spanish', '🇯🇵 Japanese', '🇰🇷 Korean', '🇨🇳 Chinese', '🇸🇦 Arabic', '🇷🇺 Russian', '🇮🇳 Tamil', '🇮🇳 Telugu', '🇮🇳 Bengali', '🇮🇹 Italian', '🇵🇹 Portuguese', '🇳🇱 Dutch', '🇹🇷 Turkish', '🇹🇭 Thai', '🇻🇳 Vietnamese', '🇬🇷 Greek', '🇵🇱 Polish', '🇸🇪 Swedish', '🇮🇳 Marathi', '🇮🇳 Kannada'].map((l, i) => (
              <span key={i} className="lang-chip">{l}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════ CTA ═══════════ */}
      <section ref={ctaRef} className={`lp-section lp-cta ${ctaVis ? 'revealed' : ''}`} id="cta">
        <div className="cta-glow-a" />
        <div className="cta-glow-b" />
        <div className="cta-inner">
          <div className="lp-section-eyebrow">Get Started</div>
          <h2 className="cta-title">The Future of Desktop<br/>Control is Here</h2>
          <p className="cta-sub">Free forever. No account required. Just your voice.</p>
          <div className="cta-btn-row">
            <button className="lp-btn-primary lp-btn-lg cta-btn" onClick={onOpenAssistant}>
              <span>🚀</span> Launch Nova Now
              <span className="btn-glow" />
            </button>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="lp-btn-ghost lp-btn-lg">
              <span>⭐</span> Star on GitHub
            </a>
          </div>
        </div>
      </section>

      {/* ═══════════ FOOTER ═══════════ */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div className="lp-footer-brand">
            <div className="lp-logo-core sm">N</div>
            <span>NOVA AI Assistant</span>
          </div>
          <div className="lp-footer-links">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">GitHub</a>
            <a href="#">Contact</a>
          </div>
          <div className="lp-footer-copy">© 2025 Nova AI. Built with 🤍</div>
        </div>
      </footer>
    </div>
  );
}
