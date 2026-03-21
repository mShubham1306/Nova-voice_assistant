import React, { useMemo } from 'react';

export default function VoiceOrb({ state, onToggle, isRunning }) {
  const getIcon = () => {
    switch (state) {
      case 'listening': return '🎙️';
      case 'speaking': return '🔊';
      case 'processing': return '⚡';
      default: return '🎤';
    }
  };

  const getLabel = () => {
    switch (state) {
      case 'listening': return 'Listening...';
      case 'speaking': return 'Nova is speaking...';
      case 'processing': return 'Processing...';
      default: return 'Tap to activate';
    }
  };

  // Orbiting particles
  const orbitParticles = useMemo(() =>
    Array.from({ length: 8 }, (_, i) => ({
      id: i,
      delay: `${i * 0.4}s`,
      size: 3 + Math.random() * 3,
      orbit: 85 + Math.random() * 20,
      dur: `${3 + Math.random() * 2}s`,
      hue: i % 2 === 0 ? '200' : '280',
    })), []
  );

  return (
    <div className="voice-section">
      <div className="voice-orb-container">
        {/* Orbiting particles */}
        {orbitParticles.map(p => (
          <div
            key={p.id}
            className={`orbit-particle ${state !== 'idle' ? 'active' : ''}`}
            style={{
              '--orbit-radius': `${p.orbit}px`,
              '--orbit-delay': p.delay,
              '--orbit-dur': p.dur,
              '--particle-size': `${p.size}px`,
              '--particle-hue': p.hue,
            }}
          />
        ))}

        {/* Pulse rings */}
        <div className={`voice-ring ring-1 ${state !== 'idle' ? 'active' : ''}`} />
        <div className={`voice-ring ring-2 ${state !== 'idle' ? 'active' : ''}`} />
        <div className={`voice-ring ring-3 ${state !== 'idle' ? 'active' : ''}`} />

        {/* Main orb */}
        <button
          className={`voice-orb ${state}`}
          onClick={onToggle}
          aria-label="Toggle voice assistant"
          id="voice-orb-button"
        >
          <div className="orb-inner-glow" />
          <span className="orb-icon">{getIcon()}</span>
        </button>
      </div>

      {/* Wave bars */}
      <div className="wave-container">
        {Array.from({ length: 14 }).map((_, i) => (
          <div
            key={i}
            className={`wave-bar ${state === 'listening' || state === 'speaking' ? 'active' : ''}`}
            style={{ '--bar-index': i }}
          />
        ))}
      </div>

      <div className="voice-label">{getLabel()}</div>
      {state === 'idle' && (
        <div className="voice-hint">Say <strong>"Hey Nova"</strong> or click the orb</div>
      )}
    </div>
  );
}
