import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import VoiceOrb from './VoiceOrb';
import CommandInput from './CommandInput';

/* ═══════════════════════════════════════════
   Custom Hook — Scroll-triggered reveal
   ═══════════════════════════════════════════ */
function useScrollReveal(options = {}) {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setIsVisible(true); },
      { threshold: options.threshold || 0.15, rootMargin: options.rootMargin || '0px' }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, isVisible];
}

/* ═══════════════════════════════════════════
   Animated Counter Component
   ═══════════════════════════════════════════ */
function AnimatedCounter({ end, suffix = '', duration = 2000, isVisible }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!isVisible) return;
    let start = 0;
    const step = end / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setCount(end); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [isVisible, end, duration]);
  return <span>{count}{suffix}</span>;
}

/* ═══════════════════════════════════════════
   Typewriter Text
   ═══════════════════════════════════════════ */
function TypewriterText({ texts, speed = 80, pause = 2000 }) {
  const [textIndex, setTextIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const current = texts[textIndex];
    let timeout;
    if (!isDeleting && charIndex < current.length) {
      timeout = setTimeout(() => setCharIndex(c => c + 1), speed);
    } else if (!isDeleting && charIndex === current.length) {
      timeout = setTimeout(() => setIsDeleting(true), pause);
    } else if (isDeleting && charIndex > 0) {
      timeout = setTimeout(() => setCharIndex(c => c - 1), speed / 2);
    } else if (isDeleting && charIndex === 0) {
      setIsDeleting(false);
      setTextIndex(i => (i + 1) % texts.length);
    }
    return () => clearTimeout(timeout);
  }, [charIndex, isDeleting, textIndex, texts, speed, pause]);

  return (
    <span className="typewriter">
      {texts[textIndex].slice(0, charIndex)}
      <span className="typewriter-cursor">|</span>
    </span>
  );
}

/* ═══════════════════════════════════════════
   Mouse Glow Effect Hook
   ═══════════════════════════════════════════ */
function useMouseGlow() {
  const ref = useRef(null);
  const handleMove = useCallback((e) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    ref.current.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    ref.current.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
  }, []);
  return [ref, handleMove];
}

/* ═══════════════════════════════════════════
   LANDING PAGE — Main Component
   ═══════════════════════════════════════════ */
export default function LandingPage({
  voiceState,
  isRunning,
  isProcessing,
  backendOnline,
  onToggleAssistant,
  onSendCommand,
  onOpenAssistant,
}) {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [headerSolid, setHeaderSolid] = useState(false);
  const mainRef = useRef(null);

  // Scroll tracking
  useEffect(() => {
    const handleScroll = () => {
      const el = document.documentElement;
      const scrollTop = el.scrollTop || document.body.scrollTop;
      const scrollHeight = el.scrollHeight - el.clientHeight;
      setScrollProgress(scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0);
      setHeaderSolid(scrollTop > 60);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Section reveal hooks
  const [heroRef, heroVis] = useScrollReveal({ threshold: 0.1 });
  const [featRef, featVis] = useScrollReveal({ threshold: 0.1 });
  const [langRef, langVis] = useScrollReveal({ threshold: 0.1 });
  const [howRef, howVis] = useScrollReveal({ threshold: 0.15 });
  const [capRef, capVis] = useScrollReveal({ threshold: 0.1 });
  const [techRef, techVis] = useScrollReveal({ threshold: 0.15 });
  const [demoRef, demoVis] = useScrollReveal({ threshold: 0.15 });
  const [statsRef, statsVis] = useScrollReveal({ threshold: 0.2 });

  // Features data
  const features = useMemo(() => [
    { icon: '🎙️', title: 'Voice Control', desc: 'Speak naturally to control your entire system. Nova understands context, intent, and even casual speech patterns.', color: '#00d4ff', tag: 'CORE' },
    { icon: '🌍', title: '40+ Languages', desc: 'Speak in Hindi, Gujarati, French, German, Spanish, Tamil, Bengali, or any of 40+ languages — Nova auto-detects and responds in the same language.', color: '#ff7b00', tag: 'MULTILINGUAL' },
    { icon: '🧠', title: 'Gemini AI Brain', desc: 'Powered by Google Gemini for deep reasoning, creative answers, code help, and nuanced conversations.', color: '#a855f7', tag: 'AI' },
    { icon: '⚙️', title: 'System Automation', desc: 'Open apps, control volume, check battery, lock screen, monitor CPU — all with voice or text commands.', color: '#6366f1', tag: 'SYSTEM' },
    { icon: '🌐', title: 'Web Intelligence', desc: 'Search Google, YouTube, Wikipedia. Open any website. Get instant web answers without touching a browser.', color: '#06b6d4', tag: 'WEB' },
    { icon: '🎵', title: 'Media Maestro', desc: 'Play, pause, skip tracks, control volume. Full media playback control through voice commands.', color: '#8b5cf6', tag: 'MEDIA' },
    { icon: '📸', title: 'Smart Utilities', desc: 'Screenshots, timers, calculations, notes, coin flips — everyday tools at your command.', color: '#f59e0b', tag: 'TOOLS' },
    { icon: '💬', title: 'Natural Chat', desc: 'Ask anything — jokes, fun facts, motivational quotes, or deep philosophical questions. Nova always has an answer.', color: '#10b981', tag: 'CHAT' },
  ], []);

  // How it works steps
  const steps = useMemo(() => [
    { num: '01', title: 'Activate', desc: 'Click the orb or say "Hey Nova" to wake the assistant. The orb pulses blue to signal it\'s listening.', icon: '🔵' },
    { num: '02', title: 'Command', desc: 'Speak naturally or type your command. Nova processes your request using advanced AI and system APIs.', icon: '⚡' },
    { num: '03', title: 'Execute', desc: 'Nova performs the action instantly — opens apps, answers questions, plays music, or controls your system.', icon: '🚀' },
  ], []);

  // Capabilities
  const capabilities = useMemo(() => [
    { category: 'System Control', icon: '⚙️', items: ['Open Chrome', 'Volume Up/Down', 'Battery Status', 'Lock Screen', 'CPU Usage', 'IP Address', 'System Info'], color: '#6366f1' },
    { category: 'Web Search', icon: '🌐', items: ['Google Search', 'YouTube Search', 'Wikipedia Lookup', 'Open Website', 'Web Answers'], color: '#06b6d4' },
    { category: 'Media', icon: '🎵', items: ['Play Music', 'Next/Prev Song', 'Volume Control', 'Pause/Resume'], color: '#8b5cf6' },
    { category: 'Utilities', icon: '🛠️', items: ['Screenshot', 'Timer', 'Calculator', 'Notes', 'Coin Flip'], color: '#f59e0b' },
    { category: 'AI Chat', icon: '🤖', items: ['Ask Anything', 'Get Explanations', 'Creative Writing', 'Code Help', 'Advice'], color: '#ec4899' },
    { category: 'Info & Fun', icon: '📚', items: ['Weather', 'Jokes', 'Fun Facts', 'Quotes', 'Time/Date'], color: '#10b981' },
  ], []);

  // Tech stack
  const techStack = useMemo(() => [
    { name: 'React', icon: '⚛️', desc: 'Frontend UI', color: '#61dafb' },
    { name: 'Vite', icon: '⚡', desc: 'Build tool', color: '#646cff' },
    { name: 'Flask', icon: '🐍', desc: 'Backend API', color: '#00d4aa' },
    { name: 'Gemini', icon: '🧠', desc: 'AI Engine', color: '#a855f7' },
    { name: 'Python', icon: '🐍', desc: 'Core Logic', color: '#3776ab' },
    { name: 'WebSocket', icon: '🔌', desc: 'Real-time', color: '#ff6b6b' },
  ], []);

  // Languages data for showcase
  const languages = useMemo(() => [
    { name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
    { name: 'Gujarati', native: 'ગુજરાતી', flag: '🇮🇳' },
    { name: 'Bengali', native: 'বাংলা', flag: '🇮🇳' },
    { name: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
    { name: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
    { name: 'Kannada', native: 'ಕನ್ನಡ', flag: '🇮🇳' },
    { name: 'Malayalam', native: 'മലയാളം', flag: '🇮🇳' },
    { name: 'Marathi', native: 'मराठी', flag: '🇮🇳' },
    { name: 'Punjabi', native: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
    { name: 'Urdu', native: 'اردو', flag: '🇵🇰' },
    { name: 'French', native: 'Français', flag: '🇫🇷' },
    { name: 'German', native: 'Deutsch', flag: '🇩🇪' },
    { name: 'Spanish', native: 'Español', flag: '🇪🇸' },
    { name: 'Italian', native: 'Italiano', flag: '🇮🇹' },
    { name: 'Portuguese', native: 'Português', flag: '🇵🇹' },
    { name: 'Russian', native: 'Русский', flag: '🇷🇺' },
    { name: 'Japanese', native: '日本語', flag: '🇯🇵' },
    { name: 'Korean', native: '한국어', flag: '🇰🇷' },
    { name: 'Chinese', native: '中文', flag: '🇨🇳' },
    { name: 'Arabic', native: 'العربية', flag: '🇸🇦' },
    { name: 'Turkish', native: 'Türkçe', flag: '🇹🇷' },
    { name: 'Dutch', native: 'Nederlands', flag: '🇳🇱' },
    { name: 'Thai', native: 'ไทย', flag: '🇹🇭' },
    { name: 'Vietnamese', native: 'Tiếng Việt', flag: '🇻🇳' },
    { name: 'Nepali', native: 'नेपाली', flag: '🇳🇵' },
    { name: 'Odia', native: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
    { name: 'Sanskrit', native: 'संस्कृतम्', flag: '🇮🇳' },
    { name: 'Swedish', native: 'Svenska', flag: '🇸🇪' },
    { name: 'Greek', native: 'Ελληνικά', flag: '🇬🇷' },
    { name: 'Polish', native: 'Polski', flag: '🇵🇱' },
  ], []);

  // Stats
  const stats = useMemo(() => [
    { value: 45, suffix: '+', label: 'Voice Commands', icon: '🎙️' },
    { value: 40, suffix: '+', label: 'Languages Supported', icon: '🌍' },
    { value: 6, suffix: '', label: 'Command Categories', icon: '📂' },
    { value: 500, suffix: 'ms', label: 'Avg Response Time', icon: '🚀' },
  ], []);

  const [glowRef, glowHandler] = useMouseGlow();

  return (
    <>
      {/* ═══ SCROLL PROGRESS BAR ═══ */}
      <div className="scroll-progress-track">
        <div className="scroll-progress-bar" style={{ width: `${scrollProgress}%` }} />
      </div>

      {/* ═══ FIXED HEADER ═══ */}
      <header className={`landing-header ${headerSolid ? 'solid' : ''}`}>
        <div className="lh-brand">
          <div className="lh-logo">
            <span className="lh-logo-letter">N</span>
            <div className="lh-logo-ring" />
          </div>
          <div>
            <div className="lh-title">NOVA</div>
            <div className="lh-subtitle">AI Voice Assistant</div>
          </div>
        </div>
        <nav className="lh-nav">
          <a href="#features" className="lh-link">Features</a>
          <a href="#languages" className="lh-link">Languages</a>
          <a href="#how-it-works" className="lh-link">How It Works</a>
          <a href="#capabilities" className="lh-link">Commands</a>
          <a href="#demo" className="lh-link">Try It</a>
        </nav>
        <div className="lh-actions">
          <div className={`lh-status ${backendOnline ? 'online' : 'offline'}`}>
            <span className="lh-status-dot" />
            <span>{backendOnline ? 'Online' : 'Offline'}</span>
          </div>
          <button className="lh-cta" onClick={onOpenAssistant}>
            💬 Open Assistant
          </button>
        </div>
      </header>

      {/* ═══════════════════════════════════════
           SECTION 1 — HERO
         ═══════════════════════════════════════ */}
      <section ref={heroRef} className={`landing-section hero-section ${heroVis ? 'visible' : ''}`} id="hero">
        <div className="hero-bg-effects">
          <div className="hero-nebula hero-nebula-1" />
          <div className="hero-nebula hero-nebula-2" />
          <div className="hero-nebula hero-nebula-3" />
          <div className="hero-grid-overlay" />
          <div className="hero-radial-glow" />
          {/* Animated lines */}
          <div className="hero-line hero-line-1" />
          <div className="hero-line hero-line-2" />
          <div className="hero-line hero-line-3" />
        </div>

        <div className="hero-content">
          <div className="hero-badge-row">
            <span className="hero-badge">✨ Next-Gen Desktop AI</span>
            <span className="hero-badge accent">🌍 40+ Languages</span>
            <span className="hero-badge">v2.0 — Gemini Powered</span>
          </div>

          <h1 className="hero-mega-title">
            <span className="hero-text-line reveal-text">Meet</span>
            <span className="hero-text-line">
              <span className="hero-gradient-text">Nova</span>
            </span>
          </h1>

          <p className="hero-description">
            Your intelligent voice-powered desktop assistant. Control your system, search the web, 
            play media, get AI-powered answers — all through natural conversation in <strong>40+ languages</strong> including Hindi, Gujarati, French, German, and more.
          </p>

          <div className="hero-typewriter-row">
            <span className="hero-prompt-icon">›</span>
            <TypewriterText
              texts={[
                '"Hey Nova, open Chrome"',
                '"नोवा, मौसम कैसा है?" (Hindi)',
                '"નોવા, સમય શું છે?" (Gujarati)',
                '"Nova, ouvre Chrome" (French)',
                '"Nova, spiel Musik" (German)',
                '"Tell me a joke"',
                '"बैटरी कितनी है?" (Hindi)',
                '"Quelle heure est-il?" (French)',
                '"Search YouTube for React tutorials"',
              ]}
              speed={60}
              pause={2500}
            />
          </div>

          <div className="hero-orb-showcase">
            <div className="hero-orb-glow-ring" />
            <VoiceOrb state={voiceState} onToggle={onToggleAssistant} isRunning={isRunning} />
          </div>

          <div className="hero-btn-row">
            <button className="hero-btn primary" onClick={onOpenAssistant}>
              <span>🚀</span> Launch Assistant
            </button>
            <a href="#features" className="hero-btn secondary">
              <span>✦</span> Explore Features
            </a>
          </div>

          <div className="hero-scroll-indicator">
            <div className="scroll-mouse">
              <div className="scroll-wheel" />
            </div>
            <span>Scroll to explore</span>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION 2 — FEATURES
         ═══════════════════════════════════════ */}
      <section ref={featRef} className={`landing-section features-section ${featVis ? 'visible' : ''}`} id="features">
        <div className="section-bg-accent" />
        <div className="section-header">
          <span className="section-tag">FEATURES</span>
          <h2 className="section-title">Everything You Need, <span className="gradient-word">Voice-First</span></h2>
          <p className="section-desc">Nova combines powerful system control, AI intelligence, and intuitive voice interaction into one seamless assistant.</p>
        </div>

        <div className="features-grid" ref={glowRef} onMouseMove={glowHandler}>
          {features.map((f, i) => (
            <div
              key={i}
              className="feature-card"
              style={{ '--card-color': f.color, '--card-index': i, '--card-delay': `${i * 0.08}s` }}
            >
              <div className="feature-card-glow" />
              <div className="feature-card-border" />
              <div className="feature-card-inner">
                <div className="feature-icon-wrap">
                  <span className="feature-icon">{f.icon}</span>
                  <div className="feature-icon-ring" />
                </div>
                <span className="feature-tag" style={{ color: f.color }}>{f.tag}</span>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION — LANGUAGES
         ═══════════════════════════════════════ */}
      <section ref={langRef} className={`landing-section lang-section ${langVis ? 'visible' : ''}`} id="languages">
        <div className="section-header">
          <span className="section-tag">🌍 MULTILINGUAL</span>
          <h2 className="section-title">Speak in <span className="gradient-word">Any Language</span></h2>
          <p className="section-desc">Nova understands and responds in 40+ Indian and global languages. Just speak or type naturally — language is auto-detected.</p>
        </div>

        <div className="lang-showcase">
          <div className="lang-examples">
            <div className="lang-example-card">
              <span className="lang-ex-flag">🇮🇳</span>
              <span className="lang-ex-label">Hindi</span>
              <span className="lang-ex-text">"नोवा, मौसम कैसा है?"</span>
              <span className="lang-ex-reply">→ "आज का मौसम साफ है, 28°C"</span>
            </div>
            <div className="lang-example-card">
              <span className="lang-ex-flag">🇮🇳</span>
              <span className="lang-ex-label">Gujarati</span>
              <span className="lang-ex-text">"નોવા, સમય શું છે?"</span>
              <span className="lang-ex-reply">→ "હાલનો સમય બપોરે ૨:૩૦ છે"</span>
            </div>
            <div className="lang-example-card">
              <span className="lang-ex-flag">🇫🇷</span>
              <span className="lang-ex-label">French</span>
              <span className="lang-ex-text">"Nova, raconte une blague"</span>
              <span className="lang-ex-reply">→ "Pourquoi les plongeurs..."</span>
            </div>
            <div className="lang-example-card">
              <span className="lang-ex-flag">🇩🇪</span>
              <span className="lang-ex-label">German</span>
              <span className="lang-ex-text">"Nova, wie ist das Wetter?"</span>
              <span className="lang-ex-reply">→ "Heute ist es sonnig, 24°C"</span>
            </div>
          </div>

          <div className="lang-badges-container">
            <div className="lang-badges-scroll">
              {languages.map((l, i) => (
                <div key={i} className="lang-badge" style={{ '--lang-delay': `${i * 0.05}s` }}>
                  <span className="lang-flag">{l.flag}</span>
                  <span className="lang-name">{l.name}</span>
                  <span className="lang-native">{l.native}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="lang-note">💡 Auto-detection — just type or speak in your language, Nova replies in the same language!</p>
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION — HOW IT WORKS
         ═══════════════════════════════════════ */}
      <section ref={howRef} className={`landing-section how-section ${howVis ? 'visible' : ''}`} id="how-it-works">
        <div className="section-header">
          <span className="section-tag">HOW IT WORKS</span>
          <h2 className="section-title">Three Steps to <span className="gradient-word">Magic</span></h2>
          <p className="section-desc">From activation to execution in under a second. It's that simple.</p>
        </div>

        <div className="how-timeline">
          {steps.map((s, i) => (
            <div key={i} className="how-step" style={{ '--step-delay': `${i * 0.2}s` }}>
              <div className="how-step-num">{s.num}</div>
              <div className="how-step-icon">{s.icon}</div>
              <div className="how-step-content">
                <h3 className="how-step-title">{s.title}</h3>
                <p className="how-step-desc">{s.desc}</p>
              </div>
              {i < steps.length - 1 && <div className="how-connector" />}
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION 4 — CAPABILITIES
         ═══════════════════════════════════════ */}
      <section ref={capRef} className={`landing-section cap-section ${capVis ? 'visible' : ''}`} id="capabilities">
        <div className="section-header">
          <span className="section-tag">CAPABILITIES</span>
          <h2 className="section-title"><span className="gradient-word">45+</span> Commands at Your Service</h2>
          <p className="section-desc">From system control to AI conversations — explore everything Nova can do.</p>
        </div>

        <div className="cap-grid">
          {capabilities.map((cap, i) => (
            <div key={i} className="cap-card" style={{ '--cap-color': cap.color, '--cap-delay': `${i * 0.1}s` }}>
              <div className="cap-card-header">
                <span className="cap-icon">{cap.icon}</span>
                <h3 className="cap-title">{cap.category}</h3>
                <span className="cap-count">{cap.items.length} commands</span>
              </div>
              <div className="cap-items">
                {cap.items.map((item, j) => (
                  <button
                    key={j}
                    className="cap-item"
                    onClick={() => onSendCommand(item.toLowerCase())}
                    style={{ '--item-delay': `${j * 0.04}s` }}
                  >
                    <span className="cap-item-dot" />
                    <span>{item}</span>
                    <span className="cap-item-arrow">→</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION 5 — TECH STACK
         ═══════════════════════════════════════ */}
      <section ref={techRef} className={`landing-section tech-section ${techVis ? 'visible' : ''}`} id="tech">
        <div className="section-header">
          <span className="section-tag">TECHNOLOGY</span>
          <h2 className="section-title">Built With <span className="gradient-word">Modern Tech</span></h2>
          <p className="section-desc">A powerful stack designed for real-time AI interactions and system-level control.</p>
        </div>

        <div className="tech-orbit-container">
          <div className="tech-center-orb">
            <span>NOVA</span>
          </div>
          <div className="tech-ring" />
          <div className="tech-ring tech-ring-2" />
          {techStack.map((t, i) => (
            <div
              key={i}
              className="tech-badge"
              style={{
                '--tech-angle': `${(i * 360) / techStack.length}deg`,
                '--tech-color': t.color,
                '--tech-delay': `${i * 0.15}s`,
              }}
            >
              <span className="tech-badge-icon">{t.icon}</span>
              <span className="tech-badge-name">{t.name}</span>
              <span className="tech-badge-desc">{t.desc}</span>
            </div>
          ))}
        </div>

        <div className="tech-details-grid">
          <div className="tech-detail-card">
            <div className="tech-detail-icon">⚡</div>
            <h4>Lightning Fast</h4>
            <p>Sub-500ms response times with optimized Flask backend and React frontend.</p>
          </div>
          <div className="tech-detail-card">
            <div className="tech-detail-icon">🔒</div>
            <h4>Local-First</h4>
            <p>Runs entirely on your machine. Your data never leaves your desktop.</p>
          </div>
          <div className="tech-detail-card">
            <div className="tech-detail-icon">🔄</div>
            <h4>Real-Time</h4>
            <p>Live status updates, voice waveforms, and instant feedback via WebSocket.</p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION 6 — LIVE DEMO
         ═══════════════════════════════════════ */}
      <section ref={demoRef} className={`landing-section demo-section ${demoVis ? 'visible' : ''}`} id="demo">
        <div className="demo-bg-glow" />
        <div className="section-header">
          <span className="section-tag">TRY IT NOW</span>
          <h2 className="section-title">Experience <span className="gradient-word">Nova</span> Live</h2>
          <p className="section-desc">Type a command below or click the orb to start talking. Nova is ready.</p>
        </div>

        <div className="demo-container">
          <div className="demo-card">
            <div className="demo-card-glow" />
            <div className="demo-orb-area">
              <VoiceOrb state={voiceState} onToggle={onToggleAssistant} isRunning={isRunning} />
            </div>
            <div className="demo-input-area">
              <CommandInput onSend={onSendCommand} disabled={isProcessing} />
            </div>
            <div className="demo-quick-cmds">
              {['What time is it', 'Tell me a joke', 'Weather', 'Play music', 'Battery status', 'Fun fact'].map((cmd, i) => (
                <button key={i} className="demo-quick-btn" onClick={() => onSendCommand(cmd)}>
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
           SECTION 7 — STATS
         ═══════════════════════════════════════ */}
      <section ref={statsRef} className={`landing-section stats-section ${statsVis ? 'visible' : ''}`} id="stats">
        <div className="stats-grid">
          {stats.map((s, i) => (
            <div key={i} className="stat-card" style={{ '--stat-delay': `${i * 0.1}s` }}>
              <div className="stat-icon">{s.icon}</div>
              <div className="stat-value">
                <AnimatedCounter end={s.value} suffix={s.suffix} isVisible={statsVis} />
              </div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════
           FOOTER
         ═══════════════════════════════════════ */}
      <footer className="landing-footer">
        <div className="footer-glow" />
        <div className="footer-content">
          <div className="footer-brand">
            <div className="footer-logo">N</div>
            <div>
              <div className="footer-title">NOVA</div>
              <div className="footer-tagline">AI Voice Assistant for Desktop</div>
            </div>
          </div>
          <div className="footer-links">
            <a href="#hero">Home</a>
            <a href="#features">Features</a>
            <a href="#capabilities">Commands</a>
            <a href="#demo">Try It</a>
          </div>
          <div className="footer-divider" />
          <div className="footer-bottom">
            <span>⚡ Powered by Flask + Gemini AI</span>
            <span>Built with ❤️ for productivity</span>
          </div>
        </div>
      </footer>
    </>
  );
}
