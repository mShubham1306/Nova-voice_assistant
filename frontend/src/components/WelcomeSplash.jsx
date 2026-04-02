import React, { useEffect, useState } from 'react';

export default function WelcomeSplash({ onDone }) {
  const [phase, setPhase] = useState('enter'); // enter → show → exit

  useEffect(() => {
    // Phase 1: fade in (0–700ms)
    const t1 = setTimeout(() => setPhase('show'), 700);
    // Phase 2: start exit at 3s
    const t2 = setTimeout(() => setPhase('exit'), 3000);
    // Phase 3: unmount after exit animation
    const t3 = setTimeout(() => onDone(), 3700);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [onDone]);

  return (
    <div className={`welcome-splash ${phase}`}>
      {/* Animated background orbs */}
      <div className="splash-orb splash-orb-1" />
      <div className="splash-orb splash-orb-2" />
      <div className="splash-orb splash-orb-3" />

      {/* Grid overlay */}
      <div className="splash-grid" />

      {/* Main content */}
      <div className="splash-content">
        {/* Logo */}
        <div className="splash-logo-wrap">
          <div className="splash-logo-ring splash-ring-3" />
          <div className="splash-logo-ring splash-ring-2" />
          <div className="splash-logo-ring splash-ring-1" />
          <div className="splash-logo">
            <span className="splash-logo-n">N</span>
          </div>
        </div>

        {/* Welcome text */}
        <div className="splash-text-block">
          <p className="splash-welcome-label">✦ Welcome To</p>
          <h1 className="splash-title">Nova</h1>
          <p className="splash-tagline">Your AI Voice Companion</p>
        </div>

        {/* Loading bar */}
        <div className="splash-loading-track">
          <div className="splash-loading-bar" />
        </div>

        {/* Status */}
        <p className="splash-status">Initializing systems...</p>
      </div>
    </div>
  );
}
