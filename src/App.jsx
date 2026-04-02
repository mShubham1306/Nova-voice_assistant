import React, { useState, useCallback, useEffect, useRef } from 'react';
import LandingPage from './components/LandingPage';
import FloatingAssistant from './components/FloatingAssistant';
import api from './services/api';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [voiceState, setVoiceState] = useState('idle');
  const [history, setHistory] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const canvasRef = useRef(null);

  // Check backend status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        await api.getStatus();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // Full-page particle canvas animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let particles = [];
    let mouseX = 0, mouseY = 0;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = document.documentElement.scrollHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const handleMouseMove = (e) => { mouseX = e.clientX; mouseY = e.clientY + window.scrollY; };
    window.addEventListener('mousemove', handleMouseMove);

    class Particle {
      constructor() { this.reset(); }
      reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 2 + 0.5;
        this.speedX = (Math.random() - 0.5) * 0.3;
        this.speedY = (Math.random() - 0.5) * 0.3;
        this.opacity = Math.random() * 0.4 + 0.05;
        this.hue = Math.random() > 0.5 ? 200 + Math.random() * 40 : 270 + Math.random() * 40;
        this.pulse = Math.random() * Math.PI * 2;
      }
      update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.pulse += 0.015;
        this.opacity = 0.1 + Math.sin(this.pulse) * 0.12;
        // Mouse repulsion
        const dx = this.x - mouseX;
        const dy = this.y - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          this.x += dx / dist * 0.8;
          this.y += dy / dist * 0.8;
        }
        if (this.x < 0 || this.x > canvas.width) this.x = Math.random() * canvas.width;
        if (this.y < 0 || this.y > canvas.height) this.y = Math.random() * canvas.height;
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${this.hue}, 80%, 65%, ${this.opacity})`;
        ctx.fill();
      }
    }

    for (let i = 0; i < 120; i++) particles.push(new Particle());

    const connectParticles = () => {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.strokeStyle = `hsla(220, 60%, 50%, ${0.04 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => { p.update(); p.draw(); });
      connectParticles();
      animId = requestAnimationFrame(animate);
    };
    animate();

    // Re-calc canvas height on scroll (for dynamic pages)
    const resizeOnScroll = () => {
      const newH = document.documentElement.scrollHeight;
      if (canvas.height !== newH) canvas.height = newH;
    };
    const scrollInterval = setInterval(resizeOnScroll, 2000);

    return () => {
      cancelAnimationFrame(animId);
      clearInterval(scrollInterval);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  // ─── Web Speech API for browser-based voice input ───
  const recognitionRef = useRef(null);
  const [speechSupported, setSpeechSupported] = useState(false);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-IN'; // Default, supports auto-detection too
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('[Voice] Heard:', transcript);
        setVoiceState('processing');
        handleSendCommand(transcript);
      };

      recognition.onerror = (event) => {
        console.log('[Voice] Error:', event.error);
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
          console.error('[Voice] Recognition error:', event.error);
        }
        setVoiceState('idle');
        setIsRunning(false);
      };

      recognition.onend = () => {
        // If still running, auto-restart for continuous listening
        if (isRunning) {
          try {
            recognition.start();
            setVoiceState('listening');
          } catch (e) {
            setVoiceState('idle');
            setIsRunning(false);
          }
        } else {
          setVoiceState('idle');
        }
      };

      recognition.onspeechstart = () => {
        setVoiceState('listening');
      };

      recognitionRef.current = recognition;
      setSpeechSupported(true);
    } else {
      console.warn('[Voice] Web Speech API not supported in this browser');
      setSpeechSupported(false);
    }
  }, []);

  // Keep the recognition's onend callback in sync with isRunning
  useEffect(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    recognition.onend = () => {
      if (isRunning) {
        try {
          recognition.start();
          setVoiceState('listening');
        } catch (e) {
          setVoiceState('idle');
          setIsRunning(false);
        }
      } else {
        setVoiceState('idle');
      }
    };
  }, [isRunning]);

  const handleToggleAssistant = useCallback(async () => {
    const recognition = recognitionRef.current;

    if (isRunning) {
      // Stop listening
      setIsRunning(false);
      setVoiceState('idle');
      if (recognition) {
        try { recognition.abort(); } catch (e) {}
      }
      // Also stop backend voice loop if it was started
      try { await api.stopAssistant(); } catch {}
    } else {
      // Start listening via browser
      if (recognition && speechSupported) {
        try {
          recognition.start();
          setIsRunning(true);
          setVoiceState('listening');
        } catch (e) {
          console.error('[Voice] Failed to start:', e);
          setIsRunning(false);
          setVoiceState('idle');
        }
      } else {
        // Fallback: try backend voice (if PyAudio available)
        try {
          await api.startAssistant();
          setIsRunning(true);
          setVoiceState('listening');
        } catch {
          setIsRunning(false);
          setVoiceState('idle');
        }
      }
    }
  }, [isRunning, speechSupported]);

  const handleSendCommand = useCallback(async (query) => {
    setIsProcessing(true);
    setVoiceState('processing');

    const newEntry = {
      query,
      response: '',
      type: 'pending',
      timestamp: new Date().toISOString(),
    };
    setHistory(prev => [...prev, newEntry]);

    try {
      const result = await api.sendCommand(query);
      setHistory(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          query,
          response: result.response || 'Done!',
          type: result.type || 'success',
          timestamp: new Date().toISOString(),
        };
        return updated;
      });
      setVoiceState('speaking');
      setTimeout(() => setVoiceState(isRunning ? 'listening' : 'idle'), 2000);
    } catch {
      setHistory(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          query,
          response: '🔌 Backend offline — start it with: cd backend && python app.py',
          type: 'error',
          timestamp: new Date().toISOString(),
        };
        return updated;
      });
      setVoiceState('idle');
    } finally {
      setIsProcessing(false);
    }
  }, [isRunning]);

  const handleCommandClick = useCallback((cmd) => {
    handleSendCommand(cmd);
  }, [handleSendCommand]);

  // Reference to open assistant from landing page
  const [assistantOpen, setAssistantOpen] = useState(false);

  return (
    <div className="app-root">
      {/* ✨ GLOBAL ANIMATED BACKGROUND */}
      <div className="app-background">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
        <div className="bg-orb bg-orb-4" />
        <canvas ref={canvasRef} className="particle-canvas" />
      </div>

      {/* 🏠 SCROLLABLE LANDING PAGE */}
      <LandingPage
        voiceState={voiceState}
        isRunning={isRunning}
        isProcessing={isProcessing}
        backendOnline={backendOnline}
        onToggleAssistant={handleToggleAssistant}
        onSendCommand={handleSendCommand}
        onOpenAssistant={() => setAssistantOpen(true)}
      />

      {/* 💬 FLOATING ASSISTANT PANEL */}
      <FloatingAssistant
        history={history}
        onSendCommand={handleSendCommand}
        isProcessing={isProcessing}
        onCommand={handleCommandClick}
      />
    </div>
  );
}

export default App;
