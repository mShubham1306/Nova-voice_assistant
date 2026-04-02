import React, { useState, useCallback, useEffect, useRef } from 'react';
import LandingPage from './components/LandingPage';
import FloatingAssistant from './components/FloatingAssistant';
import WelcomeSplash from './components/WelcomeSplash';
import api from './services/api';

function App() {
  const [showSplash, setShowSplash]   = useState(true);
  const [isRunning, setIsRunning]     = useState(false);
  const [voiceState, setVoiceState]   = useState('idle');
  const [interimText, setInterimText] = useState('');
  const [history, setHistory]         = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);

  const canvasRef       = useRef(null);
  const recognitionRef  = useRef(null);
  const isRunningRef    = useRef(false); // sync mirror of isRunning for closures
  const processingRef   = useRef(false); // prevents double-fire mid-command

  // ─── Backend health check ───
  useEffect(() => {
    const check = async () => {
      try { await api.getStatus(); setBackendOnline(true); }
      catch { setBackendOnline(false); }
    };
    check();
    const t = setInterval(check, 8000);
    return () => clearInterval(t);
  }, []);

  // ─── Particle canvas ───
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let mouseX = 0, mouseY = 0;
    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = document.documentElement.scrollHeight;
    };
    resize();
    const onResize = () => resize();
    const onMouse  = (e) => { mouseX = e.clientX; mouseY = e.clientY + window.scrollY; };
    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', onMouse);

    const particles = Array.from({ length: 90 }, () => {
      return {
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight * 3,
        size: Math.random() * 1.8 + 0.3,
        sx: (Math.random() - 0.5) * 0.25,
        sy: (Math.random() - 0.5) * 0.25,
        hue: Math.random() * 15,
        pulse: Math.random() * Math.PI * 2,
      };
    });

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.sx; p.y += p.sy; p.pulse += 0.012;
        const op = 0.06 + Math.sin(p.pulse) * 0.07;
        const dx = p.x - mouseX, dy = p.y - mouseY;
        const d  = Math.hypot(dx, dy);
        if (d < 100) { p.x += (dx / d) * 0.6; p.y += (dy / d) * 0.6; }
        if (p.x < 0 || p.x > canvas.width)  p.x = Math.random() * canvas.width;
        if (p.y < 0 || p.y > canvas.height) p.y = Math.random() * canvas.height;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue},80%,55%,${op})`;
        ctx.fill();
      }
      animId = requestAnimationFrame(animate);
    };
    animate();
    const si = setInterval(() => {
      const h = document.documentElement.scrollHeight;
      if (canvas.height !== h) canvas.height = h;
    }, 2000);
    return () => {
      cancelAnimationFrame(animId);
      clearInterval(si);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMouse);
    };
  }, []);

  // ─── SINGLE VOICE RECOGNITION INSTANCE ───
  //     Created once and never recreated — prevents duplicate audio sessions
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setSpeechSupported(false); return; }

    const rec = new SR();
    rec.continuous      = false;
    rec.interimResults  = true;   // ← real-time text as user speaks
    rec.lang            = 'en-IN';
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      setVoiceState('listening');
      setInterimText('');
    };

    rec.onresult = (event) => {
      let interim = '';
      let final   = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) final   += event.results[i][0].transcript;
        else                          interim += event.results[i][0].transcript;
      }
      if (interim) setInterimText(interim);
      if (final && !processingRef.current) {
        processingRef.current = true;
        setInterimText('');
        setVoiceState('processing');
        handleSendCommandRef.current(final.trim());
      }
    };

    rec.onerror = (event) => {
      if (event.error === 'no-speech') {
        // Silently restart — user just didn't say anything
        if (isRunningRef.current) { try { rec.start(); } catch {} }
        else { setVoiceState('idle'); }
        return;
      }
      if (event.error === 'aborted') return; // deliberate stop
      console.warn('[Voice] Error:', event.error);
      setVoiceState('idle');
      setIsRunning(false);
      isRunningRef.current = false;
    };

    rec.onend = () => {
      if (isRunningRef.current && !processingRef.current) {
        try { rec.start(); }  // ← restart immediately after each utterance
        catch {
          setVoiceState('idle');
          setIsRunning(false);
          isRunningRef.current = false;
        }
      } else if (!isRunningRef.current) {
        setVoiceState('idle');
      }
    };

    recognitionRef.current = rec;
    setSpeechSupported(true);
    return () => { try { rec.abort(); } catch {} };
  }, []); // ← NEVER re-run

  // Use a ref for sendCommand so recognition closure can call the latest version
  const handleSendCommandRef = useRef(null);

  const handleSendCommand = useCallback(async (query) => {
    if (!query?.trim()) return;
    setIsProcessing(true);
    const ts = new Date().toISOString();
    setHistory(prev => [...prev, { query, response: '', type: 'pending', timestamp: ts }]);

    try {
      const result   = await api.sendCommand(query);
      const response = result.response || 'Done!';
      const type     = result.type     || 'success';

      setHistory(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { query, response, type, timestamp: new Date().toISOString() };
        return updated;
      });

      // Non-blocking TTS — speak response, then immediately resume listening
      if (response && window.speechSynthesis && isRunningRef.current) {
        const voices   = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Microsoft'))) || voices[0];
        const utter = new SpeechSynthesisUtterance(response);
        utter.rate = 1.15; utter.pitch = 1; utter.volume = 0.95;
        if (preferred) utter.voice = preferred;
        setVoiceState('speaking');
        utter.onend = utter.onerror = () => {
          processingRef.current = false;
          if (isRunningRef.current) {
            setVoiceState('listening');
            try { recognitionRef.current?.start(); } catch {}
          } else {
            setVoiceState('idle');
          }
        };
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
      } else {
        // No TTS or not running — immediately resume
        processingRef.current = false;
        setVoiceState(isRunningRef.current ? 'listening' : 'idle');
        if (isRunningRef.current) { try { recognitionRef.current?.start(); } catch {} }
      }
    } catch {
      setHistory(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          query,
          response: '🔌 Backend offline. Run: cd backend && python app.py',
          type: 'error',
          timestamp: new Date().toISOString(),
        };
        return updated;
      });
      processingRef.current = false;
      setVoiceState(isRunningRef.current ? 'listening' : 'idle');
      if (isRunningRef.current) { try { recognitionRef.current?.start(); } catch {} }
    } finally {
      setIsProcessing(false);
    }
  }, []);

  // Keep ref synced
  useEffect(() => { handleSendCommandRef.current = handleSendCommand; }, [handleSendCommand]);

  // ─── Toggle on-page orb listening ───
  const handleToggleAssistant = useCallback(() => {
    if (isRunningRef.current) {
      isRunningRef.current = false;
      setIsRunning(false);
      setVoiceState('idle');
      setInterimText('');
      window.speechSynthesis?.cancel();
      try { recognitionRef.current?.abort(); } catch {}
    } else if (speechSupported) {
      isRunningRef.current = true;
      setIsRunning(true);
      processingRef.current = false;
      try { recognitionRef.current?.start(); }
      catch { isRunningRef.current = false; setIsRunning(false); setVoiceState('idle'); }
    } else {
      setAssistantOpen(true);
    }
  }, [speechSupported]);

  // ─── Mic button in floating panel ───
  const handleMicToggle = useCallback(() => {
    if (!speechSupported || !recognitionRef.current) return;
    if (isRunningRef.current) {
      isRunningRef.current = false;
      setIsRunning(false);
      setVoiceState('idle');
      setInterimText('');
      try { recognitionRef.current.abort(); } catch {}
    } else {
      isRunningRef.current  = true;
      processingRef.current = false;
      setIsRunning(true);
      try { recognitionRef.current.start(); }
      catch { isRunningRef.current = false; setIsRunning(false); setVoiceState('idle'); }
    }
  }, [speechSupported]);

  return (
    <div className="app-root">
      {showSplash && <WelcomeSplash onDone={() => setShowSplash(false)} />}

      <div className="app-background">
        <canvas ref={canvasRef} className="particle-canvas" />
      </div>

      <LandingPage
        voiceState={voiceState}
        interimText={interimText}
        isRunning={isRunning}
        isProcessing={isProcessing}
        backendOnline={backendOnline}
        onToggleAssistant={handleToggleAssistant}
        onSendCommand={handleSendCommand}
        onOpenAssistant={() => setAssistantOpen(true)}
        speechSupported={speechSupported}
      />

      <FloatingAssistant
        history={history}
        onSendCommand={handleSendCommand}
        isProcessing={isProcessing}
        onCommand={handleSendCommand}
        isOpen={assistantOpen}
        onClose={() => setAssistantOpen(false)}
        voiceState={voiceState}
        onMicToggle={handleMicToggle}
        interimText={interimText}
        speechSupported={speechSupported}
      />
    </div>
  );
}

export default App;
